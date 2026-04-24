import streamlit as st
import os

from parser import parse_file
from extractor import get_keyword_processor, extract_all_facts, load_taxonomy
from scorer import score_cv, generate_feedback

# Initialize page config
st.set_page_config(page_title="Advanced CV Analyzer", page_icon="📄", layout="wide")

# Ensure skills.json exists
if not os.path.exists("skills.json"):
    st.error("skills.json file not found in the root directory. Please provide one for the KeywordProcessor.")
    st.stop()

# Initialize resources
@st.cache_resource
def load_resources():
    kp = get_keyword_processor("skills.json")
    tax = load_taxonomy("taxonomy.json")
    return kp, tax

keyword_processor, taxonomy = load_resources()

# UI Layout
st.title("📄 Advanced Deterministic CV Analyzer")
st.markdown("""
This application analyzes a candidate's CV against a Job Description using an advanced 100% deterministic, rule-based engine. 
It evaluates **Relevance**, **Formatting**, **Action Verbs**, **Metrics**, **Timeline**, and **Grammar**.
""")

st.divider()

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Job Description (JD)")
    jd_text = st.text_area("Paste the Job Description here:", height=300, placeholder="We are looking for a Software Engineer with experience in Python, Django, and SQL...")

with col2:
    st.subheader("2. Upload CV")
    uploaded_file = st.file_uploader("Choose a PDF, DOCX, or Image file", type=["pdf", "docx", "png", "jpg", "jpeg"])

if st.button("Analyze Detailed CV", type="primary"):
    if not jd_text.strip():
        st.warning("Please provide a Job Description.")
    elif not uploaded_file:
        st.warning("Please upload a CV file.")
    else:
        with st.spinner("Parsing and analyzing CV..."):
            # Phase 1: Parse Text
            cv_text = parse_file(uploaded_file, uploaded_file.name)
            
            if not cv_text.strip():
                st.error("⚠️ No text could be extracted from this file. If it's an image, please ensure Tesseract OCR is installed and configured.")
                with st.expander("Debug: Why did this happen?"):
                    st.write("The parser returned an empty string. Possible reasons:")
                    st.write("- Image OCR failed (is Tesseract installed?)")
                    st.write("- PDF is a 'scanned' PDF (images only) and OCR isn't working.")
                    st.write("- DOCX/PDF file is corrupted or empty.")
                st.stop()

            # Phase 2: Extract Facts (Advanced)
            facts = extract_all_facts(cv_text, keyword_processor, taxonomy)
            
            # Phase 3: Detailed Scoring
            scoring = score_cv(facts, jd_text, keyword_processor)
            
            # Phase 4: Generate Targeted Feedback
            feedback = generate_feedback(facts, scoring)
            
        st.success("Detailed Analysis Complete!")

        # Debug: Show extracted text
        with st.expander("🔍 View Extracted Raw Text (Debug)"):
            st.code(cv_text)
        
        st.divider()
        
        # Display Results Dashboard
        score_col, details_col = st.columns([1, 2])
        
        with score_col:
            st.header("Overall ATS Score")
            score_val = scoring["overall_score"]
            if score_val >= 80:
                color = "green"
            elif score_val >= 60:
                color = "orange"
            else:
                color = "red"
                
            st.markdown(f"<h1 style='text-align: center; color: {color}; font-size: 4rem;'>{score_val}%</h1>", unsafe_allow_html=True)
            st.progress(score_val / 100.0)
            
            st.subheader("Category Breakdown")
            for cat, val in scoring["category_scores"].items():
                st.write(f"**{cat.replace('_', ' ').title()}:** {val}%")
                st.progress(val / 100.0)
            
            st.divider()
            st.subheader("Candidate Details")
            st.write(f"**📧 Email:** {facts['email'] if facts['email'] else 'Not Found'}")
            st.write(f"**📞 Phone:** {facts['phone'] if facts['phone'] else 'Not Found'}")
            st.write(f"**⏱️ Total Experience:** {facts['experience'] if facts['experience'] else 'Not Found'}")

        with details_col:
            st.subheader("Skill Alignment")
            
            st.write("**Matching Skills (Found in both CV and JD):**")
            if scoring["matching_skills"]:
                tags = " ".join([f"<span style='background-color:#d4edda; color:#155724; padding:4px 8px; border-radius:4px; margin:4px; display:inline-block;'>{s}</span>" for s in scoring["matching_skills"]])
                st.markdown(tags, unsafe_allow_html=True)
            else:
                st.write("None")
                
            st.write("**Missing Skills (Required by JD but missing in CV):**")
            if scoring["missing_skills"]:
                tags = " ".join([f"<span style='background-color:#f8d7da; color:#721c24; padding:4px 8px; border-radius:4px; margin:4px; display:inline-block;'>{s}</span>" for s in scoring["missing_skills"]])
                st.markdown(tags, unsafe_allow_html=True)
            else:
                st.write("None")
                
            st.write("**Additional Skills (Found in CV but not required by JD):**")
            additional = facts["skills"] - scoring["required_skills"]
            if additional:
                tags = " ".join([f"<span style='background-color:#e2e3e5; color:#383d41; padding:4px 8px; border-radius:4px; margin:4px; display:inline-block;'>{s}</span>" for s in additional])
                st.markdown(tags, unsafe_allow_html=True)
            else:
                st.write("None")

            st.divider()
            
            st.subheader("Advanced Extracted Features")
            exp_details = facts.get("experience_quality", {})
            st.write(f"**Sections Detected:** {', '.join(facts.get('sections', {}).get('sections_found', []))}")
            st.write(f"**Action Verbs Detected:** {len(exp_details.get('action_verbs', []))}")
            st.write(f"**Metrics/Numbers Detected:** {exp_details.get('metrics_count', 0)}")
            
        st.divider()
        
        if feedback:
            st.subheader("⚠️ Targeted Suggestions to Improve Your CV")
            for fb in feedback:
                st.warning(fb)
