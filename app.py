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
