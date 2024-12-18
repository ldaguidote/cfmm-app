import streamlit as st
import pandas as pd
from utils.query import (initialize_parameter_query,
                         build_query,
                         execute_query_to_dataframe,
                         export_query_params_to_json)

# This controls the content of the initial page
# Determine the constraints to be set by the application based on the articles in the database and set categories

query_constraints = initialize_parameter_query()
query_constraints['bias_category'] = [
    'Misrepresentation', 'Negative Aspects and Behaviors', 'Generalizing Claims',
    'Due Prominence', 'Headlines'
]
query_constraints['topics'] = [
    'Accidents and Natural Disasters', 'Business and Economy', "Women's and Children's Rights",
    'Crimes and Arrests', 'Education', 'Hate Speech and Discrimination', 'Health',
    'Immigration', 'Minorities and Human Rights', 'Politics', 'Religion',
    'Sports, Culture, and Entertainment', 'Terrorism and Extremism'
]

## APP COMPONENTS

def select_publisher():
    st.subheader('Step 1: Select publisher')
    st.markdown('I want to analyze articles from:')

    selected_publisher = st.selectbox(
        label='Select one from the list of publishers',
        options=query_constraints['publishers'],
        key='selected_publisher',
        )
    
    return selected_publisher
    
def select_date_range():
    st.subheader('Step 2: Select date range of publication')
    st.markdown('Articles must be published within:')

    col1, col2 = st.columns(spec=2, gap='large')
    start_date = col1.date_input(label='Start date', value=query_constraints['date_range'][0],
                                min_value=query_constraints['date_range'][0],
                                max_value=query_constraints['date_range'][1])
    end_date = col2.date_input(label='End date', value=query_constraints['date_range'][1],
                            min_value=query_constraints['date_range'][0],
                            max_value=query_constraints['date_range'][1])
    
    # Typecast to SQL readable format
    start_date = start_date.strftime('%Y-%m-%d')
    end_date = end_date.strftime('%Y-%m-%d')
    return start_date, end_date

@st.fragment()
def select_comparison(selected_publisher):
    st.subheader('Step 3: Select journal comparisons')
    st.markdown(f"The following are publishers with articles dated during the selected time period. "
                f'Please select the relevant publishers you wish to compare against your chosen publisher.')

    container = st.container()
    select_all = st.checkbox('Select all publishers', key='pub_checkbox')

    unselected_pubs = [i for i in query_constraints['publishers'] if i not in [selected_publisher]]

    if select_all:
        compared_publishers = container.multiselect("Select one or more options:",
            unselected_pubs, unselected_pubs)
    else:
        compared_publishers =  container.multiselect("Select one or more options:",
            unselected_pubs)
        
    return compared_publishers

def select_bias_category():
    st.subheader('Step 4: Select bias categories')
    st.markdown('I want to analyze articles having only any of the following bias categories:')

    container = st.container()
    select_all = st.checkbox('Select all bias categories', key='bias_checkbox')

    if select_all:
        bias_category = container.multiselect("Select one or more options:",
            query_constraints['bias_category'], query_constraints['bias_category'])
    else:
        bias_category =  container.multiselect("Select one or more options:",
            query_constraints['bias_category'])
        
    return bias_category

def select_topics():
    st.subheader('Step 5: Select article topics')
    st.markdown('Further, I want to analyze articles having only the following themes:')

    container = st.container()
    select_all = st.checkbox('Select all topics', key='topic_checkbox')

    if select_all:
        topics = container.multiselect("Select one or more options:",
            query_constraints['topics'], query_constraints['topics'])
    else:
        topics =  container.multiselect("Select one or more options:",
            query_constraints['topics'])
        
    return topics

st.title('Briefing Pack Scope and Coverage')
selected_publisher = select_publisher()
start_date, end_date = select_date_range()
compared_publishers = select_comparison(selected_publisher)
bias_category = select_bias_category()
topics = select_topics()

check_1 = st.button('Preview Data')
check_2 = st.button('Proceed to Section Selector')

if check_1 or check_2:
    dict_params = export_query_params_to_json(
        selected_publisher,
        start_date,
        end_date,
        compared_publishers,
        bias_category,
        topics
    )
    if ('df' not in st.session_state or
        st.session_state['params'] is not dict_params):
        # Perform partial query
        sql = build_query(selected_publisher,
                        start_date, end_date,
                        compared_publishers,
                        bias_category,
                        topics,
                        partial_query=True)
        df = execute_query_to_dataframe(sql)

        if len(df) > 0:
            sql = build_query(selected_publisher,
                        start_date, end_date,
                        compared_publishers,
                        bias_category,
                        topics,
                        partial_query=False)
            df = execute_query_to_dataframe(sql)
            st.session_state['df'] = df
            st.session_state['params'] = dict_params

        else:
            st.error('Invalid request. No articles retrieved for the chosen publisher during the specified time period. '
                    'Try expanding your search criteria.')

    if check_1:
        df = st.session_state['df']      
        st.success(f'{len(df)} articles retrieved.')
        st.dataframe(df)

    elif check_2:
        st.switch_page("report-builder/customize_report.py")