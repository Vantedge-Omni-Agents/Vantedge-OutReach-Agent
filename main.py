import streamlit as st
import pandas as pd
import requests
import re
import json
import smtplib
from email.mime.text import MIMEText
from urllib.parse import urlparse

# --- 1. CONFIG & BRANDING ---
st.set_page_config(page_title="Vantedge Intelligence", layout="wide")
st.title("Vantedge-OutReach-Intelligence 🚀")

# --- 2. THE SEARCH ENGINE (Fixes the 'Zero Leads' issue) ---
def get_verified_leads(niche, city):
    all_results = []
    # Serper API call with pagination for more results
    headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
    
    # Scanning Page 1 and Page 2
    for start in [0, 10]:
        payload = json.dumps({"q": f'"{niche}" {city} website', "num": 50, "start": start})
        try:
            res = requests.post("https://google.serper.dev/search", headers=headers, data=payload).json()
            if "organic" in res:
                all_results.extend(res["organic"])
        except:
            continue
    return all_results

def scrape_email(url):
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', resp.text)
        # Filter out image files and junk
        valid = [e.lower() for e in set(emails) if not any(x in e.lower() for x in ['.png', '.jpg', '.webp', 'sentry.io'])]
        return valid[0] if valid else None
    except:
        return None

# --- 3. UI TABS ---
tab1, tab2 = st.tabs(["🔍 Lead Hunter", "📧 AI Outreach"])

with tab1:
    col1, col2 = st.columns(2)
    niche_input = col1.text_input("Niche", placeholder="e.g. Solar")
    city_input = col2.text_input("City", placeholder="e.g. Dubai")
    
    if st.button("Start Bulk Extraction"):
        with st.spinner("Hunting for verified emails..."):
            raw_data = get_verified_leads(niche_input, city_input)
            leads = []
            p_bar = st.progress(0)
            
            for i, item in enumerate(raw_data):
                email = scrape_email(item['link'])
                if email:
                    leads.append({"Business": item['title'], "Website": item['link'], "Email": email})
                p_bar.progress((i + 1) / len(raw_data))
            
            st.session_state.leads = leads
            if leads:
                st.success(f"Found {len(leads)} Verified Leads!")
                st.table(pd.DataFrame(leads))
            else:
                st.warning("No emails found. Try a broader niche like 'Real Estate' instead of 'Real Estate Agency'.")

with tab2:
    if 'leads' in st.session_state and st.session_state.leads:
        for i, lead in enumerate(st.session_state.leads):
            with st.expander(f"Pitch to: {lead['Business']}"):
                st.write(f"Target: {lead['Email']}")
                if st.button(f"Send AI Pitch", key=f"send_{i}"):
                    try:
                        server = smtplib.SMTP("smtp.gmail.com", 587)
                        server.starttls()
                        server.login(st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASSWORD"])
                        
                        msg = MIMEText(f"Hi {lead['Business']}, we saw your site {lead['Website']}...")
                        msg['Subject'] = "Business Collaboration"
                        msg['From'] = st.secrets["GMAIL_USER"]
                        msg['To'] = lead['Email']
                        
                        server.sendmail(st.secrets["GMAIL_USER"], lead['Email'], msg.as_string())
                        server.quit()
                        st.success("Email sent successfully!")
                    except Exception as e:
                        st.error(f"Gmail Error: {e}") # This catches the 535 Bad Credentials
    else:
        st.info("Pehle 'Lead Hunter' tab mein leads nikaalein.")
