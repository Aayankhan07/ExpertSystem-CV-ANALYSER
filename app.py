import streamlit as st
import os

from parser import parse_file
from extractor import get_keyword_processor, extract_all_facts, load_taxonomy
from scorer import score_cv, generate_feedback

# Initialize page config
st.set_page_config(page_title="FlashCV Pro | Expert System", page_icon="⚡", layout="wide")

# Custom CSS for Premium Look
st.markdown("""
<style>
    .main {
        background: #0f172a;
    }
    .stApp {
        background: #0f172a;
    }
    .stButton>button {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        padding: 0.6rem 1.2rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.5);
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
    }
    .score-circle {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 150px;
        height: 150px;
        border-radius: 50%;
        background: conic-gradient(#3b82f6 var(--score), #1e293b 0);
        margin: auto;
        position: relative;
    }
    .score-circle::after {
        content: attr(data-score-text);
        position: absolute;
        width: 130px;
        height: 130px;
        background: #0f172a;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        font-weight: bold;
    }
    h1, h2, h3 {
        color: #f8fafc !important;
    }
    .stProgress > div > div > div > div {
        background-color: #3b82f6;
    }
</style>
""", unsafe_allow_html=True)

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
st.title("⚡ FlashCV Pro: AI Expert System")
st.markdown("""
<div class="glass-card">
    <p style='font-size: 1.1rem; color: #94a3b8;'>
        This application analyzes a candidate's CV against a Job Description using an advanced 100% deterministic, rule-based engine. 
        It evaluates <b>Relevance</b>, <b>Formatting</b>, <b>Action Verbs</b>, <b>Metrics</b>, <b>Timeline</b>, and <b>Grammar</b>.
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Job Description (JD)")
    jd_text = st.text_area("Paste the Job Description here:", height=300, placeholder="We are looking for a Software Engineer with experience in Python, Django, and SQL...")

with col2:
    st.subheader("2. Upload CV")
    uploaded_file = st.file_uploader("Choose a PDF, DOCX, or Image file", type=["pdf", "docx", "png", "jpg", "jpeg"])

if st.button("🚀 Analyze Detailed CV", type="primary"):
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
            score_val = scoring["overall_score"]
            if score_val >= 80:
                color = "#22c55e" # Green
            elif score_val >= 60:
                color = "#f59e0b" # Amber
            else:
                color = "#ef4444" # Red
                
            st.markdown(f"""
            <div style='text-align: center;'>
                <div style='font-size: 5rem; font-weight: 800; color: {color}; margin-bottom: 0;'>{score_val}%</div>
                <div style='color: #94a3b8; margin-bottom: 2rem;'>Overall Match Score</div>
            </div>
            """, unsafe_allow_html=True)
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
                tags = " ".join([f"<span style='background-color:rgba(34, 197, 94, 0.2); color:#4ade80; padding:4px 10px; border-radius:6px; margin:4px; display:inline-block; border: 1px solid rgba(34, 197, 94, 0.3); font-weight:500;'>{s}</span>" for s in scoring["matching_skills"]])
                st.markdown(tags, unsafe_allow_html=True)
            else:
                st.write("None")
                
            st.write("**Missing Skills (Required by JD but missing in CV):**")
            if scoring["missing_skills"]:
                tags = " ".join([f"<span style='background-color:rgba(239, 68, 68, 0.2); color:#f87171; padding:4px 10px; border-radius:6px; margin:4px; display:inline-block; border: 1px solid rgba(239, 68, 68, 0.3); font-weight:500;'>{s}</span>" for s in scoring["missing_skills"]])
                st.markdown(tags, unsafe_allow_html=True)
            else:
                st.write("None")
                
            st.write("**Additional Skills (Found in CV but not required by JD):**")
            additional = facts["skills"] - scoring["required_skills"]
            if additional:
                tags = " ".join([f"<span style='background-color:rgba(148, 163, 184, 0.2); color:#cbd5e1; padding:4px 10px; border-radius:6px; margin:4px; display:inline-block; border: 1px solid rgba(148, 163, 184, 0.3); font-weight:500;'>{s}</span>" for s in additional])
                st.markdown(tags, unsafe_allow_html=True)
            else:
                st.write("None")

            st.divider()
            
            st.subheader("🔍 Advanced Insights")
            exp_details = facts.get("experience_quality", {})
            
            feat_col1, feat_col2 = st.columns(2)
            with feat_col1:
                st.markdown(f"""
                <div style='background: rgba(255,255,255,0.03); padding: 1rem; border-radius: 10px; border: 1px solid rgba(255,255,255,0.05);'>
                    <div style='color: #94a3b8; font-size: 0.8rem; text-transform: uppercase;'>Action Verbs</div>
                    <div style='font-size: 1.5rem; font-weight: bold;'>{len(exp_details.get('action_verbs', []))}</div>
                </div>
                """, unsafe_allow_html=True)
            with feat_col2:
                st.markdown(f"""
                <div style='background: rgba(255,255,255,0.03); padding: 1rem; border-radius: 10px; border: 1px solid rgba(255,255,255,0.05);'>
                    <div style='color: #94a3b8; font-size: 0.8rem; text-transform: uppercase;'>Measurable Metrics</div>
                    <div style='font-size: 1.5rem; font-weight: bold;'>{exp_details.get('metrics_count', 0)}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='background: rgba(255,255,255,0.03); padding: 1rem; border-radius: 10px; border: 1px solid rgba(255,255,255,0.05); margin-top: 1rem;'>
                <div style='color: #94a3b8; font-size: 0.8rem; text-transform: uppercase;'>Sections Detected</div>
                <div style='font-size: 1.1rem;'>{', '.join(facts.get('sections', {}).get('sections_found', [])) if facts.get('sections', {}).get('sections_found') else 'None'}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.divider()
        
        if feedback:
            st.subheader("⚠️ Targeted Suggestions to Improve Your CV")
            for fb in feedback:
                st.warning(fb)
