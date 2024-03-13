# -*- coding: utf-8 -*-
"""
Spyder Editor

The provided Python script processes a Word document (`.docx`) using the `python-docx` library and extracts both text and images. The extracted information is organized into a pandas DataFrame (`df_main`). The primary features of the code are as follows:

1.	Document Processing:

Pipeline extracts images, identifies headers, and organizes content.
Relationships between rId and filenames recorded in 'rels' dictionary.

2.	Image Extraction 
Utilizes docx2txt library to extract and save images in 'img_folder/'.

3.	Relationship Establishment 
Uses docx library to open DOCX document.
Captures rId-filename relationships, stores in 'rels' dictionary.

4.	Paragraph and Header Processing 
Analyzes paragraphs, discerns headers, and organizes information.

5.	Header Processing 
Identifies headers based on styles starting with 'Heading'.
Transforms headers into consistent format, stores in 'headers' list.

6.	Guide Text Association
Associates guide text with hierarchical headers in 'headers_df' list.

7.	Image Relationships
Identifies and maps image relationships in 'rels' dictionary.

8.	Information Storage
Captures data in Pandas DataFrame.
Stored in CSV, XML, and ElephantSQL for various applications.

9.	CSV
DataFrame stored in CSV for future processing and UI design.

10.	XML
DataFrame preserved in XML for hierarchical organization, beneficial for LLM development.


This script serves as a tool for extracting structured information from Word documents, making it useful for tasks such as document analysis and data extraction.

df = pd.DataFrame()
This is a temporary script file.

# Iterate through inline shapes (images) in the document
for shape in doc.inline_shapes:
    if shape.type == 3:  # Check if the shape is an image
        image_bytes = shape.image.blob
        # Save the image bytes or perform other desired actions
        images.append(image_bytes)

return headers, content, images, df_main

"""
import pandas as pd
from docx import Document
import os
import docx
import docx2txt

class doc2content_integrated:
    def __init__(self,source_pdf_file_path,out_folder,filename):
        self.doc_file_path = source_pdf_file_path
        print('doc2content_integrated_test')
        self.out_folder=out_folder
        self.filename=filename+'_knowledge_graph_data.csv'
        self.output_filename = f"{self.out_folder}/{self.filename}"
        #self.pdf_file_path = "/Users/sauravsahu/Downloads/Automated_2013-nissan-leaf-27_194.pdf"  # Provide the path to your PDF file
        print(self.doc_file_path)
        #data = self.extract_text_and_images(self.doc_file_path)
        #print(data.shape)
        #self.save_output(data,self.out_folder,self.filename+'_knowledge_graph_data.csv')

        headers, content, df = self.extract_text_and_images(self.doc_file_path)

        #df.head()
        df = df.fillna('')
        df = df.drop_duplicates().reset_index(drop=True)
        df.to_csv(self.output_filename, index=False)
        print(f"DataFrame saved to {self.filename}")

    def extract_text_and_images(self,docx_path):
        # Open the Word document
        doc = Document(docx_path)
        
        # Extract the images to img_folder/
        docx2txt.process(docx_path, 'static/img_folder/')
        
        
        df = pd.DataFrame()
        df_main = pd.DataFrame()
        #df = pd.DataFrame(columns=['heading_1', 'heading_2','heading_3','heading_4','heading_5','heading_6','heading_7','heading_8','heading_9','warning','caution','danger','special_instruction','guide_text','image_name'])
        dict_example = {'heading_1': 1, 'guide_text': 2}
        #print(df)
        # Initialize lists to store headers, content, and images
        headers = []
        content = []
        #images = []
        old_number=1
        headers_df = []
        
        
        rels = {}
        for r in doc.part.rels.values():
            if isinstance(r._target, docx.parts.image.ImagePart):
                rels[r.rId] = os.path.basename(r._target.partname)
        
        
        
        # Iterate through paragraphs in the document
        for paragraph in doc.paragraphs:
            dict_example = {'heading_1': 1, 'guide_text': 2}
            rels_id =''
            rels_image = ''
            # Check if the paragraph is a header (adjust as needed)
            if 'Graphic' in paragraph._p.xml:
                # Get the rId of the image
                rId =''
                rels_image = ''
                for rId in rels:
                    if rId in paragraph._p.xml:
                        #rId = rId
                        rId = rId
                        rels_id=rId
                        rels_image=rels.get(rId)
                        # Your image will be in os.path.join(img_path, rels[rId])
            if paragraph.style.name.startswith('Heading'):
                para_style_name = str(paragraph.style.name).replace(" ", "_")
                
                para_style_number= int(para_style_name.replace("Heading_", ""))
                para_style_name=para_style_name.lower()
                #para_style_name = para_style_name.replace(" ", "_")
                print(para_style_name)
                old_number_mod = old_number
                
                #if old_number==9 and para_style_number != 9:
                if old_number - para_style_number > 1:
                    old_number_mod = para_style_number+1
                    #print("old_number_mod logic :",old_number, old_number_mod, para_style_number+1)
                    
                if para_style_name not in df.columns:
                    df[para_style_name]=''
                    
                if para_style_number == old_number_mod:
                #print(len(headers_df))
                    if len(headers_df) != 0:
                        headers_df.pop()
                    headers_df.append(paragraph.text.strip().replace(":", "").lower())
                    #print(headers_df)
                    
                    if para_style_number > old_number_mod:
                        headers_df.append(paragraph.text.strip().replace(":", "").lower())
                    #print(headers_df)
                    
                    if para_style_number < old_number:
                    #print(old_number_mod)
                        difference = old_number_mod-para_style_number
                    #print(difference)
                        for i in range(1,difference+1):
                            headers_df.pop()
                        headers_df.append(paragraph.text.strip().replace(":", "").lower())
                        #print(headers_df)
                
                #print('Heading Name',para_style_name)
                headers.append(paragraph.text.strip())
                
        
                
            else:
                content.append(paragraph.text.strip())
                
                for i in range(0,len(headers_df)):
                    if headers_df[i]=='danger' or headers_df[i]=='caution' or headers_df[i]=='warning':
                        dict_example[headers_df[i]]=headers_df[i]
                    elif i == 9 :
                        print('elif i == 9 :',i)
                        dict_example['special_instruction']=headers_df[i]
                    else:
                        dict_example['heading_'+str(i+1)]=headers_df[i]

                        #print('heading',dict_example)
                #df = pd.DataFrame(data=headers_df)
                #df = df.T
                dict_example['guide_text']=paragraph.text.strip()
                dict_example['rId']=rels_id
                dict_example['image_name']=rels_image
            
                #print(dict_example)
                df = pd.DataFrame(dict_example,index=['i',])
                #df.append(df.append(pd.DataFrame(headers_df).T))
                #print(df.head)
                
                #df = writeintodf(df,headers_df,paragraph.text.strip())

            df_main=pd.concat([df_main, df], ignore_index=True)
            
            old_number=para_style_number
        return headers, content, df_main