import streamlit as st

parameters_page = st.Page("report-builder/set_report_parameters.py", title="Report Parameters")

# drafts_page = st.Page("report-retriever/view_drafts.py", title="Drafts")
# published_page = st.Page("report-retriever/view_published_reports.py", title="Published Reports")

pg = st.navigation(
    {
        "New Briefing Pack": [parameters_page],
        # "My Reports": [drafts_page, published_page],
    },
    position="hidden"
)

pg.run()
