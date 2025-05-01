from openai import OpenAI
import sqlite3
import markdown
from docx.shared import Pt
import io
import re
from spire.doc import *
from spire.doc.common import *
from datetime import date

def generate_refined_report(raw_findings,selected,comments, openai_client):
    """Generate a refined report using the appropriate GPT model."""

    
    model = 'gpt-4o'
    prompt=()
    if comments:
        prompt = (
            f"Act as a professional {selected} and Refine the following medical report.\n\n"
            f"Raw report: {raw_findings}\n\n"
            "give your output in strict markdown format."
            """
            also provide the output in following format,\n\n
        
            patient information,
            Investigation method,
            Technique,
            clinical profile,
            findings,
            impression

            If you dont find clinical profile in the raw report, then just skip the section without mentioning it and try to determine other sections by yourself.
            
            Enhance the given raw medical findings by integrating logical diagnostic reasoning. You must:
            1. **Embed clinically relevant analysis seamlessly** within the findings section — do not create a separate 'Analysis' section or use casual phrases like "this might mean".
            2. Use **professional medical terminology** to infer additional possibilities, correlations, or implications based on the findings.
            3. Highlight possible causes, differential diagnoses, or suggestive patterns that may aid in disease identification — even if not explicitly mentioned.
            4. Maintain a factual, evidence-based tone — reference imaging signs, lab patterns, anatomical context, or pathophysiology where possible.
            5. Provide an enhanced "Impression" section derived not only from the given findings but also from your integrated medical reasoning.
            Also highlight the positive findings in the report with **bold**

            When describing anatomical locations, avoid repeating the same phrase (e.g., "medial aspect") multiple times in close succession. Instead:
            - Use alternative descriptors where appropriate.
            - Combine related findings when they involve the same region.
            - Assume implicit context to avoid stating the same location repeatedly unless clinically essential.
            Also highlight the positive findings in the report with **bold**

            Cross-check all sections for internal consistency. If any values, laterality (e.g., left vs. right), or statements are clearly incorrect, contradictory, or medically implausible, correct them based on logical inference from the full report. 
            
            - For numerical values (e.g., abnormal measurements or illogical anatomy), revise only if they are clearly erroneous or physiologically impossible.
            - For inconsistent references (e.g., left in findings but right in impression), resolve based on context and maintain report integrity.
            - Maintain original tone and structure — do not highlight the correction as an "edit" or explain it separately.
            - Do NOT introduce casual language or guesswork — only fix what is clearly incorrect or contradictory.
            """

            f"Doctor has some preference for his report : {comments}, analize it and add an explicit section according to his preference."
            """
            You must format the findings and impression output exactly like this:
            
            - Heading
            \t- Subheading
            \t\t- Content
            
            OR
            
            - Heading
            \t- Content

            Rules:
            - Use EXACTLY one dash and one space ("- ") for bullets.
            - Use EXACTLY one tab ("\t") for each indentation level.
            - If subheadings exist, nest content below them.
            - If no subheading, put content directly after one tab.
            - Do not add blank lines between bullets or headings.
            """
            )
    else:
        prompt = (
            
            f"Act as a professional {selected} and Refine the following medical report.\n\n"
            f"Raw report: {raw_findings}\n\n"
            "give your output in strict markdown format."
            """
            also provide the output in following format,\n\n
        
            patient information,
            Investigation method,
            Technique,
            clinical profile,
            findings,
            impression

            If you dont find clinical profile in the raw report, then just skip the section without mentioning it and try to determine other sections by yourself.
            
            Enhance the given raw medical findings by integrating logical diagnostic reasoning. You must:
            1. **Embed clinically relevant analysis seamlessly** within the findings section — do not create a separate 'Analysis' section or use casual phrases like "this might mean".
            2. Use **professional medical terminology** to infer additional possibilities, correlations, or implications based on the findings.
            3. Highlight possible causes, differential diagnoses, or suggestive patterns that may aid in disease identification — even if not explicitly mentioned.
            4. Maintain a factual, evidence-based tone — reference imaging signs, lab patterns, anatomical context, or pathophysiology where possible.
            5. Provide an enhanced "Impression" section derived not only from the given findings but also from your integrated medical reasoning.
            Also highlight the positive findings in the report with **bold**

            When describing anatomical locations, avoid repeating the same phrase (e.g., "medial aspect") multiple times in close succession. Instead:
            - Use alternative descriptors where appropriate.
            - Combine related findings when they involve the same region.
            - Assume implicit context to avoid stating the same location repeatedly unless clinically essential.
            Also highlight the positive findings in the report with **bold**
            
            Cross-check all sections for internal consistency. If any values, laterality (e.g., left vs. right), or statements are clearly incorrect, contradictory, or medically implausible, correct them based on logical inference from the full report. 

            - For numerical values (e.g., abnormal measurements or illogical anatomy), revise only if they are clearly erroneous or physiologically impossible.
            - For inconsistent references (e.g., left in findings but right in impression), resolve based on context and maintain report integrity.
            - Maintain original tone and structure — do not highlight the correction as an "edit" or explain it separately.
            - Do NOT introduce casual language or guesswork — only fix what is clearly incorrect or contradictory.
            
            You must format the findings and impression output exactly like this:
            
            - Heading
            \t- Subheading
            \t\t- Content
            
            OR
            
            - Heading
            \t- Content

            Rules:
            - Use EXACTLY one dash and one space ("- ") for bullets.
            - Use EXACTLY one tab ("\t") for each indentation level.
            - If subheadings exist, nest content below them.
            - If no subheading, put content directly after one tab.
            - Do not add blank lines between bullets or headings.
            """
        ) 
    try:
        response = openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
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
