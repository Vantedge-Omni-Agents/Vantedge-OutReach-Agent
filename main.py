import streamlit as st
import pandas as pd
import requests
import re
import smtplib
import json
from email.mime.text import MIMEText
from groq import Groq
from urllib.parse import urlparse

# --- 1. CONFIG & LOGO ---
DARK_LOGO = "https://raw.githubusercontent.com/Vantedge-Omni-Agents/Vantedge-OutReach-Agent/main/logo.png"
LIGHT_LOGO = "https://raw.githubusercontent.com/Vantedge-Omni-Agents/Vantedge-OutReach-Agent/main/black%20logo.png"

st.set_page_config(page_title="Vantedge Bulk Hunter", page_icon=DARK_LOGO, layout="wide")

# Dynamic Logo Logic
is_dark = st.get_option("theme.base") == "dark"
st.sidebar.image(DARK_LOGO if is_dark else LIGHT_LOGO, use_container_width=True)
st.sidebar.title("Vantedge Bulk Hunter")

# --- 2. SMART BULK SCRAPER ---
def get_verified_email(website_url):
    try:
        parsed_url = urlparse(website_url)
        domain = parsed_url.netloc.replace('www.', '')
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        # Timeout thora kam rakha hai taake bulk scraping slow na ho
        response = requests.get(website_url, headers=headers, timeout=5)
        
        raw_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', response.text)
        blacklist = ['.webp', '.png', '.jpg', '.jpeg', '.gif', 'sentry.io', 'example.com']
        
        valid_emails = []
        for email in set(raw_emails):
            email = email.lower()
            # Priority 1: Domain Match
            if domain in email and not any(word in email for word in blacklist):
                valid_emails.append(email)
        
        # Priority 2: Generic if no domain match
        if not valid_emails:
            for email in set(raw_emails):
                if 'gmail' in email or 'outlook' in email:
                    valid_emails.append(email)

        return valid_emails[0] if valid_emails else None
    except:
        return None

# --- 3. SECRETS ---
try:
    SERPER_KEY = st.secrets["SERPER_API_KEY"]
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("API Keys missing in secrets!")
    st.stop()

# --- 4. MAIN UI ---
st.title("Vantedge Bulk Lead Extractor 🚀")

col1, col2 = st.columns(2)
niche = col1.text_input("Target Niche", placeholder="e.g. Roofers or Solar Installers")
city = col2.text_input("Target City", placeholder="e.g. Texas")

if st.button("Start Bulk Extraction"):
    if niche and city:
        with st.spinner(f"Extracting up to 100 leads for {niche} in {city}..."):
            # Max Quantity: Search query broadened and num set to 100
            search_url = "https://google.serper.dev/search"
            headers = {'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json'}
            
            # Diverse search query taake zyada results milen
            query = f'"{niche}" companies in {city} website'
            payload = json.dumps({"q": query, "num": 100}) # Yahan quantity barha di hai
            
            res = requests.post(search_url, headers=headers, data=payload).json()
            
            leads_list = []
            if "organic" in res:
                # Progress bar for better UI
                progress_bar = st.progress(0)
                results = res["organic"]
                total = len(results)
                
                for i, result in enumerate(results
