import re
import torch
import faiss
import numpy as np
import pandas as pd
from pathlib import Path
from PyPDF2 import PdfReader
from nltk import word_tokenize
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel, pipeline
from sklearn.metrics.pairwise import cosine_similarity
import nltk
import PyPDF2
import spacy
import os
import ast
import shutil
# Ensure that nltk data is downloaded
nltk.download('punkt')

class NerExtractor:
    def __init__(self,path, model_name='bert-base-uncased',model_path='./static/models/NER'):
        self.nlp = spacy.load(model_path)
        self.path=path
        csv_file = next((f for f in os.listdir(self.path) if f.endswith('_kdb_data.csv')), None)

        # Load the CSV file into a DataFrame
        if csv_file:
            file_path = os.path.join(self.path, csv_file)
            self.image_df = pd.read_csv(file_path)
            print('self.image_df.shape',self.image_df.shape)
        else:
            print("No file ending with '_kdb_data.csv' found.")

        # Initialize the model and tokenizer from Hugging Face
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)

        # Embed all 'Text' column values
        self.image_df['Embeddings'] = self.image_df['Text'].apply(self.get_embedding)
    def word_match_check(self, component, replaced_component):
        """Check if at least one word from the component matches with the replaced_component."""
        component_words = set(component.lower().split())
        replaced_words = set(replaced_component.lower().split())
        return not component_words.isdisjoint(replaced_words)
    
    def get_embedding(self, text):
        """Get embeddings for a given text using Hugging Face model and tokenizer."""
        tokens = self.tokenizer(text, return_tensors='pt', truncation=True, padding=True)
        with torch.no_grad():
            output = self.model(**tokens)
        # Mean pooling to get a single vector representation
        embeddings = output.last_hidden_state.mean(dim=1)
        return embeddings.squeeze().numpy()

    def compute_similarity(self, component_embedding):
        """Compute similarity between the component embedding and all text embeddings."""
        # Calculate cosine similarity between component embedding and all text embeddings
        text_embeddings = list(self.image_df['Embeddings'])
        cosine_sim = cosine_similarity([component_embedding], text_embeddings).flatten()
        #print('cosine_sim',cosine_sim)
        # Find the index of the maximum similarity
        max_idx = cosine_sim.argmax()
        max_similarity = cosine_sim[max_idx]
        # Return the most similar text from 'Text' column
        #print(self.image_df['cc_segment_image'].iloc[max_idx])
        return self.image_df['Text'].iloc[max_idx], self.image_df['cc_segment_image'].iloc[max_idx], max_similarity

    def extract_entities(self, text):
        doc = self.nlp(text)
        components = [ent.text for ent in doc.ents if ent.label_ == 'COMPONENT']
        tools = [ent.text for ent in doc.ents if ent.label_ == 'TOOL']
        joints = [ent.text for ent in doc.ents if ent.label_ == 'JOINT']

        cc_segment_images = []
        replaced_components = []
        for component in components:
            # Get embedding for the component
            component_embedding = self.get_embedding(component)

            # Find the most similar text and replace the component
            replaced_component, cc_segment_image, max_similarity = self.compute_similarity(component_embedding)
            #cc_segment_image = None

            # Check for at least one word match
            if self.word_match_check(component, replaced_component):
                replaced_components.append(replaced_component)
                if cc_segment_images != None:
                    cc_segment_images.append(cc_segment_image)
                print(f"Original component: {component}, Replaced with: {replaced_component}, "
                      f"cc_segment_image: {cc_segment_image}, Similarity score: {max_similarity}")
            else:
                replaced_components.append(component)  # Keep original component if no match is found
                cc_segment_images.append(None)  # No cc_segment_image for unmatched components
                print(f"Original component: {component}, No matching text found. Similarity score: {max_similarity}")
            print(replaced_components, cc_segment_images, tools, joints)
        return replaced_components, cc_segment_images, tools, joints
        
class PDFProcessor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.text = self._extract_text_from_pdf()

    def _extract_text_from_pdf(self):
        with open(self.pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ''.join([page.extract_text() for page in reader.pages])
        return text

    def split_into_sentences(self):
        sentences = nltk.sent_tokenize(self._clean_text(self.text))
        return sentences

    def _clean_text(self, text):
        cleaned_text = ""
        for line in text.splitlines():
            cleaned_line = self._clean_string(line)
            if cleaned_line:
                cleaned_text += f"{cleaned_line} "
        return cleaned_text

    def _clean_string(self, s):
        s = re.sub(r'\bINFOID:\S*\b', '', s)
        single_letter_word = re.sub(r'[.\s]', '', s)
        return "" if len(single_letter_word) < 4 else s

class DataProcessor:
    def __init__(self):
        self.df = pd.DataFrame(columns=['Headings', 'Text', 'result'])
        self.df['result'] = 'Not Checked'
        self.heading = ''
        self.add_numeric = ''
        self.unique_sentences = []
        self.unique_embeddings = []
        self.tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
        self.model = AutoModel.from_pretrained('bert-base-uncased')

    def populate_dataframe(self, sentences):
        for sentence in sentences:
            self._process_sentence(sentence)
        self._apply_heading_labels()
        self._print_heading_pivot()

    def _process_sentence(self, sentence):
        line_check = sentence[:10].split(':')[0]
        special_character_check = bool(re.match(r'^[\W_]+$', sentence[:3]))

        if bool(re.search(r'\d', ''.join(sentence.split()[:1]))):
            self.add_numeric = sentence
        elif line_check.isupper() and not special_character_check and not bool(re.search(r'\d', sentence[:1])):
            heading = ' '.join(re.findall(r'\b[A-Z]+(?=\b|:)', sentence))
            #heading = ''.join([match + ':' if ':' in sentence[sentence.index(match) + len(match)] == ':' else match for match in heading])
            heading = ''.join([match + ':' if (sentence.index(match) + len(match) < len(sentence) and sentence[sentence.index(match) + len(match)] == ':') else match for match in heading])
            sentence = sentence.replace(heading, "")
            if ''.join(sentence.split()) and all(char == '.' for char in ''.join(sentence.split())):
                return
            else:
                array = [heading.replace(":", ""), self.add_numeric + sentence, ""]
                self.df.loc[len(self.df)] = array
            self.add_numeric = ''
        elif not special_character_check and not bool(re.search(r'\d', ''.join(sentence.split()[:1]))):
            sentence = sentence.replace(self.heading, "")
            if ''.join(sentence.split()) and all(char == '.' for char in ''.join(sentence.split())):
                return
            else:
                array = [self.heading.replace(":", ""), self.add_numeric + sentence, ""]
                self.df.loc[len(self.df)] = array
            self.add_numeric = ''

    def _apply_heading_labels(self):
        # Ensure consistent label mapping
        label_mapping = {"CAUTION": "0", "DANGER": "1", "INSTRUCTION": "2", "PRECAUTION": "3", "WARNING": "4"}
        
        # Apply filtering sequentially
        self.df['Headings'] = self.df['Headings'].apply(lambda x: x if x in label_mapping else 'INSTRUCTION')
        self.df['Headings'] = self.df['Headings'].apply(lambda x: x if x in label_mapping else 'CAUTION')
        self.df['Headings'] = self.df['Headings'].apply(lambda x: x if x in label_mapping else 'PRECAUTION')

        # Mapping Headings to numeric values
        self.df['Headings'] = self.df['Headings'].map(label_mapping)
        
        
        # Debugging: Check the DataFrame after processing
        print("DataFrame after applying heading labels:")
        print(self.df[['Headings', 'Text']].head())

    def _print_heading_pivot(self):
        # Create a pivot table showing the count of rows for each heading
        pivot_df = self.df.pivot_table(index='Headings', values='Text', aggfunc='count')
        print("Pivot Table of Headings vs Count of Text Rows:")
        print(pivot_df)

class FAISSIndexManager:
    def __init__(self, model_name,path, stage=None,df=None):
        self.model_name = model_name
        self.df = df
        self.csv_path = path+"/"+f'{self.model_name}_data.csv'
        self.vector_store_path = Path(path+"/"+f'pretrained_ST_{self.model_name}_vector_store.index')
        print('self.vector_store_path',self.vector_store_path)
        self.labels_path = Path(path+"/"+f'{self.model_name}_labels.npy')
        self.index = None
        self.labels = None
        
        if stage=='write':
            self.labels = self.df['Headings'].tolist()
            self._create_faiss_index()
        '''
        if self.df is None and self.csv_path:
            self.df = pd.read_csv(self.csv_path)
        
        
        else:
            raise ValueError("DataFrame or CSV path must be provided.")'''

    def _create_faiss_index(self):
        model = SentenceTransformer(self.model_name)
        embeddings = model.encode(self.df['Text'].tolist(), convert_to_tensor=True)
        embeddings_np = embeddings.cpu().numpy()
        dimension = embeddings_np.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings_np)
        
        # Save FAISS index
        faiss.write_index(self.index, str(self.vector_store_path))
        
        # Save labels
        np.save(self.labels_path, np.array(self.labels))
        print(self.csv_path)
        # Save DataFrame to CSV
        self.df.to_csv(self.csv_path, index=False)

    def load_index(self, path):
        self.index = faiss.read_index(self.vector_store_path)
        if self.index is None:
            raise ValueError("Failed to load FAISS index. The index is None.")
        self.labels = np.load(self.labels_path).tolist()

        # Load DataFrame from CSV
        self.df = pd.read_csv(self.csv_path)
        if self.df.empty:
            raise ValueError("Failed to load DataFrame. The DataFrame is empty.")

    def retrieve_documents(self, query, k=50):
        self.index = faiss.read_index(str(self.vector_store_path))
        if self.index is None:
            raise ValueError("FAISS index is not initialized. Please load or create the index first.")

        model = SentenceTransformer(self.model_name)
        query_embedding = model.encode([query], convert_to_tensor=True).cpu().numpy()
        distances, indices = self.index.search(query_embedding, k + 20)
        print('distances, indices',len(distances[0]), len(indices[0]))
        return indices, distances




class RAGQueryManager:
    def __init__(self, model_name, df, index_manager,qamodelname,question):
        self.qa_pipeline = pipeline("question-answering", model=qamodelname)
        self.model_name = model_name
        self.df = df
        self.index_manager = index_manager
        self.tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
        self.model = AutoModel.from_pretrained('bert-base-uncased')
        self.question=question
        self.reverse_label_mapping = {
            "0": "CAUTION",
            "1": "DANGER",
            "2": "INSTRUCTION",
            "3": "PRECAUTION",
            "4": "WARNING"
        }
        self.unique_sentences = []
        self.unique_embeddings = []

    def preprocess_text(self, text):
        text = text.lower()  # Convert to lowercase
        text = re.sub(r'\s+', ' ', text)  # Remove extra whitespace
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
        return text

    def get_embedding(self, text):
        tokens = self.tokenizer(text, return_tensors='pt', truncation=True, padding=True)
        with torch.no_grad():
            output = self.model(**tokens)
        # Mean pooling to get a single vector representation
        embeddings = output.last_hidden_state.mean(dim=1)
        return embeddings.squeeze().numpy()

    def _is_unique_sentence(self, sentence):
        preprocessed_sentence = self.preprocess_text(sentence)
        new_embedding = self.get_embedding(preprocessed_sentence).reshape(1, -1)
        
        if not self.unique_sentences:  # If unique_sentences is empty
            self.unique_sentences.append(sentence)
            self.unique_embeddings.append(new_embedding)
            return True

        # Calculate cosine similarity with existing embeddings
        similarities = cosine_similarity(new_embedding, np.array(self.unique_embeddings).reshape(-1, new_embedding.shape[1]))
        if np.max(similarities) < 0.9:  # Check if the max similarity is below the threshold
            self.unique_sentences.append(sentence)
            self.unique_embeddings.append(new_embedding)
            return True

        return False
    def get_answer_or_context(self,sentence,question):
        result = self.qa_pipeline(question=self.question, context=sentence)
        answer = result['answer']
        sentence_embedding = self.get_embedding(sentence).reshape(1, -1)
        question_embedding = self.get_embedding(question).reshape(1, -1)
        answer_embedding = self.get_embedding(answer).reshape(1, -1)
        similarities = cosine_similarity(question_embedding, answer_embedding)[0][0]
        #print('print similratity',similarities,":",answer)
        #print(answer)
        #print('len(answer)',len(answer.split()))
        # Check if answer length is less than or equal to 3 characters
        if len(answer.split()) <= 3:
            similarities = cosine_similarity(question_embedding, sentence_embedding)[0][0]
            #print('print similratity',similarities,":",similarities)
            return sentence,similarities  # Return the entire sentence as the answer
        return answer,similarities  # Otherwise return the extracted answer

    def query(self, question, k=80):
        if len(self.df) <=80:
            k = len(self.df) - 20
        indices, cosine_similarities = self.index_manager.retrieve_documents(question, k)
        seen_documents = set()
        unique_results = []

        # Label count requirements for a total of 22 retrievals
        label_counts = {
            "2": 7,  # 10 instructions
            "1": 2,   # 3 danger
            "4": 2,   # 3 warning
            "0": 2,   # 3 caution
            "3": 2    # 3 precaution
        }
        collected_counts = {label: 0 for label in label_counts}
        # Filter out indices with negative values
        valid_indices = [index for index in indices[0] if index >= 0]

        # Ensure valid indices are within the range of the DataFrame
        valid_indices = [index for index in valid_indices if index < len(self.df)]
        #print('valid_indices',valid_indices)
        results_with_scores = list(zip(valid_indices, cosine_similarities[0]))
        results_with_scores.sort(key=lambda x: x[1], reverse=True)
     

        answer_df = self.df.loc[valid_indices].reset_index()
        answer_df['Headings'] = answer_df['Headings'].apply(lambda label: self.reverse_label_mapping.get(str(label), str(label)))
    
        # Remove duplicate sentences
        unique_sentence_indices = {}
        
        for idx, sentence in enumerate(answer_df['Text']):
            if self._is_unique_sentence(sentence):
                unique_sentence_indices[sentence] = idx

        # Create a DataFrame with only the first occurrence of each unique sentence
        unique_indices = list(unique_sentence_indices.values())
        answer_df = answer_df.loc[unique_indices].reset_index(drop=True)
        answer_df[['Answer', 'cosine_sim']] = answer_df.apply(lambda row: pd.Series(self.get_answer_or_context(row['Text'], question)),axis=1)
        answer_df = answer_df[answer_df['cosine_sim'] > 0.6]
        answer_df = answer_df.sort_values(by='cosine_sim', ascending=False).reset_index(drop=True)
       # Get the current counts of each label in the DataFrame
        current_counts = answer_df['Headings'].value_counts()
        if len(answer_df)<=5:
            return None
        #print(current_counts)

        # Calculate shortfalls
        shortfalls = {label: max(0, label_counts.get(label, 0) - current_counts.get(self.reverse_label_mapping[label], 0)) for label in label_counts}
        print('shortfalls',shortfalls)
        # Filter DataFrame based on required counts
        filtered_dfs = []
        #print("test_filter",answer_df[answer_df['Headings'] == "CAUTION"].head(min(shortfalls["0"],label_counts.get("0", 0))))
        filtered_dfs.append(answer_df[answer_df['Headings'] == "CAUTION"].head(label_counts.get("0", 0)))
        filtered_dfs.append(answer_df[answer_df['Headings'] == "DANGER"].head(label_counts.get("1", 0)))
        filtered_dfs.append(answer_df[answer_df['Headings'] == "PRECAUTION"].head(label_counts.get("3", 0)))
        filtered_dfs.append(answer_df[answer_df['Headings'] == "WARNING"].head(label_counts.get("4", 0)))
        # Add instructions if needed (use key '2' for 'INSTRUCTION')
        total_instruction = max(label_counts["2"]+shortfalls["0"]+shortfalls["1"]+shortfalls["3"]+shortfalls["4"],label_counts["2"])

        #filtered_dfs.append(answer_df[answer_df['Headings'] == "INSTRUCTION"].head(total_instruction))
        filtered_dfs.append(answer_df[answer_df['Headings'] == "INSTRUCTION"].head(total_instruction))
        # Concatenate all filtered dataframes
        answer_df = pd.concat(filtered_dfs).reset_index(drop=True)
        #answer_df['cosine_sim']=""
        answer_df[['Answer', 'cosine_sim']] = answer_df.apply(lambda row: pd.Series(self.get_answer_or_context(row['Text'], question)),axis=1)
        #answer_df['Text'].apply(lambda sentence: self.get_answer_or_context(sentence, question))
        
        #answer_df['Answer'] = answer_df['Text'].apply(lambda sentence: self.get_answer_or_context(sentence, question))
        
        print("Current counts:", current_counts)
        print(f"Total results retrieved: {answer_df.shape}")

        return answer_df

def safe_literal_eval(val):
    if isinstance(val, str):
        return ast.literal_eval(val)
    return val  # If it's already a list or any other valid Python object, return as is

def main(stage,faiss_model_names,qa_model_names,main_path,source_filename_pdf,question=None):
#qa_write_query_main('write',faiss_model_names,qa_model_names,
    #app.config['KNOWLEDGE_GRAPH']+"/",os.path.join(app.config['UPLOAD_DIR'], source_filename_pdf))
    #main_path = main_path+'/'
    path =main_path+"/confirmedkdb/"
    #imagepath=os.path.join(os.path.join(main_path, "img_folder"),"segmentimages")          
    result=pd.DataFrame()
    csv_path = path+'/'+f'{faiss_model_names}_data.csv'
    final_answers=""

    print(source_filename_pdf)
    if stage == 'write':
        component_names=list()
        component_image_map=dict()
        unique_tool_list=list()
        unique_joint_list=list()
        pdf_path = source_filename_pdf
        pdf_processor = PDFProcessor(pdf_path)
        sentences = pdf_processor.split_into_sentences()

        data_processor = DataProcessor()
        data_processor.populate_dataframe(sentences)
        NER=NerExtractor(path)
        
        data_processor.df[['COMPONENT','CC_SEGMENT_IMAGES','TOOL', 'JOINT']] = data_processor.df['Text'].apply(lambda x: pd.Series(NER.extract_entities(x)))
        
        faiss_manager = FAISSIndexManager(faiss_model_names,path,stage, data_processor.df)
        
    if stage == 'query':
        if csv_path:
            df = pd.DataFrame(pd.read_csv(csv_path))

        print('df.shape',df.shape)
        faiss_manager = FAISSIndexManager(faiss_model_names,path,stage, df)
        rag_manager = RAGQueryManager(faiss_model_names, df, faiss_manager,qa_model_names,question )
        result = rag_manager.query(question)
        print('result.shape',result.shape)
        #print(result['Answer'])

        component_image_map=dict()
        for index, row in result.iterrows():
            # Safely evaluate string to list (if necessary)
            #print(len(list(row['COMPONENT'])))
            #print(row['CC_SEGMENT_IMAGES'])
            
            if len(row['COMPONENT']) >= 3 and len(row['CC_SEGMENT_IMAGES']) >= 3:
                #print(row['COMPONENT'])
                components = ast.literal_eval(row['COMPONENT']) if isinstance(row['COMPONENT'], str) else row['COMPONENT']
                images = ast.literal_eval(row['CC_SEGMENT_IMAGES']) if isinstance(row['CC_SEGMENT_IMAGES'], str) else row['CC_SEGMENT_IMAGES']
                for image_check in images:
                    #print('image_check')
                    if image_check:
                        if not os.path.isfile(main_path+'img_folder/segmentimages/'+image_check):
                            sourcefile=main_path+'/img_folder/'+image_check
                            destfile=main_path+'/img_folder/segmentimages/'+image_check
                            shutil.copyfile(sourcefile, destfile)
                            print('image file moved')
                    
                # Create dictionary by zipping components and images
                component_image_map.update(dict(zip(components, images)))

                # Output the result for this row
                #print(f"Row {index} - Component to Image Mapping: {component_image_map}")
        component_image_map = {
            k: v for k, v in component_image_map.items() if v is not None
        }
        component_names = list(component_image_map.keys())

        # Convert string representation of lists to actual lists
        #result_df_final['COMPONENT'] = result_df_final['COMPONENT'].apply(ast.literal_eval)
        result['TOOL'] = result['TOOL'].apply(safe_literal_eval)

        # Flatten the lists and get unique components
        unique_tool = set([item for sublist in result['TOOL'] for item in sublist])

        # Add prefix 'Component - ' to each unique component
        unique_tool_list = [tool for tool in unique_tool]
        #print(unique_tool_list_1)

        result['JOINT'] = result['JOINT'].apply(safe_literal_eval)

        # Flatten the lists and get unique components
        unique_joint = set([item for sublist in result['JOINT'] for item in sublist])

        # Add prefix 'Component - ' to each unique component
        unique_joint_list = [joint for joint in unique_joint]
        #print(unique_joint_list)
        if result is None or result.empty:
            final_answers = "The question is out of scope. please try with questions related to the document."
        else:
            final_answers = ' '.join(result['Answer'].tolist()) +'.'
        print(final_answers)
        return final_answers, component_names, component_image_map, unique_tool_list, unique_joint_list

'''
# Example usage
stage = 'query'
faiss_model_names = 'all-MiniLM-L6-v2'
qa_model_names = 'distilbert-base-uncased-distilled-squad'
#csv_path = f'{faiss_model_names}_data.csv'
path = f"test_program/"
result_df_final = main(stage,faiss_model_names,qa_model_names,path)'''