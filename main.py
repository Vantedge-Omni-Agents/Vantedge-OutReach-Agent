import streamlit as st
import pandas as pd
import requests
import re
import json
from urllib.parse import urlparse

# --- 1. CONFIG ---
st.set_page_config(page_title="Vantedge Extreme Bulk", layout="wide")
st.title("Vantedge Extreme Bulk Hunter 🚀")

# --- 2. MULTI-PAGE SEARCH ENGINE ---
def get_extreme_bulk(niche, city):
    all_organic_results = []
    headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
    
    # Hum 3 alag pages se data uthayenge (Total 300 possible links)
    pages_to_scan = [0, 10, 20] 
    
    for page_start in pages_to_scan:
        payload = json.dumps({
            "q": f'"{niche}" {city} -site:clutch.co -site:facebook.com',
            "num": 100,
            "start": page_start
        })
        try:
            res = requests.post("https://google.serper.dev/search", headers=headers, data=payload).json()
            if "organic" in res:
                all_organic_results.extend(res["organic"])
        except:
            continue
            
    return all_organic_results

# --- 3. FAST EMAIL EXTRACTOR ---
def fast_extract(url):
    try:
        # Timeout kam rakha hai taake 300 sites jaldi scan hon
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=4)
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', resp.text)
        
        blacklist = ['.webp', '.png', '.jpg', 'sentry.io', 'example.com', 'yourcompany']
        valid = [e.lower() for e in set(emails) if not any(x in e.lower() for x in blacklist)]
        
        return valid[0] if valid else None
    except:
        return None

# --- 4. UI LOGIC ---
c1, c2 = st.columns(2)
niche = c1.text_input("Niche", placeholder="e.g. Real Estate")
city = c2.text_input("City", placeholder="e.g. Dubai")

if st.button("Start Extreme Bulk Hunting"):
    if niche and city:
        with st.spinner("Scanning 200+ websites... This might take 2-3 minutes."):
            raw_results = get_extreme_bulk(niche, city)
            
            # Remove duplicate links
            unique_links = {item['link']: item for item in raw_results}.values()
            
            final_leads = []
            progress_bar = st.progress(0)
            total = len(unique_links)
            
            for i, item in enumerate(unique_links):
                email = fast_extract(item['link'])
                if email:
                    final_leads.append({
                        "Business": item.get('title'),
                        "Website": item.get('link'),
                        "Email": email
                    })
                progress_bar.progress((i + 1) / total)
            
            if final_leads:
                st.success(f"Found {len(final_leads)} leads successfully!")
                df = pd.DataFrame(final_leads)
                st.dataframe(df)
                st.download_button("Download CSV", df.to_csv(index=False), "extreme_leads.csv")
            else:
                st.warning("No emails found. Try a broader niche.")
