from .prompt.exceptions import PromptError
from .prompt.utils import (filter_dataset,
                          sort_and_filter_by_case_type, 
                          convert_df_to_json_list_v2,
                          restructure_analysis)
class FixedResponseGenerator:

    def __init__(self, query_params, query_results):
        self.query_params = query_params
        self.__parse_parameters(query_params, query_results)


    def __parse_parameters(self, query_params, query_results):

        self.selected_publisher = query_params['selected_publisher']
        self.start_date = query_params['start_date']
        self.end_date = query_params['end_date']
        self.publishers = ', '.join(query_params['compared_publishers'])
        self.bias_categories = ', '.join(query_params['bias_category'])
        self.topics = ', '.join(query_params['topics'])        

        self.data = filter_dataset(query_results, publisher=self.selected_publisher)


    def generate_methodology(self):
        query_params_modified = dict()
        for k, v in self.query_params.items():
            
            if isinstance(v, list):
                if len(v) > 0:
                    # v = '\n\t' +'\n\t'.join(v)
                    v = ', '.join(v)
                    query_params_modified[k] = v

            else:
                v = str(v)
                query_params_modified[k] = v
        
        return query_params_modified


    def generate_case_study(self, case_type):
        # Filter out articles that do not fit the specified case type
        df = sort_and_filter_by_case_type(self.data, case_type)

        # Refine n examples and resample the dataframe
        article_json = convert_df_to_json_list_v2(df, case_type)

        response_list = []
        for n, article in enumerate(article_json):
            headline = article['headline']
            analysis = restructure_analysis(article['analysis'], case_type)
            response = f'[{headline}] {analysis}'
            response_list.append(response)

        return response_list

    def generate_analysis(self, analysis_type, data):
        if analysis_type == 'bias_rating':
            biased_article_count = data[data['bias_rating'] > 0]['count'].sum()
            response = f'{str(biased_article_count)} articles from the {self.query_params["selected_publisher"]} are "Biased" or "Very Biased"'

        elif analysis_type == 'bias_category':
            bias_cat = data.sort_values(by='count', ascending=False).iloc[0]
            response = f'{bias_cat["count"]} articles from the {self.query_params["selected_publisher"]} show {bias_cat["bias_category"].title()}'

        elif analysis_type == 'bias_rating_vs_topics':
            bias_count = data.sum(axis=0)
            if bias_count[1] > bias_count[2]:
                top_topic = data.sort_values(by=1, ascending=False).head(1).index[0]
                response = f'{top_topic} has the highest number of Biased articles'
            elif bias_count[1] < bias_count[2]:
                top_topic = data.sort_values(by=2, ascending=False).head(1).index[0]
                response = f'{top_topic} has the highest number of Very Biased articles'  

        elif analysis_type == 'bias_category_vs_topics':
            data = data.sort_values(by='VBB_unique_count', ascending=False).drop(columns='VBB_unique_count').head(1)
            data = data.T.sort_values(by=data.index[0], ascending=False).head(1)
            bias = data.index[0].title()
            topic = data.columns[0].title()
            response = f'{bias} is the most common bias in articles about {topic}'

        elif analysis_type == 'bias_rating_comparison':
            data = data[data['bias_rating'] > 0].groupby(['publisher'])['count'].sum()
            publisher_count =  str(data[self.query_params['selected_publisher']])
            others_count =  str(data['Others'])
            response = f"{self.query_params['selected_publisher']} published {publisher_count} biased articles compared to {others_count} from other publishers"

        elif analysis_type == 'bias_category_comparison':
            data = data.groupby(['publisher', 'bias_category'])['count'].sum().unstack().fillna(0).T
            data['Total'] = data.sum(axis=1)
            data = data.sort_values(by='Total', ascending=False).drop(columns='Total').T
            data = data.iloc[:, 0]
            response = f"{data.index[0]} accounts for {str(data[0])} counts of {data.name.title()} compared to {str(data[1])} articles from {data.index[1]} in the same time period"

        else:
            raise PromptError('Invalid analysis type. Must be either "topic", "bias_rating", "bias_category" or "tendency"')
        
        return response
