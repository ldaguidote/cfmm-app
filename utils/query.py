import pandas as pd
import sqlite3
from datetime import datetime

def make_db_connection():
    conn = sqlite3.connect('cfmm.db')
    return conn

def initialize_parameter_query():
    conn = sqlite3.connect('cfmm.db')
    cursor = conn.cursor()

    # Generate list of publishers from database
    pub_query = 'SELECT publisher FROM articles GROUP BY publisher'
    publishers = [i[0] for i in cursor.execute(pub_query)]

    # Generate list of dates
    date_query = 'SELECT MIN(date_published) min_date, MAX(date_published) max_date FROM articles'
    date_range = [i for i in cursor.execute(date_query)][0]

    query_constraints =  {
        'publishers': publishers,
        'date_range': [datetime.strptime(date_range[0], '%Y-%m-%d'), datetime.strptime(date_range[1], '%Y-%m-%d')]

        }

    conn.close()

    return query_constraints

def build_query(selected_publisher, start_date, end_date, compared_publishers, topics, partial_query=False):
    start_date = start_date.strftime('%Y-%m-%d')
    end_date = end_date.strftime('%Y-%m-%d')
    sql = f"SELECT * FROM articles WHERE (date_published >= '{start_date}' AND date_published <= '{end_date}')"

    if partial_query:
        publishers = [selected_publisher]
    else:
        publishers = [selected_publisher] + compared_publishers

    if len(publishers) > 0:
        publisher_sql = ' AND (' + ' OR '.join([f"publisher LIKE '%{i}%'" for i in publishers]) + ')'
        sql += publisher_sql

    if len(topics) > 0:
        topic_sql = ' AND (' + ' OR '.join([f'topic LIKE "%{i}%"' for i in topics]) + ')'
        sql += topic_sql
    
    return sql

def execute_query_to_dataframe(sql):
    conn = sqlite3.connect('cfmm.db')
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df