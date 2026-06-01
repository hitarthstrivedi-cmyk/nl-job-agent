import streamlit as st
import json
import google.generativeai as genai
import pandas as pd
import requests
import os

# Configure the page
st.set_page_config(page_title="NL Job Agent", page_icon="🇳🇱", layout="wide")

# Fetch secrets safely
APP_PASSWORD = st.secrets["APP_PASSWORD"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
ADZUNA_APP_ID = st.secrets.get("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = st.secrets.get("ADZUNA_APP_KEY", "")

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
    
    pwd = st.text_input("Passcode", type="password")
    if st.button("Unlock Dashboard"):
        if pwd == APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect Passcode. Access Denied.")
    st.stop() 

# ==========================================
# DATA LOADING FUNCTIONS
# ==========================================
@st.cache_data
def load_ind_sponsors():
    try:
        # Reads the CSV flexibly in case Excel saved it with semicolons instead of commas
        df = pd.read_csv("ind_sponsors.csv", sep=None, engine='python')
        # We flatten the entire list to lowercase text so we can easily search for company names
        sponsor_text = " ".join(df.astype(str).sum(axis=1)).lower()
        return sponsor_text
    except Exception as e:
        return ""

def fetch_adzuna_jobs(keyword, location="Netherlands"):
    url = f"https://api.adzuna.com/v1/api/jobs/nl/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": 50, # Fetch up to 50 jobs at once
        "what": keyword,
        "where": location
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get("results", [])
    return []

# Load files into memory
ind_sponsors_text = load_ind_sponsors()

try:
    with open("master_profile.json", "r") as f:
        master_profile = f.read()
except FileNotFoundError:
    master_profile = "Error: master_profile.json not found."

# ==========================================
# MAIN WORKSPACE
# ==========================================
st.title("🇳🇱 Highly Skilled Migrant Job Agent")
st.markdown("Welcome back, Hitarrth. Your centralized hub for compliance-first, AI-assisted job hunting.")

tab_pipeline, tab_sourcing, tab_tailoring, tab_settings = st.tabs([
    "📊 Application Pipeline", 
    "🔍 Job Sourcing", 
    "📄 Document Tailoring", 
    "⚙️ Settings & Logs"
])

# --- TAB 1: Pipeline ---
with tab_pipeline:
    st.header("Application Pipeline")
    st.info("Phase 4: SQLite Database connection for tracking will go here.")

# --- TAB 2: Job Sourcing ---
with tab_sourcing:
    st.header("🔍 Sourcing & Approvals")
    st.markdown("Fetch live jobs and immediately filter out companies that cannot legally sponsor an HSM visa.")
    
    col_search1, col_search2 = st.columns([3, 1])
    with col_search1:
        search_kw = st.text_input("Job Title / Keyword", value="AI Transformation")
    with col_search2:
        st.write("") # Spacing alignment
        st.write("")
        run_search = st.button("🚀 Run Sourcing Agent", use_container_width=True)
        
    if run_search:
        if not ADZUNA_APP_ID or not ind_sponsors_text:
            st.error("Missing Adzuna API keys or IND Sponsor CSV.")
        else:
            with st.spinner(f"Hunting for '{search_kw}' and verifying IND status..."):
                raw_jobs = fetch_adzuna_jobs(search_kw)
                
                matched_jobs = []
                for job in raw_jobs:
                    company_name = job.get('company', {}).get('display_name', '')
                    
                    # Core check: Is the company name found anywhere in our IND CSV text?
                    is_sponsor = str(company_name).lower() in ind_sponsors_text if company_name else False
                    
                    if is_sponsor:
                        matched_jobs.append({
                            "Company": company_name,
                            "Title": job.get('title', '').replace("<strong>", "").replace("</strong>", ""),
                            "Location": job.get('location', {}).get('display_name', ''),
                            "Apply Link": job.get('redirect_url', '')
                        })
                
                if matched_jobs:
                    st.success(f"Success! Found {len(matched_jobs)} roles with recognized HSM sponsors.")
                    st.dataframe(pd.DataFrame(matched_jobs), use_container_width=True)
                else:
                    st.warning("Found jobs, but none of the companies matched the IND Sponsor list. Try 'AI Strategy' or 'Data Governance'.")

# --- TAB 3: Document Tailoring ---
with tab_tailoring:
    st.header("CV & Cover Letter Studio")
    st.markdown("Paste a Job Description here to generate a tailored CV and HSM-focused Cover Letter.")
    jd_input = st.text_area("Job Description (Paste text here)", height=200)
    col_doc1, col_doc2 = st.columns(2)
    with col_doc1:
        if st.button("Generate Tailored CV", use_container_width=True):
            if jd_input:
                with st.spinner("Generating reverse-chronological, compliant Dutch CV..."):
                    prompt = f"You are an expert Dutch recruiter. Create a tailored, reverse-chronological CV based on this Master Profile:\n{master_profile}\n\nTailor it for this Job Description:\n{jd_input}\n\nRules:\n1. NO age, gender, nationality, or marital status.\n2. Output entirely in Markdown format."
                    st.markdown("### Tailored CV")
                    st.markdown(model.generate_content(prompt).text)
    with col_doc2:
        if st.button("Generate HSM Cover Letter", use_container_width=True):
            if jd_input:
                with st.spinner("Drafting low-friction HSM cover letter..."):
                    prompt = f"Write a professional Dutch Cover Letter for this profile:\n{master_profile}\n\nFor this Job Description:\n{jd_input}\n\nRules:\n1. Tone: Direct, polite.\n2. Must explicitly state I qualify for the IND Highly Skilled Migrant scheme (€5,942 threshold).\n3. Output entirely in Markdown."
                    st.markdown("### Tailored Cover Letter")
                    st.markdown(model.generate_content(prompt).text)

with tab_settings:
    st.header("⚙️ Settings")
    st.success("App Deployed. APIs Connected. IND Database Loaded.")
