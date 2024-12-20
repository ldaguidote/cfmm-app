import streamlit as st
from briefbuilder.components import ReportComponentFactory
from prs_generator.generator import Prs
from datetime import date
import json


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

st.title('Briefing Pack Scope and Coverage')
sections = select_sections()

if st.button('Generate Report'):
    dict_params = st.session_state['params']
    df = st.session_state['df']
    rcf = ReportComponentFactory(dict_params, df)
    rcf.run()
    dict_rcf = rcf.results
    st.write(dict_rcf)
    factory_json = json.dumps(dict_rcf)
    

    prs = Prs('template.pptx', factory_json)
    # secfunc_mapper = {
    #     'Title': prs.add_Title_section('Briefing Pack for BBC', date.today().strftime("%B %d, %Y")),
    #     'Introduction': prs.add_Introduction_section('Introduction', 'Placeholder text'),
    #     'Methodology': prs.add_Methodology_section(use_json=True),
    #     'Key Findings':,
    #     'Final Bias Rating':,
    #     'Bias Category':,
    #     'Final Bias Rating vs. Topics':,
    #     'Tendency to Commit Very Bias, Bias, Bias/Very Bias':,
    #     'Very Biased':
    # }
    prs.add_Title_section('Briefing Pack for BBC', date.today().strftime("%B %d, %Y"))
    prs.add_Introduction_section('Introduction', 'Placeholder text')
    prs.add_Methodology_section(use_json=True)
    prs.add_KeyFindings_section(use_json=True)
    prs.add_PublisherPerformance_section(use_json=True)
    prs.add_PublisherComparison_section(use_json=True)
    prs.add_Conclusion_section(use_json=True)
    prs.add_Recommendations_section('Recommendations', 'Placeholder text')
    prs.save('tmp.pptx')