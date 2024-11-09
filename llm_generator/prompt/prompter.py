import json
import pandas as pd
from .helper import (filter_dataset,
                     filter_by_case_type, resample_data, 
                     convert_df_to_json_list)

class Prompt:

    def __init__(self, query_params, query_results):
        self.__parse_parameters(query_params, query_results)


    def __parse_parameters(self, query_params, query_results):

        self.selected_publisher = query_params['selected_publisher']
        self.start_date = query_params['start_date']
        self.end_date = query_params['end_date']
        self.publishers = ', '.join(query_params['compared_publishers'])
        self.bias_categories = ', '.join(query_params['bias_category'])
        self.topics = ', '.join(query_params['topics'])        

        self.data = filter_dataset(query_results, publisher=self.selected_publisher)


    def build_methodology(self):

        prompt = f"""[METHODOLOGY]
        1. Paraphrase this paragraph for the methodology of the report to make it more journalistic:

        This report analyzes publications of {self.selected_publisher} from {self.start_date} to {self.end_date}.
        Here, we compared it with the following publishers: {self.publishers}.
        where we considered the following bias types: {self.bias_categories} across the following topics: {self.topics}.
        """

        return prompt
    

    def build_case_studies(self, case_type, n_examples):

        # Filter out articles that do not fit the specified case type
        df = filter_by_case_type(self.data, case_type)

        # Refine n examples and resample the dataframe
        df = resample_data(df, n_examples)
        article_json = r'\n'.join(convert_df_to_json_list(df))

        # Refine prompt header statement
        if case_type in ['Very Biased', 'Biased']:
            header = f"[CASES OF {case_type} ARTICLES FROM {self.selected_publisher}]"
        elif case_type in ['Misrepresentation', 'Negative Behaviour', 'Due Prominence', 'Generalisation',
                           'Imagery and Headlines']:
            header = f"[EXAMPLES FROM {self.selected_publisher} EXHIBITING {case_type}]"

        prompt = f"""[CASES OF BIASED ARTICLES]
        1. The following news articles are examples of biased publications. For each news article, answer the following questions:
        - What is the news article about? What are the key elements of the case?
        - Why is the article showing the bias rating or category? Show evidences that substantiate this claim. 
        2. Be as specific as you can in decribing the key elements and evidences
        3. Each question must be answered using 1-2 bullet points, with each bullet containing only 25-45 words. 
        In total, the final answer must only have three bullet points.
        4. Separate your answer for each article and use this format:
        [TITLE OF ARTICLE 1]
        - Bullet point 1
        - Bullet point 2
        - Bullet point 3

        {header}
        {article_json}
        """
        
        return prompt
    