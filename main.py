import streamlit as st
import pandas as pd
import requests
import re
import json
import smtplib
from email.mime.text import MIMEText
from groq import Groq
from urllib.parse import urlparse

# --- 1. CONFIG & UI ---
DARK_LOGO = "https://raw.githubusercontent.com/Vantedge-Omni-Agents/Vantedge-OutReach-Agent/main/logo.png"
st.set_page_config(page_title="Vantedge Intelligence", page_icon=DARK_LOGO, layout="wide")

# Sidebar for Branding
st.sidebar.image(DARK_LOGO, use_container_width=True)
st.sidebar.title("Vantedge Control")

# --- 2. LEAD HUNTER ENGINE (High Quantity) ---
def get_bulk_emails(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', response.text)
        
        blacklist = ['.webp', '.png', '.jpg', 'sentry.io', 'example', 'yourcompany']
        valid = [e.lower() for e in set(emails) if not any(x in e.lower() for x in blacklist)]
        
        return valid[0] if valid else None
    except:
        return None

# --- 3. MAIN APP INTERFACE ---
st.title("Vantedge-OutReach-Intelligence 🚀")

tab1, tab2 = st.tabs(["🔍 Lead Hunter", "📧 AI Outreach"])

with tab1:
    c1, c2 = st.columns(2)
    niche = c1.text_input("Target Niche", placeholder="e.g. Marketing Agency")
    city = c2.text_input("Target City", placeholder="e.g. Dubai")
    
    if st.button("Start Bulk Extraction"):
        if niche and city:
            with st.spinner("Hunting for leads across multiple pages..."):
                headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
                
                # Double the pages for more leads
                all_leads = []
                for start in [0, 10]:
                    payload = json.dumps({"q": f'"{niche}" {city} website', "num": 100, "start": start})
                    res = requests.post("https://google.serper.dev/search", headers=headers, data=payload).json()
                    if "organic" in res:
                        all_leads.extend(res["organic"])

                unique_results = {item['link']: item for item in all_leads}.values()
                leads_data = []
                progress = st.progress(0)
                
                for i, item in enumerate(unique_results):
                    email = get_bulk_emails(item['link'])
                    if email:
                        leads_data.append({"Business": item['title'], "Website": item['link'], "Email": email})
                    progress.progress((i + 1) / len(unique_results))
                
                st.session_state.leads = leads_data
                if leads_data:
                    st.success(f"Found {len(leads_data)} Verified Leads!")
                    st.table(pd.DataFrame(leads_data))
                else:
                    st.warning("No emails found. Try a broader niche.")

with tab2:
    if 'leads' in st.session_state and st.session_state.leads:
        st.subheader("Send Personalized AI Pitches")
        
        # UI for AI Outreach (As requested, back to original style)
        for i, lead in enumerate(st.session_state.leads):
            with st.expander(f"Lead: {lead['Business']}"):
                st.write(f"**Target Email:** {lead['Email']}")
                receiver = st.text_input("Receiver Email", value=lead['Email'], key=f"rev_{i}")
                
                if st.button(f"Send AI Pitch to {lead['Business']}", key=f"btn_{i}"):
                    try:
                        # Simple SMTP Setup
                        server = smtplib.SMTP("smtp.gmail.com", 587)
                        server.starttls()
                        # Use App Password here!
                        server.login(st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASSWORD"])
                        
                        msg = MIMEText(f"Hello {lead['Business']},\n\nWe saw your website {lead['Website']} and would love to collaborate.")
                        msg['Subject'] = f"Collaboration Proposal for {lead['Business']}"
                        msg['From'] = st.secrets["GMAIL_USER"]
                        msg['To'] = receiver
                        
                        server.sendmail(st.secrets["GMAIL_USER"], receiver, msg.as_string())
                        server.quit()
                        st.success(f"Email sent to {lead['Business']}!")
                    except Exception as e:
                        st.error(f"Gmail Error: {e}")
    else:
        st.info("Please extract leads in the 'Lead Hunter' tab first.")
