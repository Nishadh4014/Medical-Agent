import streamlit as st
import os
from openai import OpenAI
import sqlite3
from utils import generate_refined_report, generate_docx, get_analytics
from spire.doc import *
from spire.doc.common import *
from datetime import date

# Set Streamlit page configuration
st.set_page_config(page_title="X-Ray House - Medical Report Refinement", layout="wide")

# Initialize OpenAI API client
openai_api_key = st.secrets.get("OPENAI_API_KEY")
if not openai_api_key:
    st.error("OPENAI_API_KEY environment variable not set")
    st.stop()
openai_client = OpenAI(api_key=openai_api_key)

# # Database setup (create table if not exists)
# with sqlite3.connect('reports.db') as conn:
#     c = conn.cursor() 
#     c.execute('''
#         CREATE TABLE IF NOT EXISTS reports (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
#             patient_name TEXT,
#             age INTEGER,
#             gender TEXT,
#             referred_by TEXT,
#             report_type TEXT NOT NULL,
#             report_file BLOB
#         )
#     ''')
#     conn.commit()

# Sidebar for navigation
page = st.sidebar.selectbox("Choose a page", ["Dashboard", "Refine Report"])

# Initialize session state variables
if "refined_report" not in st.session_state:
    st.session_state.refined_report = None
if "output_file" not in st.session_state:
    st.session_state.output_file = None
if "report_type" not in st.session_state:
    st.session_state.report_type = None

# Dashboard page
if page == "Dashboard":
    st.title("Analytics Dashboard")
    analytics_data = get_analytics()
    st.bar_chart(analytics_data)

# Report refinement page
elif page == "Refine Report":
    st.title("Refine Medical Report")
    
    radiology_options = {
        "op:1":"General Radiologist",
        "op:2":"Neuroradiologist",
        "op:3":"Musculoskeletal (MSK) Radiologist",
        "op:4":"Abdominal Radiologist",
        "op:5":"Chest Radiologist",
        "op:6":"Breast Radiologist",
        "op:7":"Cardiac Radiologist",
        "op:8":"Pediatric Radiologist",
        "op:9":"Emergency & Trauma Radiologist",
        "op:10":"Head & Neck Radiologist",
        "op:11":"Vascular/Interventional Radiologist",
        "op:12":"Fetal/Obstetric Radiologist",
        "op:13":"Onco Radiologist"
    }

    selected = st.selectbox("Select a Radiology Specialty", list(radiology_options.values()))

    st.write("### Enter any comments you have about the report(optional)")
    comments = st.text_area(
        label="Comments",
        height=100,  # height in pixels
    )
 
    with st.form("refine_form"):
        
        st.write("### Enter your raw findings here...")
        raw_findings = st.text_area(
            label="Raw findings",
            height=600,  # height in pixels
        )
        
        col1, col2 = st.columns(2) 
        with col1:
            complex_submit = st.form_submit_button("Refine as Complex Report")
        with col2:
            non_complex_submit = st.form_submit_button("Refine as Non-Complex Report")
    
    # Process form submission for Complex Report
        if complex_submit and raw_findings:
            report_type = "Complex"
            with st.spinner("Refining complex report..."):
                refined_report = generate_refined_report(raw_findings,selected,comments,openai_client)
                # with sqlite3.connect('reports.db') as conn:
                #     c = conn.cursor()
                #     c.execute("INSERT INTO reports (report_type) VALUES (?)", (report_type,))
                #     conn.commit()
            st.session_state.refined_report = refined_report
            st.session_state.report_type = report_type
        
        # Process form submission for Non-Complex Report
        elif non_complex_submit and raw_findings:
            report_type = "Non-Complex"
            with st.spinner("Refining non-complex report..."):
                refined_report = generate_refined_report(raw_findings,selected,comments, openai_client)
                # with sqlite3.connect('reports.db') as conn:
                #     c = conn.cursor()
                #     # c.execute("INSERT INTO reports (report_type) VALUES (?)", (report_type,))
                #     conn.commit()
            st.session_state.refined_report = refined_report
            st.session_state.report_type = report_type
        
        # Display refined report and download button if available
    if st.session_state.refined_report:
        st.write(f"### Refined {st.session_state.report_type} Report")
        

         # Display model output on the UI
        # with st.expander("📋 View Refined Report Output", expanded=True):
        #     st.markdown(st.session_state.refined_report, unsafe_allow_html=True)
        # Generate DOCX file
        docx_filename = generate_docx(st.session_state.refined_report)
        # generate_docx(st.session_state.refined_report, docx_filename)
        
        with open(docx_filename, "rb") as f:
            docx_bytes = f.read()
 
        # with sqlite3.connect('reports.db') as conn:
        #     c = conn.cursor()
        #     c.execute("""
        #         INSERT INTO reports (patient_name, age, gender, referred_by, report_type, report_file)
        #         VALUES (?, ?, ?, ?, ?, ?)
        #     """, ( st.session_state.report_type, docx_bytes))
        #     conn.commit()

        with open(docx_filename, "rb") as file:
            st.download_button(
                label="Download DOCX",
                data=docx_bytes,
                file_name=f"refined_report.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
