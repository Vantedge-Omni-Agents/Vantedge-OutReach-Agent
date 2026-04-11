import streamlit as st
import pandas as pd
import requests
import re
import json
from urllib.parse import urlparse

# --- 1. CONFIG & UI ---
DARK_LOGO = "https://raw.githubusercontent.com/Vantedge-Omni-Agents/Vantedge-OutReach-Agent/main/logo.png"
st.set_page_config(page_title="Vantedge Bulk Hunter", page_icon=DARK_LOGO, layout="wide")

st.title("Vantedge Bulk Lead Extractor 🚀")
st.markdown("### Extract 50-100+ Verified Leads in one click")

# --- 2. THE ULTIMATE SCRAPER ENGINE ---
def get_verified_email(website_url):
    try:
        parsed_url = urlparse(website_url)
        domain = parsed_url.netloc.replace('www.', '')
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        # Quick timeout taake bulk processing fast ho
        response = requests.get(website_url, headers=headers, timeout=5)
        
        # Professional Email Regex
        raw_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', response.text)
        blacklist = ['.webp', '.png', '.jpg', '.jpeg', '.gif', 'sentry.io', 'example.com']
        
        valid_emails = []
        for email in set(raw_emails):
            email = email.lower()
            # Priority: Domain Match (e.g. info@company.com)
            if domain in email and not any(word in email for word in blacklist):
                valid_emails.append(email)
        
        if not valid_emails:
            for email in set(raw_emails):
                if ('gmail' in email or 'outlook' in email) and not any(word in email for word in blacklist):
                    valid_emails.append(email)

        return valid_emails[0] if valid_emails else None
    except:
        return None

# --- 3. SERPER BULK FETCHING ---
def fetch_bulk_leads(niche, city, max_results=100):
    search_url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
    
    # Hum 100 results mangwa rahe hain (Max limit)
    payload = json.dumps({
        "q": f'"{niche}" companies in {city} -site:clutch.co -site:linkedin.com',
        "num": max_results 
    })
    
    response = requests.post(search_url, headers=headers, data=payload).json()
    return response.get('organic', [])

# --- 4. MAIN APP LOGIC ---
c1, c2 = st.columns(2)
target_niche = c1.text_input("Niche", placeholder="e.g. Solar Installers")
target_city = c2.text_input("City", placeholder="e.g. Dubai")

if st.button("Start Bulk Hunting"):
    if target_niche and target_city:
        results = fetch_bulk_leads(target_niche, target_city)
        total_found = len(results)
        
        leads_data = []
        progress_text = "Scanning websites for verified emails..."
        progress_bar = st.progress(0, text=progress_text)
        
        # Fix for the SyntaxError you encountered
        for i, result in enumerate(results):
            url = result.get('link', '')
            email = get_verified_email(url)
            
            if email:
                leads_data.append({
                    "Company": result.get('title'),
                    "Website": url,
                    "Email": email
                })
            
            # Progress update
            progress_bar.progress((i + 1) / total_found)
            
        st.session_state.leads = leads_data
        
        if leads_data:
            st.success(f"Successfully found {len(leads_data)} verified leads from {total_found} websites!")
            df = pd.DataFrame(leads_data)
            st.dataframe(df, use_container_width=True)
            
            # Download Button for Bulk Data
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download All Leads (CSV)", csv, "vantedge_leads.csv", "text/csv")
        else:
            st.warning("No business emails found. Try broadening your niche.")
    else:
        st.error("Please enter both Niche and City.")
