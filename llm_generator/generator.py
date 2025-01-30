from .api.handler import OpenAITextGenerator
from .prompt.prompter import Prompt
from .prompt.exceptions import PromptError
from .prompt.utils import sort_and_filter_by_case_type, convert_df_to_json_list_v2

class Generator:
    def __init__(self, query_params, query_data):
        self.prompt = Prompt(query_params, query_data)
        self.api_handler = OpenAITextGenerator()

    
    def generate_methodology(self):
        prompt = self.prompt.build_methodology()
        response = self.api_handler.generate_text(prompt)
        return response

    def generate_case_study(self, case_type):

        try:
            prompt_list = self.prompt.build_case_studies(case_type)
            response_list = []
            for prompt in prompt_list:
                response = self.api_handler.generate_text(prompt)
                response_list.append(response)
            return response_list
        except Exception as e:
            raise ValueError(e)

    def generate_analysis(self, analysis_type, data):
        if analysis_type == 'topic':
            prompt = self.prompt.analyze_topics(data)
        elif analysis_type == 'bias_rating':
            prompt = self.prompt.analyze_bias_rating(data)
        elif analysis_type == 'bias_category':
            prompt = self.prompt.analyze_bias_category(data)
        elif analysis_type == 'tendency':
            prompt = self.prompt.analyze_bias_tendency(data)
        else:
            raise PromptError('Invalid analysis type. Must be either "topic", "bias_rating", "bias_category" or "tendency"')

        response = self.api_handler.generate_text(prompt)
        return response
    
    def generate_conclusions(self):
        prompt = self.prompt.build_conclusions()
        response = self.api_handler.generate_text(prompt)
        return response
    
    def generate_key_message(self):
        prompt = self.prompt.build_key_message()
        response = self.api_handler.generate_text(prompt)
        return response