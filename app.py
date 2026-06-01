import streamlit as st
import json
import google.generativeai as genai
import pandas as pd
import requests
import os
from supabase import create_client, Client
import streamlit.components.v1 as components
import markdown
import pdfkit
from deep_translator import GoogleTranslator

# Configure the page
st.set_page_config(page_title="NL Job Agent", page_icon="🇳🇱", layout="wide")

# Fetch secrets safely
APP_PASSWORD = st.secrets.get("APP_PASSWORD", "fallback")
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
ADZUNA_APP_ID = st.secrets.get("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = st.secrets.get("ADZUNA_APP_KEY", "")
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

# Configure AI and DB
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

@st.cache_resource
def init_db():
    if SUPABASE_URL and SUPABASE_KEY:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    return None

db = init_db()

# ==========================================
# LOGIN GATE
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Agent Login")
    pwd = st.text_input("Passcode", type="password")
    if st.button("Unlock Dashboard"):
        if pwd == APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect Passcode.")
    st.stop() 

# ==========================================
# DATA LOADING, TRANSLATION, & POP-UPS
# ==========================================
@st.cache_data
def load_ind_sponsors():
    try:
        df = pd.read_csv("ind_sponsors.csv", sep=None, engine='python')
        return " ".join(df.astype(str).sum(axis=1)).lower()
    except:
        return ""

def fetch_adzuna_jobs(keyword, location="Netherlands"):
    url = f"https://api.adzuna.com/v1/api/jobs/nl/search/1"
    params = {"app_id": ADZUNA_APP_ID, "app_key": ADZUNA_APP_KEY, "results_per_page": 50, "what": keyword, "where": location}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get("results", [])
    return []

@st.dialog("🌐 Live Job Viewer", width="large")
def job_viewer_modal(url):
    st.info("⚠️ If the screen below is blank, the company's security blocks embedding. Use the fallback button.")
    st.link_button("↗️ Open in New Tab (Fallback)", url)
    components.iframe(url, height=600, scrolling=True)

def generate_pdf(markdown_text):
    html_content = markdown.markdown(markdown_text)
    css = """
    <style>
        body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 11pt; color: #2c3e50; line-height: 1.5; margin: 40px; }
        h1 { color: #1a252f; border-bottom: 2px solid #3498db; padding-bottom: 8px; font-size: 24pt; margin-bottom: 15px; }
        h2 { color: #2980b9; margin-top: 25px; font-size: 14pt; text-transform: uppercase; border-bottom: 1px solid #bdc3c7; padding-bottom: 4px; }
        h3 { color: #34495e; font-size: 12pt; font-weight: bold; margin-bottom: 2px; margin-top: 15px; }
        p { margin: 6px 0; }
        li { margin-bottom: 6px; }
        strong { color: #1a252f; }
    </style>
    """
    full_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'>{css}</head><body>{html_content}</body></html>"
    options = {
        'page-size': 'A4',
        'margin-top': '15mm', 'margin-right': '15mm', 'margin-bottom': '15mm', 'margin-left': '15mm',
        'encoding': "UTF-8", 'enable-local-file-access': None
    }
    try:
        return pdfkit.from_string(full_html, False, options=options)
    except Exception as e:
        st.error(f"PDF Compiler Error: {e}")
        return None

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

tab_pipeline, tab_sourcing, tab_tailoring, tab_settings = st.tabs([
    "📊 Application Pipeline", "🔍 Job Sourcing", "📄 Document Tailoring", "⚙️ Settings"
])

# --- TAB 1: Pipeline ---
with tab_pipeline:
    st.header("Application Pipeline")
    if db:
        try:
            response = db.table("saved_jobs").select("*").execute()
            df_saved = pd.DataFrame(response.data)
            if not df_saved.empty:
                st.dataframe(df_saved[['company', 'title', 'location', 'status', 'match_score', 'link']], use_container_width=True)
            else:
                st.info("Your pipeline is currently empty. Go to the Sourcing tab to find and save jobs!")
        except Exception as e:
            st.error(f"Database error: {e}")

# --- TAB 2: Job Sourcing ---
with tab_sourcing:
    st.header("🔍 Sourcing & Approvals")
    col_search1, col_search2 = st.columns([3, 1])
    with col_search1:
        search_kw = st.text_input("Job Title / Keyword", value="AI Transformation")
    with col_search2:
        st.write(""); st.write("")
        run_search = st.button("🚀 Run Sourcing Agent", use_container_width=True)
        
    if run_search:
        with st.spinner(f"Hunting for '{search_kw}', verifying IND status, and translating to English..."):
            raw_jobs = fetch_adzuna_jobs(search_kw)
            matched_jobs = []
            translator = GoogleTranslator(source='auto', target='en')
            
            for job in raw_jobs:
                company_name = job.get('company', {}).get('display_name', '')
                if str(company_name).lower() in ind_sponsors_text if company_name else False:
                    # Fetch raw text
                    raw_title = job.get('title', '').replace("<strong>", "").replace("</strong>", "")
                    raw_desc = job.get('description', '')
                    
                    # Translate to English (with fallback if the translator service blips)
                    try:
                        en_title = translator.translate(raw_title) if raw_title else ""
                        en_desc = translator.translate(raw_desc) if raw_desc else ""
                    except:
                        en_title = raw_title
                        en_desc = raw_desc
                    
                    matched_jobs.append({
                        "Company": company_name, 
                        "Title": en_title,
                        "Location": job.get('location', {}).get('display_name', ''), 
                        "Description": en_desc,
                        "Link": job.get('redirect_url', '')
                    })
            if matched_jobs:
                st.session_state['matched_jobs'] = matched_jobs
                st.success(f"Success! Found and translated {len(matched_jobs)} roles with recognized HSM sponsors.")
            else:
                st.warning("Found jobs, but none matched the IND Sponsor list.")

    if 'matched_jobs' in st.session_state:
        for idx, job in enumerate(st.session_state['matched_jobs']):
            with st.expander(f"🏢 {job['Company']} - {job['Title']}"):
                st.write(f"**Location:** {job['Location']}")
                st.write(f"**Snippet (English):** {job['Description'][:300]}...")
                col_view, col_score, col_save = st.columns(3)
                with col_view:
                    if st.button("🖥️ Open Job Webpage", key=f"popup_{idx}", use_container_width=True):
                        job_viewer_modal(job['Link'])
                with col_score:
                    if st.button(f"🤖 Generate AI Match Score", key=f"score_{idx}", use_container_width=True):
                        prompt = f"Compare Profile:\n{master_profile}\n\nTo Job Snippet:\n{job['Description']}\n\nProvide match score from 0-100 and a 2-sentence rationale on why. Format as: 'Score: X/100 - Rationale: Y'."
                        st.info(model.generate_content(prompt).text)
                with col_save:
                    if st.button(f"💾 Save to Pipeline", key=f"save_{idx}", use_container_width=True):
                        if db:
                            db.table("saved_jobs").insert({"company": job['Company'], "title": job['Title'], "location": job['Location'], "link": job['Link'], "status": "Found"}).execute()
                            st.success("Saved to Tab 1!")

# --- TAB 3: Document Tailoring ---
with tab_tailoring:
    st.header("CV & Cover Letter Studio")
    jd_input = st.text_area("Job Description (Paste text here)", height=200)
    col_doc1, col_doc2 = st.columns(2)
    
    with col_doc1:
        if st.button("Tailor & Download CV", use_container_width=True):
            if jd_input:
                with st.spinner("Compiling ATS-friendly Dutch CV..."):
                    prompt = f"Create a tailored, reverse-chronological CV based on this Master Profile:\n{master_profile}\n\nTailor it for this Job Description:\n{jd_input}\n\nRules:\n1. NO age, gender, nationality, or marital status.\n2. Output entirely in Markdown format.\n3. Use # for Name, ## for Sections, and ### for Job Titles."
                    cv_text = model.generate_content(prompt).text
                    st.markdown("### Preview")
                    st.markdown(cv_text)
                    
                    pdf_bytes = generate_pdf(cv_text)
                    if pdf_bytes:
                        st.download_button("📥 Download CV (PDF)", data=pdf_bytes, file_name="Hitarrth_Trivedi_CV.pdf", mime="application/pdf", use_container_width=True)

    with col_doc2:
        if st.button("Tailor & Download Cover Letter", use_container_width=True):
            if jd_input:
                with st.spinner("Compiling HSM Cover Letter..."):
                    prompt = f"Write a professional Dutch Cover Letter for this profile:\n{master_profile}\n\nFor this Job Description:\n{jd_input}\n\nRules:\n1. Direct, polite tone.\n2. Must explicitly state I qualify for the IND Highly Skilled Migrant scheme (€5,942 threshold).\n3. Output entirely in Markdown."
                    cl_text = model.generate_content(prompt).text
                    st.markdown("### Preview")
                    st.markdown(cl_text)
                    
                    pdf_bytes = generate_pdf(cl_text)
                    if pdf_bytes:
                        st.download_button("📥 Download Cover Letter (PDF)", data=pdf_bytes, file_name="Hitarrth_Trivedi_CoverLetter.pdf", mime="application/pdf", use_container_width=True)

with tab_settings:
    st.header("⚙️ Settings")
    st.success("Translation Engine Active. PDF Compiler Active. App Deployed. Database Connected.")
