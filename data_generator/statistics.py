import pandas as pd
import scipy.stats as stats

class StatsCalculator:

    def __init__(self, query_parameters, query_data):
        self.query_data = query_data
        self.query_params = query_parameters

    def calc_1D_stats(self, param):
        """Calculate count of all topics in query"""

        df_stat = self.__show_counts_c1(self.query_data,
                                        self.query_params['selected_publisher'],
                                        param)
        return df_stat

    # def calc_bias_category(self):
    #     """Calculate count of all bias categories in query"""

    #     df_stat = self.__show_counts_c1(self.query_data,
    #                                     self.query_params['selected_publisher'],
    #                                     'bias_category')
    #     return df_stat

    # def calc_bias_rating(self):
    #     """Calculate count of all bias ratings in query"""

    #     df_stat = self.__show_counts_c1(self.query_data,
    #                                     self.query_params['selected_publisher'],
    #                                     'bias_rating')
    #     return df_stat

    def calc_2D_stats(self, param1, param2='topic'):
        """Calculate count of bias category by topic"""

        df_stat = self.__show_counts_c1c2(self.query_data,
                                          self.query_params['selected_publisher'],
                                          param1,
                                          param2)
        return df_stat

    # def calc_bias_rating_vs_topics(self):
    #     """Calculate count of bias rating by topic"""

    #     df_stat = self.__show_counts_c1c2(self.query_data,
    #                                       self.query_params['selected_publisher'],
    #                                       'bias_rating',
    #                                       'topic')
    #     return df_stat

    def calc_tendency(self, param):
        """Calulate bias category tendency"""

        df_stat = self.__show_odds(self.query_data,
                                   self.query_params['selected_publisher'],
                                   self.query_params['compared_publishers'],
                                   param)
        return df_stat
    
    # def calc_bias_rating_tendency(self):
    #     """Calulate bias rating tendency"""

    #     df_stat = self.__show_odds(self.query_data,
    #                                self.query_params['selected_publisher'],
    #                                self.query_params['compared_publishers'],
    #                                'bias_rating')
    #     return df_stat
    
    def __show_counts_c1(self, df_corpus, publisher, c1):
        """Shows counts for one dimension

        Accepted values for dimension:
        'location', 'bias_rating', 'bias_category', 'topic'
        """
        # Filter publisher
        df_publisher = df_corpus[df_corpus['publisher']==publisher]
        # List possible C1 options that can use group by
        simple_c1 = ['location', 'bias_rating']

        if c1 in simple_c1:
            # Group by c1
            df_count = df_publisher.groupby(c1).size().reset_index(name='count')
            return df_count

        elif c1 == 'bias_category':
            # Prepare expected bias categories
            expected_categories = {
                'generalisation',
                'prominence',
                'negative_behaviour',
                'misrepresentation',
                'headline_or_imagery'
            }
            # Find bias categories that are present in dataframe
            actual_categories = list(set(df_publisher.columns).intersection(expected_categories))
            df_count = df_publisher[actual_categories].sum().rename_axis(c1).reset_index(name='count')
            return df_count

        elif c1 == 'topic':
            # Prepare exploded topics
            s_topics = df_publisher[c1].apply(lambda x: x.split(" | "))
            df_count = s_topics.explode().reset_index().groupby(c1).size().reset_index(name='count')
            df_count = df_count.replace('', 'Unknown')
            return df_count

        else:
            raise ValueError(f"Unknown category: {c1}")
        
    def __show_counts_c1c2(self, df_corpus, publisher, c1, c2):
        """Shows counts for two dimensions

        Accepted values for dimensions:
        'location', 'bias_rating', 'bias_category', 'topic'
        """
        ## Filter articles by publisher
        df_publisher = df_corpus[df_corpus['publisher']==publisher]
        simple_c1_c2 = ['location', 'bias_rating']
        advanced_c1_c2 = ['topic', 'bias_category']
        if c1 in simple_c1_c2 + advanced_c1_c2 or c2 in simple_c1_c2 + advanced_c1_c2:
            if c1 not in simple_c1_c2 or c2 not in simple_c1_c2:
                if c1 == 'topic' or c2 == 'topic':
                    # Split topic list
                    df_publisher['topic'] = df_publisher['topic'].apply(lambda x: x.split(" | "))
                    # Explode into singular topics
                    df_publisher = df_publisher.explode('topic')

                if c1 == 'bias_category' or c2 == 'bias_category':
                    # Prepare expected bias categories
                    expected_categories = {
                        'generalisation',
                        'prominence',
                        'negative_behaviour',
                        'misrepresentation',
                        'headline_or_imagery'
                    }
                    # Find bias categories that are present in dataframe
                    actual_categories = list(set(df_publisher.columns).intersection(expected_categories))
                    # Detect other dimension other than bias categories
                    c1_c2 = [c1, c2]
                    c1_c2.remove("bias_category")
                    # Melt bias categories into one column
                    df_publisher = df_publisher.melt(
                        id_vars=c1_c2.pop(),
                        value_vars=actual_categories,
                        var_name="bias_category",
                        value_name="count"
                    )
        else:
            raise ValueError(f"Either one or both of the categories are unknown: {c1}, {c2}")

        if c1 == 'bias_category' or c2 == 'bias_category':
            df_count = df_publisher.groupby([c1, c2]).sum().reset_index()
        else:
            df_count = df_publisher.groupby([c1, c2]).size().reset_index(name='count')
        df_count = df_count.replace('', 'Unknown')
        df_count = df_count.pivot(index=c1, columns=c2, values='count')
        df_count = df_count.fillna(0)
        return df_count

    def __show_odds(self, df_corpus, selected_publisher, compared_publishers, c2):
        """Shows odds ratio for bias rating and category

        Accepted values for dimensions:
        'bias_rating', 'bias_category'
        """
        # Filter articles by stated publishers
        df_all = df_corpus[df_corpus['publisher'].isin([selected_publisher]+compared_publishers)]
        df_all['publisher'] = df_all['publisher'].replace(compared_publishers, 'Others')

        if c2 == "bias_rating":
            # Filter out negative bias rating
            df_all = df_all[df_all['bias_rating']!=-1]
            value_list = df_all['bias_rating'].unique().tolist()
            df_all = pd.get_dummies(df_all[["publisher","bias_rating"]], columns=["bias_rating"])
            df_all['bias_rating_1+2'] = df_all['bias_rating_1'] + df_all['bias_rating_2']
            value_list.append("1+2")

        elif c2 == "bias_category":
            expected_categories = {
                    'generalisation',
                    'prominence',
                    'negative_behaviour',
                    'misrepresentation',
                    'headline_or_imagery'
                }
            # Find bias categories that are present in dataframe
            actual_categories = list(set(df_all.columns).intersection(expected_categories))
            df_all = df_all[['publisher']+actual_categories]
            value_list = actual_categories

        else:
            raise ValueError(f"Unknown category: {c2}")

        dict_odds = {}
        for value in value_list:
            column_name = f'{c2}_{value}' if c2 == 'bias_rating' else f'{value}'
            ct = df_all.groupby(['publisher', column_name]).size().reset_index(name='count')
            ct = ct.pivot(index='publisher', columns=column_name, values='count')
            ct = ct.reindex(index=['Others', selected_publisher], columns=[False, True])
            ct = ct.fillna(0)
            OR, pvalue = stats.fisher_exact(ct)
            dict_odds[value] = {
                'OR': OR,
                'pvalue': pvalue,
                'count': ct.iloc[1,1]
            }
        df_odds = pd.DataFrame(dict_odds).T.reset_index(names=c2)
        return df_odds