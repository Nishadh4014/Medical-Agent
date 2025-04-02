from openai import OpenAI
import sqlite3
import markdown
from docx.shared import Pt
import io
import re
from spire.doc import *
from spire.doc.common import *
from datetime import date

def generate_refined_report(patient_name,patient_age,patient_gender,referred_by,test_done_by,raw_findings, report_type, openai_client):
    """Generate a refined report using the appropriate GPT model."""
    model = 'gpt-4o' if report_type == 'Complex' else 'gpt-3.5-turbo'
    prompt = (
        "Refine the following raw findings into a professional medical report and provide your response in markdown language:\n\n"
        f"Patient name:\n{patient_name}\n\n"
        f"Patient age:\n{patient_age}\n\n"
        f"Patient gender:\n{patient_gender}\n\n"
        f"Referred by:\n{referred_by}\n\n"
        f"Raw Findings:\n{raw_findings}\n\n"
        )
    try:
        response = openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        print(f"Response: {response}")  # Debugging line to check the response
        res=response.choices[0].message.content
        filename="input.md"
        with open(filename, "w", encoding="utf-8") as file:
            file.write(res)
            # print(f"Response saved to {filename}")
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating report: {str(e)}"


def generate_docx(refined_report):
    
    # Convert Markdown to HTML
    html_content = markdown.markdown(refined_report)

    # Create a Word Document
    document = Document()
    
    # Add the HTML content to the Word document
    document.AddSection().AddParagraph().AppendHTML(html_content)

    # Save it as a docx file
    output_path = "output/ToWord.docx"
    document.SaveToFile(output_path, FileFormat.Docx2016)

    # Dispose of resources
    document.Dispose()

    return output_path  # Return the path for downloading


def get_analytics():
    """Retrieve analytics data from the database."""
    analytics = {"Complex": 0, "Non-Complex": 0}
    try:
        with sqlite3.connect('reports.db') as conn:
            c = conn.cursor()
            c.execute("SELECT report_type, COUNT(*) FROM reports GROUP BY report_type")
            rows = c.fetchall()
            for row in rows:
                if row[0] in analytics:
                    analytics[row[0]] = row[1]
    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")
    return analytics
