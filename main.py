import streamlit as st
import pandas as pd
import requests
import re
import json
import smtplib
from email.mime.text import MIMEText
from urllib.parse import urlparse

# --- 1. SETTINGS & BRANDING ---
st.set_page_config(page_title="Vantedge Intelligence", layout="wide")
st.title("Vantedge-OutReach-Intelligence 🚀")

# --- 2. THE ENGINE (Specific Leads Fix) ---
def get_leads_aggressive(niche, city):
    all_results = []
    headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
    
    # Ye 2 alag queries khud banayega taake results zyada ayen
    queries = [f'"{niche}" in {city} website', f'{niche} contact email {city}']
    
    for q in queries:
        payload = json.dumps({"q": q, "num": 50})
        try:
            res = requests.post("https://google.serper.dev/search", headers=headers, data=payload).json()
            if "organic" in res:
                all_results.extend(res["organic"])
        except:
            continue
    return all_results

def get_email_fast(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        # Deep regex for emails
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', response.text)
        # Filter junk like .png, .jpg, .webp
        valid = [e.lower() for e in set(emails) if not any(x in e.lower() for x in ['.png', '.jpg', '.webp', 'sentry.io', 'example'])]
        return valid[0] if valid else None
    except:
        return None

# --- 3. UI TABS (Wapas Outreach ke saath) ---
tab1, tab2 = st.tabs(["🔍 Lead Hunter", "📧 AI Outreach"])

with tab1:
    col1, col2 = st.columns(2)
    n_in = col1.text_input("Niche", value="Marketing Agency", key="niche")
    c_in = col2.text_input("City", value="Dubai", key="city")
    
    if st.button("Start Extraction"):
        with st.spinner("Hunting leads..."):
            raw_data = get_leads_aggressive(n_in, c_in)
            # Remove duplicates
            unique_links = {item['link']: item for item in raw_data}.values()
            
            leads_final = []
            p = st.progress(0)
            for i, item in enumerate(unique_links):
                email = get_email_fast(item['link'])
                if email:
                    leads_final.append({"Business": item['title'], "Website": item['link'], "Email": email})
                p.progress((i + 1) / len(unique_links))
            
            st.session_state.leads = leads_final
            if leads_final:
                st.success(f"Found {len(leads_final)} Leads!")
                st.table(pd.DataFrame(leads_final))
            else:
                st.error("Still no emails? Check your Serper API Key in Secrets.")

with tab2:
    if 'leads' in st.session_state and st.session_state.leads:
        st.subheader("Auto Outreach Control")
        for i, lead in enumerate(st.session_state.leads):
            with st.expander(f"Lead: {lead['Business']}"):
                st.write(f"Email: {lead['Email']}")
                if st.button(f"Send AI Pitch", key=f"pitch_{i}"):
                    try:
                        server = smtplib.SMTP("smtp.gmail.com", 587)
                        server.starttls()
                        # App Password use karein yahan
                        server.login(st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASSWORD"])
                        
                        msg = MIMEText(f"Hi {lead['Business']},\n\nWe found your site {lead['Website']}...")
                        msg['Subject'] = "Collaboration Request"
                        msg['From'] = st.secrets["GMAIL_USER"]
                        msg['To'] = lead['Email']
                        
                        server.sendmail(st.secrets["GMAIL_USER"], lead['Email'], msg.as_string())
                        server.quit()
                        st.success("Sent!")
                    except Exception as e:
                        st.error(f"Gmail Error: {e}")
    else:
        st.info("Pehle leads extract karein.")
