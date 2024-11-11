import json
import pandas as pd
from .utils import (filter_dataset,
                    filter_by_case_type, 
                    resample_data, 
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
        1. Paraphrase the paragraph below for the methodology of the report to make it more journalistic.
        2. Ensure that you will mention all the publishers, topics and bias categories specified in the body of the text.

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
        2. Be as specific as you can in decribing the key elements and evidences.
        3. Each question must be answered using 1-2 bullet points, with each bullet containing only 25-45 words. 
        In total, the final answer must only have three bullet points.
        4. Separate your answer for each article and use this format:
        [TITLE OF ARTICLE]
        - Bullet point 1
        - Bullet point 2
        - Bullet point 3

        {header}
        {article_json}
        """
        
        return prompt
    

    def analyze_topics(self, data):

        prompt = f"""[ANALYZE TOPICS]
        1. You will be writing part of the Publisher Performance and this section deals with the topics covered by the publisher. 
        Given the topic dataset, where you are given the count of articles per topic for the publisher, give me three key insights.
        2. Do not just describe the dataset, use the context of the news articles that you have seen to enrich your analysis of this dataset. 
        3. This is turned into a bar chart. Come up with a title for the chart which encapsulates the key message of the dataset. 
        Do not provide a generic chart title. This should be insightful and it should describe the data accurately. 
        It should be able to answer the question: What can you say about the publisher given this dataset?
        4. Your insights should be in bullet form, with a maximum of 3 bullets. Each bullet must only be 10-20 words. Answer in this format:
        [CHART TITLE/ KEY INSIGHT OF THE CHART]
        - Insight #1
        - Insight #2
        - Insight #3        

        {data}
        """

        return prompt
    

    def analyze_bias_rating(self, data):

        prompt = f"""[ANALYZE BIAS RATING]
        1. You will be writing part of the Publisher Performance where you will gauge the bias profile of a publisher. 
        You will do this by uncovering insights on the bias rating datasets, where you are either given the count of articles per bias rating 
        for the publisher or the count of articles for each bias rating by topic. Give me insights by exploring the summary statistics 
        provided. 
        2. Do not just describe the dataset, use the context of the news articles that you have seen to enrich your analysis of this dataset.
        3. This will be plotted. Come up with a title for the chart which encapsulates the key message of the dataset. 
        Do not provide a generic chart title. This should be insightful and it should describe the data accurately. 
        It should be able to answer the question: What can you say about the publisher given this dataset?
        4. Your insights should be in bullet form, with a maximum of 3 bullets. Each bullet must only be 10-20 words. Answer in this format:
        [CHART TITLE/ KEY INSIGHT OF THE CHART]
        - Insight #1
        - Insight #2
        - Insight #3        

        {data}
        """

        return prompt
    

    def analyze_bias_category(self, data):

        prompt = f"""[KEY INSIGHT OF THE CHART]
        1. You will be writing part of the Publisher Performance where you will gauge the bias profile of a publisher. 
        You will do this by uncovering insights on the bias category datasets, where you are either given the count of articles per bias category 
        for the publisher or the count of articles for each bias category by topic. Give me insights by exploring the summary statistics 
        provided. 
        2. Do not just describe the dataset, use the context of the news articles that you have seen to enrich your analysis of this dataset.
        3. This will be plotted. Come up with a title for the chart which encapsulates the key message of the dataset. 
        Do not provide a generic chart title. This should be insightful and it should describe the data accurately. 
        It should be able to answer the question: What can you say about the publisher given this dataset?
        4. Your insights should be in bullet form, with a maximum of 3 bullets. Each bullet must only be 10-20 words. Answer in this format:
        [CHART TITLE/ KEY INSIGHT OF THE CHART]
        - Insight #1
        - Insight #2
        - Insight #3        

        {data}
        """

        return prompt
    

    def analyze_bias_tendency(self, data):

        prompt = f"""[ANALYZE TENDENCY TO COMMIT BIAS]
        1. You will be writing part of the Publisher Comparison where you will gauge the bias profile of a publisher vis-a-vis other publishers. 
        You will do this by uncovering insights on the tendency to commit bias datasets. The tendency to commit bias datasets includes the 
        odds ratio which signifies whether the publisher is biased compared to its peers (OR > 1) or not (OR < 1 means peers are more biased). 
        The p-value is also given which will indicate the statistical significance. For this analysis, our significance level is 0.1.
        2. You will either be given the tendency for each bias category dataset or the tendency for each bias rating. In the tendency for bias 
        rating dataset, the combined Biased and Very Biased scores are denoted as `1+2`
        3. Give me your key insights on the dataset. Do not just describe the dataset, use the context of the news articles that you have seen 
        to enrich your analysis of this dataset.
        4. This will be plotted. Come up with a title for the chart which encapsulates the key message of the dataset. 
        Do not provide a generic chart title. This should be insightful and it should describe the data accurately. 
        It should be able to answer the question: What can you say about the publisher given this dataset?
        5. Your insights should be in bullet form, with a maximum of 3 bullets. Each bullet must only be 10-20 words. Answer in this format:
        [CHART TITLE/ KEY INSIGHT OF THE CHART]
        - Insight #1
        - Insight #2
        - Insight #3     

        {data}
        """

        return prompt
    

    def build_key_message(self):

        prompt = f"""[KEY MESSAGE]
        1. You will be writing part of the Key Message where you will succinctly summarize {self.selected_publisher}'s bias profile based on your conclusions.
        3. Your insights should be in bullet form, with a maximum of 3 bullets. Each bullet must only be 10-25 words.
        """

        return prompt
    

    def build_conclusions(self):

        prompt = f"""[CONCLUSIONS]
        1. You will be writing the Conclusion where you will provide an analysis on the totality of the {self.selected_publisher}'s bias profile. 
        2. Consolidate your past insights about the publisher. It must answer these questions:
        - What is the bias profile of the publisher compared to the overall media landscape?
        - What are the notable instances of bias and what is its significance and relationship to our final analysis?
        - Why is this analysis important? Why should we care about the result of your analysis?
        3. Your insights should be in bullet form, with a maximum of 4 bullets. Each bullet must only be 25-45 words.
        """

        return prompt