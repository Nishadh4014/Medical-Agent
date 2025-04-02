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

# Database setup (create table if not exists)
with sqlite3.connect('reports.db') as conn:
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            patient_name TEXT,
            age INTEGER,
            gender TEXT,
            referred_by TEXT,
            report_type TEXT NOT NULL,
            report_file BLOB
        )
    ''')
    conn.commit()

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
    
    with st.form("refine_form"):
        st.write("### Patient Information")
        col1, col2, col3 = st.columns(3)
        with col1:
            patient_name = st.text_input("Patient Name")
        with col2:
            patient_age = st.number_input("Age", min_value=0, max_value=120, step=1)
        with col3:
            patient_gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        
        st.write("### Referred By")
        referred_by = st.text_input("Referred By")
        
        st.write("### Current Date")
        current_date = st.date_input("Date", value=date.today())
        
        st.write("### Test Done By Doctor")
        test_done_by = st.text_input("Test Done By")
        
        st.write("### Enter Raw Findings")
        raw_findings = st.text_area("Raw Findings", height=300)
        
        st.write("### Select Report Type")
        col1, col2 = st.columns(2)
        with col1:
            complex_submit = st.form_submit_button("Refine as Complex Report")
        with col2:
            non_complex_submit = st.form_submit_button("Refine as Non-Complex Report")
    
    # Process form submission for Complex Report
        if complex_submit and raw_findings:
            report_type = "Complex"
            with st.spinner("Refining complex report..."):
                refined_report = generate_refined_report(patient_name,patient_age,patient_gender,referred_by,test_done_by,raw_findings, report_type, openai_client)
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
                refined_report = generate_refined_report(patient_name,patient_age,patient_gender,referred_by,test_done_by,raw_findings, report_type, openai_client)
                # with sqlite3.connect('reports.db') as conn:
                #     c = conn.cursor()
                #     # c.execute("INSERT INTO reports (report_type) VALUES (?)", (report_type,))
                #     conn.commit()
            st.session_state.refined_report = refined_report
            st.session_state.report_type = report_type
        
        # Display refined report and download button if available
    if st.session_state.refined_report:
        st.write(f"### Refined {st.session_state.report_type} Report")
        
        # Generate DOCX file
        docx_filename = generate_docx(st.session_state.refined_report)
        # generate_docx(st.session_state.refined_report, docx_filename)
        
        with open(docx_filename, "rb") as f:
            docx_bytes = f.read()

        with sqlite3.connect('reports.db') as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO reports (patient_name, age, gender, referred_by, report_type, report_file)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (patient_name, patient_age, patient_gender, referred_by, st.session_state.report_type, docx_bytes))
            conn.commit()

        with open(docx_filename, "rb") as file:
            st.download_button(
                label="Download DOCX",
                data=docx_bytes,
                file_name=f"{patient_name}_report.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
