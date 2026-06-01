import streamlit as st
import json
import google.generativeai as genai
import os

# Configure the page (must be the first Streamlit command)
st.set_page_config(page_title="NL Job Agent", page_icon="🇳🇱", layout="wide")

# Fetch secrets safely
APP_PASSWORD = st.secrets["Hitarth@2292"]
GEMINI_API_KEY = st.secrets["AQ.Ab8RN6JJWzMazcxlHY6gcFYkjllEmuU_BtbSUQhDgOloF1ySRw"]

# Configure the AI Brain
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ==========================================
# LOGIN GATE
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Agent Login")
    st.markdown("Please enter your passcode to access the workspace.")
    
    pwd = st.text_input("Passcode", type="Hitarth@2292")
    if st.button("Unlock Dashboard"):
        if pwd == APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect Passcode. Access Denied.")
    st.stop() 

# ==========================================
# MAIN WORKSPACE
# ==========================================
st.title("🇳🇱 Highly Skilled Migrant Job Agent")
st.markdown("Welcome back, Hitarrth. Your centralized hub for compliance-first, AI-assisted job hunting.")

# Load Master Profile
try:
    with open("master_profile.json", "r") as f:
        master_profile = f.read()
except FileNotFoundError:
    master_profile = "Error: master_profile.json not found in the repository."

# Define the tabs
tab_pipeline, tab_sourcing, tab_tailoring, tab_settings = st.tabs([
    "📊 Application Pipeline", 
    "🔍 Job Sourcing", 
    "📄 Document Tailoring", 
    "⚙️ Settings & Logs"
])

with tab_pipeline:
    st.header("Application Pipeline")
    st.info("Your database connection will go here in Phase 2.")

with tab_sourcing:
    st.header("Sourcing & Approvals")
    st.info("The IND Sponsor check will appear here.")

with tab_tailoring:
    st.header("CV & Cover Letter Studio")
    st.markdown("Paste a Job Description here to generate a tailored CV and HSM-focused Cover Letter.")
    
    jd_input = st.text_area("Job Description (Paste text here)", height=200)
    
    col_doc1, col_doc2 = st.columns(2)
    with col_doc1:
        if st.button("Generate Tailored CV"):
            if not jd_input:
                st.warning("Please paste a Job Description first.")
            else:
                with st.spinner("Generating reverse-chronological, anti-discrimination compliant Dutch CV..."):
                    prompt = f"""
                    You are an expert Dutch recruiter. Create a tailored, reverse-chronological CV based on this Master Profile:
                    {master_profile}
                    
                    Tailor it for this Job Description:
                    {jd_input}
                    
                    Rules:
                    1. NO age, gender, nationality, or marital status.
                    2. Highlight AI strategy, digital transformation, and tools like Copilot/Power BI if relevant to the JD.
                    3. Output entirely in Markdown format so it is easy to copy and read. Do not include any pleasantries in the output, just the CV text.
                    """
                    response = model.generate_content(prompt)
                    st.markdown("### Tailored CV")
                    st.markdown(response.text)

    with col_doc2:
        if st.button("Generate HSM Cover Letter"):
            if not jd_input:
                st.warning("Please paste a Job Description first.")
            else:
                with st.spinner("Drafting low-friction HSM cover letter..."):
                    prompt = f"""
                    Write a professional, concise Cover Letter for the Netherlands based on my profile:
                    {master_profile}
                    
                    For this Job Description:
                    {jd_input}
                    
                    Rules:
                    1. Tone: Confident, direct (Dutch style), but polite. Focus on translating business challenges into AI use cases.
                    2. Crucial Requirement: The closing paragraph MUST explicitly state that I qualify for the IND Highly Skilled Migrant scheme (meeting the 30+ salary threshold of €5,942), meaning I am a low-friction hire and eligible for fast-track sponsorship.
                    3. Keep it under 400 words.
                    4. Output entirely in Markdown. Do not include any pleasantries in the output, just the letter.
                    """
                    response = model.generate_content(prompt)
                    st.markdown("### Tailored Cover Letter")
                    st.markdown(response.text)

with tab_settings:
    st.header("Settings")
    st.success("Cloud app deployed successfully. AI Brain connected.")
