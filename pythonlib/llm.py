import torch
from transformers import GPT2Tokenizer, GPT2LMHeadModel, GPT2Config
import re

class llm:
    def __init__(self, question, model_path,keywords_file):
        self.question = question
        self.model_path = model_path
        self.keywords_file = keywords_file

        
    def read_keywords_from_file(self,file_path):
        with open(file_path, 'r') as f:
            keywords = [line.strip() for line in f.readlines()]
        return keywords

    # Function to check if a question is relevant based on keywords
    def is_question_relevant(self,question, relevant_keywords):
        pattern = r'[^\w\s]'  # Matches any non-word and non-space characters
        # Replace the special characters with an empty string
        cleaned_string = re.sub(pattern, '', question)
        print('cleaned_string',cleaned_string)
        question_tokens = cleaned_string.lower().split()
        for keyword in relevant_keywords:
            if keyword.lower() in question_tokens:
                return True
        return False
    
    def llmmodel(self):
        # Load fine-tuned model and tokenizer configuration
        model_path = self.model_path#'fine_tuned_model.pth'  # Update with the path to your fine-tuned model .pth file
        keywords_file = self.keywords_file#'EVB_Nissan_2013_relevant_words.txt'  # Path to the relevant keywords text file
        
        # Load tokenizer configuration
        tokenizer = GPT2Tokenizer.from_pretrained('gpt2')

        # Load model configuration
        config = GPT2Config.from_pretrained('gpt2')
        model = GPT2LMHeadModel(config)

        # Load the state_dict from .pth file
        state_dict = torch.load(model_path)
        model.load_state_dict(state_dict)

        # Load relevant keywords from text file
        relevant_keywords = self.read_keywords_from_file(keywords_file)

        # Example: Generate text
        input_text = self.question
        
        # Example: Check if the question is relevant
        if self.is_question_relevant(input_text, relevant_keywords):
            input_ids = tokenizer.encode(input_text, return_tensors='pt')
            generated = model.generate(input_ids, max_length=100, num_return_sequences=1)
            decoded_text = tokenizer.decode(generated[0], skip_special_tokens=True)
            print(decoded_text)
        else:
            decoded_text = "Sorry, I am not trained to answer this question.Question is not relevant."

        response = decoded_text
        return response
