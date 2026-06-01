import streamlit as st

# Configure the page (must be the first Streamlit command)
st.set_page_config(page_title="NL Job Agent", page_icon="🇳🇱", layout="wide")

# Fetch our password securely from Streamlit Cloud
APP_PASSWORD = st.secrets["APP_PASSWORD"]

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
# MAIN WORKSPACE
# ==========================================
st.title("🇳🇱 Highly Skilled Migrant Job Agent")
st.markdown("Welcome back, Hitarrth. Your centralized hub for compliance-first, AI-assisted job hunting.")

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
    st.info("The AI Document generator will go here.")

with tab_settings:
    st.header("Settings")
    st.success("Cloud app deployed successfully!")
