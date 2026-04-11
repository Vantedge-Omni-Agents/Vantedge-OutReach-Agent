import streamlit as st
import pandas as pd
import requests
import re
import smtplib
from email.mime.text import MIMEText
from groq import Groq
from bs4 import BeautifulSoup

# --- 1. CONFIG & LOGO ---
DARK_LOGO = "https://raw.githubusercontent.com/Vantedge-Omni-Agents/Vantedge-OutReach-Agent/main/logo.png"
st.set_page_config(page_title="Vantedge AI", page_icon=DARK_LOGO, layout="wide")

# --- 2. THE SMART FILTERING ENGINE ---
def get_clean_business_email(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        # 1. Tamam potential emails nikalen
        raw_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', response.text)
        
        # 2. Blacklist: In extensions aur words wali emails ko reject karo
        blacklist = [
            '.webp', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.pdf', 
            'example.com', 'yourcompany.com', 'domain.com', 'sentry.io', 
            'wixpress.com', 'bootstrap', 'email@email.com'
        ]
        
        valid_emails = []
        for email in set(raw_emails):
            email = email.lower()
            # Check agar email blacklist mein toh nahi
            if not any(word in email for word in blacklist):
                # Professional check: Aksar business emails 'info', 'contact', ya 'hello' se shuru hoti hain
                valid_emails.append(email)
        
        # Sabse pehli saaf email wapis bhejen
        return valid_emails[0] if valid_emails else "No Business Email Found"
    except:
        return "Not Reachable"

# --- 3. SECRETS ---
try:
    SERPER_KEY = st.secrets["SERPER_API_KEY"]
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
    GMAIL_USER = st.secrets["GMAIL_USER"]
    GMAIL_PASS = st.secrets["GMAIL_PASSWORD"]
except:
    st.error("Secrets configuration check karein!")
    st.stop()

client = Groq(api_key=GROQ_KEY)

# --- 4. MAIN APP ---
st.title("Vantedge-OutReach-Intelligence 🚀")
tabs = st.tabs(["Lead Hunter", "AI Outreach"])

with tabs[0]:
    c1, c2 = st.columns(2)
    niche = c1.text_input("Niche", placeholder="e.g. Solar Companies")
    city = c2.text_input("City", placeholder="e.g. Karachi")
    
    if st.button("Start Extraction"):
        with st.spinner("Scraping real business data..."):
            # Refined Search: Directories (Clutch/LinkedIn) ko skip karke direct websites dhoondna
            query = f'"{niche}" in {city} -site:clutch.co -site:semrush.com -site:zoominfo.com'
            headers = {'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json'}
            res = requests.post("https://google.serper.dev/search", headers=headers, json={"q": query}).json()
            
            leads_data = []
            if "organic" in res:
                for result in res["organic"]:
                    site_url = result.get('link', '')
                    # Smart Fetching
                    email = get_clean_business_email(site_url)
                    
                    # Sirf wahi dikhao jinki email mil jaye
                    if email not in ["No Business Email Found", "Not Reachable"]:
                        leads_data.append({
                            "Business Name": result['title'],
                            "Website": site_url,
                            "Email": email
                        })
                
                st.session_state.leads = leads_data
                st.table(pd.DataFrame(leads_data))
