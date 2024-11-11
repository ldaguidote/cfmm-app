import json
import pandas as pd

from .exceptions import PromptError


def filter_dataset(df, **kwargs):
    """
    Filter out data that do not fit the criteria
    
    """
    for k, v in kwargs.items():
        if isinstance(v, tuple):
            if v[0] == '>':
                df = df[df[k] > v[1]]
            elif v[0] == '>=':
                df = df[df[k] >= v[1]]
            elif v[0] == '<=':
                df = df[df[k] <= v[1]]
            elif v[0] == '<':
                df = df[df[k] < v[1]]
        else:
            df = df[df[k] == v]
    return df


def filter_by_case_type(df, case_type):

    if case_type == 'Very Biased':
        df = filter_dataset(df, bias_rating=2)
    elif case_type == 'Biased':
        df = filter_dataset(df, bias_rating=1)
    elif case_type == 'Misrepresentation':
        df = filter_dataset(df, bias_rating=('>=', 1), misrepresentation=1)
    elif case_type == 'Negative Behaviour':
        df = filter_dataset(df, bias_rating=('>=', 1), negative_behaviour=1)
    elif case_type == 'Due Prominence':
        df = filter_dataset(df, bias_rating=('>=', 1), prominence=1)
    elif case_type == 'Generalisation':
        df = filter_dataset(df, bias_rating=('>=', 1), generalisation=1)
    elif case_type == 'Imagery and Headlines':
        df = filter_dataset(df, bias_rating=('>=', 1), headline_or_imagery=1)
    else:
        error_clause = "Case type must be in this list: 'Biased', 'Very Biased', 'Misrepresentation', " \
            "'Negative Behaviour', 'Due Prominence', 'Generalisation', and 'Imagery and Headlines'."
        raise ValueError(error_clause)
    
    return df


def resample_data(df, n_examples):
    article_count = len(df)
    if article_count == 0:
        raise PromptError('No examples are found for this case type.')

    if n_examples > article_count:
        n_examples = article_count
    else:
        df = df.sample(n_examples)

    return df

def convert_df_to_json_list(df):
    json_list = []
    for _, row in df.iterrows():
        row_dict = {}
        row_dict['title'] = row['title']

        content = {}

        bias_category = []
        bias_list = ['generalisation', 'prominence', 'negative_behaviour', 'misrepresentation', 'headline_or_imagery']
        for bias in bias_list:
            if row[bias] == 1:
                bias_category.append(bias)
        
        content['bias_category'] = ' | '.join(bias_category)
        content['topic'] = row['topic']
        content['location'] = row['location']
        content['text'] = row['text']

        row_dict['content'] = content

        json_str = json.dumps(row_dict)
        json_list.append(json_str)

    return json_list


