import pandas as pd
import sqlite3
from datetime import datetime
import json

def make_db_connection():
    conn = sqlite3.connect('new_cfmm_db.db')
    return conn

def initialize_parameter_query():
    conn = sqlite3.connect('new_cfmm_db.db')
    cursor = conn.cursor()

    # Generate list of publishers from database
    pub_query = 'SELECT publisher FROM articles GROUP BY publisher'
    publishers = [i[0] for i in cursor.execute(pub_query)]

    # Generate list of dates
    date_query = 'SELECT MIN(publish_date) min_date, MAX(publish_date) max_date FROM articles'
    date_range = [i for i in cursor.execute(date_query)][0]

    topic_query = 'SELECT DISTINCT(topic_name) FROM topic_list'
    topics = [i[0] for i in cursor.execute(topic_query)]

    query_constraints =  {
        'publishers': publishers,
        'topics': topics,
        'date_range': [datetime.strptime(date_range[0], '%Y-%m-%d'), datetime.strptime(date_range[1], '%Y-%m-%d')]
        }

    conn.close()

    return query_constraints

def build_query(selected_publisher, start_date, end_date, compared_publishers, bias_category, topics, partial_query=False):
    sql = f"""
        SELECT a.article_id,
               a.publish_date,
               a.url,
               a.publisher,
               a.headline,
               a.created_at,
               a.location,
               aa.negative_aspects_tag AS negative_aspects,
               aa.negative_aspects AS negative_aspects_score,
               aa.negative_aspects_analysis,
               aa.generalization_tag AS generalisation,
               aa.generalization AS generalisation_score,
               aa.generalization_analysis AS generalisation_analysis,
               aa.omit_due_prominence_tag AS omit_due_prominence,
               aa.omit_due_prominence AS omit_due_prominence_score,
               aa.omit_due_prominence_analysis,
               aa.headline_bias_tag AS headline_bias,
               aa.headline_bias AS headline_bias_score,
               aa.headline_bias_analysis,
               aa.misrepresentation_tag AS misrepresentation,
               aa.misrepresentation AS misrepresentation_score,
               aa.misrepresentation_analysis,
               aa.is_current,
               aa.bias_rating,
               tl.topic
        FROM articles a 
        LEFT JOIN article_analyses aa on a.article_id = aa.article_id
        """
    
    if len(topics) > 0:
        topic_sql ="""
        LEFT JOIN (
            SELECT
                article_id,
                GROUP_CONCAT(topic_name, ' | ') AS topic
            FROM topic_list
        """
        topic_sql += ' WHERE (' + ' OR '.join([f'topic_name LIKE "%{i}%"' for i in topics]) + ')'

        topic_sql +="""
            GROUP BY article_id
        ) tl on a.article_id = tl.article_id
        """
        sql += topic_sql
    
    date_sql = f"WHERE (publish_date >= '{start_date}' AND publish_date <= '{end_date}')"
    sql += date_sql

    if partial_query:
        publishers = [selected_publisher]
    else:
        publishers = [selected_publisher] + compared_publishers

    if len(publishers) > 0:
        publisher_sql = ' AND (' + ' OR '.join([f"publisher LIKE '%{i}%'" for i in publishers]) + ')'
        sql += publisher_sql

    # if len(bias_category) > 0:
    #     bias_col = {
    #         'Generalizing Claims': 'generalisation',
    #         'Omit Due Prominence': 'omit_due_prominence',
    #         'Negative Aspects and Behaviors': 'negative_aspects',
    #         'Misrepresentation': 'misrepresentation',
    #         'Headline Bias': 'headline_bias'
    #     }
    #     bias_sql = ' AND (' + ' OR '.join([f"{bias_col[i]} = 1" for i in bias_category]) + ')'
    #     sql += bias_sql

    return sql

def execute_query_to_dataframe(sql):
    conn = sqlite3.connect('new_cfmm_db.db')
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df

def export_query_params_to_json(selected_publisher, start_date, end_date, compared_publishers, bias_category, topics):
    query_params = {
        'selected_publisher': selected_publisher,
        'start_date': start_date,
        'end_date': end_date,
        'compared_publishers': compared_publishers,
        'bias_category': bias_category,
        'topics': topics
    }

    return query_params