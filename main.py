import streamlit as st
import pandas as pd
import requests
import re
import smtplib
from email.mime.text import MIMEText
from groq import Groq
from urllib.parse import urlparse

# --- 1. CONFIG & LOGO ---
# White logo for dark mode, Black for light mode
DARK_LOGO = "https://raw.githubusercontent.com/Vantedge-Omni-Agents/Vantedge-OutReach-Agent/main/logo.png"
LIGHT_LOGO = "https://raw.githubusercontent.com/Vantedge-Omni-Agents/Vantedge-OutReach-Agent/main/black%20logo.png"

st.set_page_config(page_title="Vantedge Intelligence", page_icon=DARK_LOGO, layout="wide")

# Sidebar Dynamic Logo
is_dark = st.get_option("theme.base") == "dark"
st.sidebar.image(DARK_LOGO if is_dark else LIGHT_LOGO, use_container_width=True)
st.sidebar.title("Vantedge Control")

# --- 2. SMART DOMAIN VERIFIER (Asli Emails ke liye) ---
def get_verified_business_email(website_url):
    try:
        # Website se domain nikalna (e.g. sirajpower.com)
        parsed_url = urlparse(website_url)
        domain = parsed_url.netloc.replace('www.', '')
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(website_url, headers=headers, timeout=10)
        
        # Tamam emails dhoondna
        raw_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', response.text)
        
        # Kachra filter karne ke liye blacklist
        blacklist = ['.webp', '.png', '.jpg', '.jpeg', '.gif', 'sentry.io', 'example.com', 'yourcompany']
        
        valid_emails = []
        for email in set(raw_emails):
            email = email.lower()
            
            # CRITICAL: Email ka domain website se match hona chahiye
            if domain in email:
                if not any(word in email for word in blacklist):
                    valid_emails.append(email)
        
        # Agar company email nahi mili toh generic (Gmail/Outlook) allow karein
        if not valid_emails:
            for email in set(raw_emails):
                if not any(word in email for word in blacklist):
                    if 'gmail' in email or 'outlook' in email:
                        valid_emails.append(email)

        return valid_emails[0] if valid_emails else None
    except:
        return None

# --- 3. SECRETS SETUP ---
try:
    SERPER_KEY = st.secrets["SERPER_API_KEY"]
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
    GMAIL_USER = st.secrets["GMAIL_USER"]
    GMAIL_PASS = st.secrets["GMAIL_PASSWORD"]
except:
    st.error("Secrets (API Keys) missing hain! Streamlit dashboard check karein.")
    st.stop()

client = Groq(api_key=GROQ_KEY)

# --- 4. UI INTERFACE ---
st.title("Vantedge OutReach Intelligence 🚀")

tab1, tab2 = st.tabs(["Lead Hunter", "AI Outreach"])

with tab1:
    col1, col2 = st.columns(2)
    niche = col1.text_input("Target Niche", placeholder="e.g. Real Estate Agency")
    city = col2.text_input("Target City", placeholder="e.g. Lahore")
    
    if st.button("Find Verified Leads"):
        with st.spinner("Hunting for domain-verified business emails..."):
            # Directories (LinkedIn/Facebook) ko exclude karke direct sites dhoondna
            query = f'"{niche}" in {city} -site:clutch.co -site:linkedin.com -site:facebook.com'
            headers = {'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json'}
            res = requests.post("https://google.serper.dev/search", headers=headers, json={"q": query}).json()
            
            leads = []
            if "organic" in res:
                for result in res["organic"]:
                    link = result.get('link', '')
                    email = get_verified_business_email(link)
                    
                    # Sirf relevant emails add hongi
                    if email:
                        leads.append({
                            "Business Name": result['title'],
                            "Website": link,
                            "Verified Email": email
                        })
            
            st.session_state.leads = leads
            if leads:
                st.success(f"Success! {len(leads)} verified leads mil gayi hain.")
                st.table(pd.DataFrame(leads))
            else:
                st.warning("Koi verified email nahi mili. Search niche change karke dekhein.")

with tab2:
    if 'leads' in st.session_state and st.session_state.leads:
        for i, lead in enumerate(st.session_state.leads):
            with st.expander(f"Pitch to: {lead['Business Name']}"):
                st.write(f"**Target:** {lead['Verified Email']}")
                if st.button(f"Send AI Pitch", key=f"send_{i}"):
                    st.info("Generating and sending email...")
                    # AI and SMTP logic yahan apply hoga
    else:
        st.info("Pehle 'Lead Hunter' tab mein data extract karein.")
