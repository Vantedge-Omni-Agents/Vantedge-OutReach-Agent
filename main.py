import streamlit as st
import pandas as pd
import requests
import re
import json
from urllib.parse import urlparse

# --- 1. CONFIG ---
st.set_page_config(page_title="Vantedge Extreme Hunter", layout="wide")
st.title("Vantedge Extreme Lead Hunter 🚀")

# --- 2. MULTI-PAGE SEARCH (Quantity barhanay ke liye) ---
def get_extreme_leads(niche, city):
    all_results = []
    headers = {
        'X-API-KEY': st.secrets["SERPER_API_KEY"], 
        'Content-Type': 'application/json'
    }
    
    # Page 1 (0) aur Page 2 (10) dono scan karein
    for start_index in [0, 10]:
        payload = json.dumps({
            "q": f'"{niche}" {city} -site:clutch.co -site:facebook.com',
            "num": 100,
            "start": start_index
        })
        try:
            r = requests.post("https://google.serper.dev/search", headers=headers, data=payload).json()
            if "organic" in r:
                all_organic = r["organic"]
                all_results.extend(all_organic)
        except:
            continue
    return all_results

# --- 3. FAST EMAIL FINDER ---
def fast_extract(url):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', res.text)
        
        # Filtering junk
        blacklist = ['.webp', '.png', '.jpg', 'sentry.io', 'example', 'yourcompany']
        valid = [e.lower() for e in set(emails) if not any(x in e.lower() for x in blacklist)]
        
        return valid[0] if valid else None
    except:
        return None

# --- 4. MAIN UI ---
c1, c2 = st.columns(2)
target_niche = c1.text_input("Niche", placeholder="e.g. Marketing Agency")
target_city = c2.text_input("City", placeholder="e.g. United States")

if st.button("Start Bulk Extraction"):
    if target_niche and target_city:
        with st.spinner("Scanning 100+ websites... please wait 1-2 minutes."):
            search_data = get_extreme_leads(target_niche, target_city)
            
            # Remove duplicate links
            unique_data = {item['link']: item for item in search_data}.values()
            
            leads_found = []
            p_bar = st.progress(0)
            
            for i, item in enumerate(unique_data):
                email = fast_extract(item['link'])
                if email:
                    leads_found.append({
                        "Business": item.get('title'),
                        "Website": item.get('link'),
                        "Email": email
                    })
                p_bar.progress((i + 1) / len(unique_data))
            
            if leads_found:
                st.success(f"Found {len(leads_found)} Leads!")
                df = pd.DataFrame(leads_found)
                st.dataframe(df)
                st.download_button("Download Data", df.to_csv(index=False), "leads.csv")
            else:
                st.warning("No emails found. Try a broader niche.")
