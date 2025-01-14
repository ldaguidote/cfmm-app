import streamlit as st
import pandas as pd
from utils.query import (initialize_parameter_query,
                         build_query,
                         execute_query_to_dataframe,
                         export_query_params_to_json)
from briefbuilder.components import ReportComponentFactory
from prs_generator.generator import Prs
from datetime import date
import json
from io import BytesIO
import streamlit.components.v1 as components


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

## Initialize generate button disable state

if 'run' not in st.session_state:
    st.session_state.run = False

if 'result' not in st.session_state:
    st.session_state.result = None

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

def select_sections():
    st.subheader('Step 6: Select report sections')
    st.markdown('Finally, I want to have the following sections in the report:')

    lst_sections_1 = [
        'Title',
        'Introduction',
        'Methodology',
        'Key Findings',
    ]

    lst_sections_2 = [
        'Final Bias Rating',
        'Bias Category',
        'Final Bias Rating vs. Topics'
    ]

    lst_sections_3 = [
        'Tendency to Commit Very Bias, Bias, Bias/Very Bias'
    ]

    lst_sections_4 = [
        'Very Biased'
    ]
    
    selection_1 = st.pills("Front Sections", lst_sections_1, selection_mode="multi")
    selection_2 = st.pills("Publisher Performance Overview", lst_sections_2, selection_mode="multi")
    selection_3 = st.pills("Publisher Comparison", lst_sections_3, selection_mode="multi")
    selection_4 = st.pills("Use Cases", lst_sections_4, selection_mode="multi")
    sections = selection_1 + selection_2 + selection_3 + selection_4
    return sections

def prepare_data(selected_publisher, start_date, end_date, compared_publishers, bias_category, topics, partial_query):
    dict_params = export_query_params_to_json(
        selected_publisher,
        start_date,
        end_date,
        compared_publishers,
        bias_category,
        topics
    )
    sql = build_query(selected_publisher,
                start_date, end_date,
                compared_publishers,
                bias_category,
                topics,
                partial_query=partial_query)
    df = execute_query_to_dataframe(sql)

    if not partial_query:
        st.session_state['df'] = df
        st.session_state['params'] = dict_params

    return df

def run():
    st.session_state.run = True
    st.session_state.result = None

st.title('Briefing Pack Scope and Coverage')
selected_publisher = select_publisher()
start_date, end_date = select_date_range()
compared_publishers = select_comparison(selected_publisher)
bias_category = select_bias_category()
topics = select_topics()
# sections = select_sections()

btn_preview = st.button('Preview Data')
btn_generate = st.button('Generate Report', on_click=run, disabled=st.session_state.run)
result_container = st.empty()

if btn_preview:
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
        df = prepare_data(
            selected_publisher,
            start_date,
            end_date,
            compared_publishers,
            bias_category,
            topics,
            partial_query=True
        )

        if len(df) > 0:
            df = prepare_data(
                selected_publisher,
                start_date,
                end_date,
                compared_publishers,
                bias_category,
                topics,
                partial_query=False
            )
        else:
            st.error('Invalid request. No articles retrieved for the chosen publisher during the specified time period. '
                    'Try expanding your search criteria.')
            
        df = st.session_state['df'] 
        st.success(f'{len(df)} articles retrieved.')
        st.dataframe(df)

binary_output  = BytesIO()
if st.session_state.run:
    result_container.empty()
    with st.empty():
        with st.spinner('Generating report. Please do not close this page.'):
            df = prepare_data(
                selected_publisher,
                start_date,
                end_date,
                compared_publishers,
                bias_category,
                topics,
                partial_query=False
            )
            dict_params = st.session_state['params']
            df = st.session_state['df']
            rcf = ReportComponentFactory(dict_params, df)
            try:
                rcf.run()
            except:
                st.error("Error in compiling generated text. Please rerun again.")
                st.session_state.run = False
            else:
                dict_rcf = rcf.results
                st.session_state.result = dict_rcf
                factory_json = json.dumps(dict_rcf)
                prs = Prs('template.pptx', factory_json)
                prs.add_Title_section('Briefing Pack for BBC', date.today().strftime("%B %d, %Y"))
                prs.add_Introduction_section('Introduction', 'Placeholder text')
                prs.add_Methodology_section(use_json=True)
                prs.add_KeyFindings_section(use_json=True)
                prs.add_PublisherPerformance_section(use_json=True)
                prs.add_PublisherComparison_section(use_json=True)
                prs.add_Conclusion_section(use_json=True)
                prs.add_Recommendations_section('Recommendations', 'Placeholder text')
                prs.save(binary_output)

    st.session_state.run = False

if st.session_state.result is not None:
    with result_container.container():
        st.success("Done! Click the button below to download")
        st.download_button(
            label = 'Download Report',
            data = binary_output.getvalue(),
            file_name = f'report_{date.today().strftime("%m%d%y")}.pptx'
        )





