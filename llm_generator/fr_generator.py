from .prompt.exceptions import PromptError

class FixedResponseGenerator:

    def __init__(self, query_params, query_data):
        self.query_params = query_params


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


    def generate_analysis(self, analysis_type, data):
        if analysis_type == 'bias_rating':
            biased_article_count = data[data['bias_rating'] > 0]['count'].sum()
            response = f'{str(biased_article_count)} articles from the {self.query_params["selected_publisher"]} are "Biased" or "Very Biased"'

        elif analysis_type == 'bias_category':
            highly_commited_bias_cat = data.sort_values(by='count', ascending=False)['bias_category'].values[0].title()
            response = f'{highly_commited_bias_cat} is the publisher\'s most commited bias catergory'

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
            response = f'{bias} is the most common bias committed in articles about {topic}'

        elif analysis_type == 'bias_rating_comparison':
            data = data[data['bias_rating'] > 0].groupby(['publisher'])['count'].sum()
            publisher_count =  str(data[self.query_params['selected_publisher']])
            others_count =  str(data['Others'])
            response = f"{self.query_params['selected_publisher']} published {publisher_count} biased articles compared to {others_count} from other publishers"

        elif analysis_type == 'bias_category_comparison':
            data = data.groupby(['publisher', 'bias_category'])['count'].sum().unstack().fillna(0)
            data['Total'] = data.sum(axis=1)
            data = data.sort_values(by='Total', ascending=False).drop(columns='Total')
            publisher_bias_cat = data.loc[self.query_params['selected_publisher']].sort_values(ascending=False).head(1).index[0]
            response = f"{self.query_params['selected_publisher']} has the highest tendency to commit {publisher_bias_cat.title()}"

        else:
            raise PromptError('Invalid analysis type. Must be either "topic", "bias_rating", "bias_category" or "tendency"')
        
        return response
