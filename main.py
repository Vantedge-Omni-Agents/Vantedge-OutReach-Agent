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
st.info("Tip: Search for broad terms like 'Real Estate' or 'Solar' to get 50+ leads.")

# --- 2. LEAD EXTRACTION ENGINE ---
def extract_email_from_site(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=5)
        
        # Regex for capturing emails
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', response.text)
        
        # Filter junk extensions
        blacklist = ['.webp', '.png', '.jpg', '.jpeg', '.gif', 'sentry.io']
        clean_emails = [e for e in set(emails) if not any(x in e.lower() for x in blacklist)]
        
        if clean_emails:
            # Domain matching priority
            domain = urlparse(url).netloc.replace('www.', '')
            for e in clean_emails:
                if domain in e.lower():
                    return e.lower()
            return clean_emails[0] # Fallback to first available email
        return None
    except:
        return None

# --- 3. BULK SEARCH LOGIC ---
def get_bulk_results(niche, city):
    all_results = []
    # Hum 2 alag queries bhejenge taake double data milay
    queries = [
        f'"{niche}" in {city} website',
        f'{niche} company contact email {city}'
    ]
    
    for q in queries:
        payload = json.dumps({
            "q": q,
            "num": 50 # Per query 50 results mangwa rahay hain
        })
        headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
        res = requests.post("https://google.serper.dev/search", headers=headers, data=payload).json()
        if "organic" in res:
            all_results.extend(res["organic"])
            
    return all_results

# --- 4. APP INTERFACE ---
c1, c2 = st.columns(2)
niche_input = c1.text_input("Target Niche", placeholder="e.g. Marketing Agency")
city_input = c2.text_input("Target City", placeholder="e.g. United States")

if st.button("Start Extreme Extraction"):
    if niche_input and city_input:
        raw_data = get_bulk_results(niche_input, city_input)
        
        # Removing duplicates from search results
        unique_results = {res['link']: res for res in raw_data}.values()
        
        final_leads = []
        progress_bar = st.progress(0, text="Searching and verifying emails...")
        
        for index, item in enumerate(unique_results):
            link = item.get('link', '')
            email = extract_email_from_site(link)
            
            if email:
                final_leads.append({
                    "Business Name": item.get('title'),
                    "Website": link,
                    "Email": email
                })
            
            # Update progress
            progress_bar.progress((index + 1) / len(unique_results))
            
        if final_leads:
            st.success(f"Found {len(final_leads)} Verified Leads!")
            df = pd.DataFrame(final_leads)
            st.dataframe(df, use_container_width=True)
            
            # Export to CSV
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Leads CSV", csv, "bulk_leads.csv", "text/csv")
        else:
            st.warning("No emails found. Try a broader search term.")
    else:
        st.error("Please fill both fields.")
