import streamlit as st

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
    st.write(sections)
    st.write(type(sections))
