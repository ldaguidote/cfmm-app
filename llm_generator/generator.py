from .api.handler import OpenAITextGenerator
from .prompt.prompter import Prompt


class Generator:
    def __init__(self, query_params, query_data):
        self.prompt = Prompt(query_params, query_data)
        self.api_handler = OpenAITextGenerator()

    
    def generate_methodology(self):
        prompt = self.prompt.build_methodology()
        response = self.api_handler.generate_text(prompt)
        return response

    def generate_case_study(self, case_type, n_examples):
        
        try:
            prompt = self.prompt.build_case_studies(case_type, n_examples)
            response = self.api_handler.generate_text(prompt)
            return response
        except:
            pass