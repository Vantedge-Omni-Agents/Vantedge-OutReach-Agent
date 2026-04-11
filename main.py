import streamlit as st
import pandas as pd
import requests
import json
import re
import smtplib
from email.mime.text import MIMEText
from groq import Groq
from bs4 import BeautifulSoup

# --- 1. CONFIG & LOGO ---
DARK_LOGO = "https://raw.githubusercontent.com/Vantedge-Omni-Agents/Vantedge-OutReach-Agent/main/logo.png"
LIGHT_LOGO = "https://raw.githubusercontent.com/Vantedge-Omni-Agents/Vantedge-OutReach-Agent/main/black%20logo.png"

st.set_page_config(page_title="Vantedge AI", page_icon=DARK_LOGO, layout="wide")

# Theme Detection for Sidebar Logo
is_dark = st.get_option("theme.base") == "dark"
st.sidebar.image(DARK_LOGO if is_dark else LIGHT_LOGO, use_container_width=True)
st.sidebar.title("Vantedge Control")

# --- 2. EMAIL SCRAPER LOGIC (Kud fetch karne ke liye) ---
def fetch_emails_from_url(url):
    try:
        response = requests.get(url, timeout=5)
        # Email pattern matching
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', response.text)
        # Filter out common junk emails
        valid_emails = [e for e in set(emails) if not e.endswith(('.png', '.jpg', '.gif', 'sentry.io'))]
        return valid_emails[0] if valid_emails else "No Email Found"
    except:
        return "Connection Error"

# --- 3. SECRETS ---
try:
    SERPER_KEY = st.secrets["SERPER_API_KEY"]
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
    GMAIL_USER = st.secrets["GMAIL_USER"]
    GMAIL_PASS = st.secrets["GMAIL_PASSWORD"]
except:
    st.error("Secrets setup missing!")
    st.stop()

client = Groq(api_key=GROQ_KEY)

# --- 4. UI INTERFACE ---
st.title("Vantedge-OutReach-Intelligence 🚀")
tabs = st.tabs(["Lead Hunter", "AI Outreach"])

with tabs[0]:
    c1, c2 = st.columns(2)
    niche = c1.text_input("Target Niche", placeholder="e.g. Marketing Agency")
    city = c2.text_input("Target City", placeholder="e.g. Pakistan")
    
    if st.button("Start Extraction"):
        with st.spinner("Directly fetching emails from websites..."):
            url = "https://google.serper.dev/search"
            # AI focused query to avoid PDFs and lists
            query = f'"{niche}" site:.com OR site:.pk "{city}" contact email'
            headers = {'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json'}
            res = requests.post(url, headers=headers, data=json.dumps({"q": query, "num": 10})).json()
            
            leads_data = []
            if "organic" in res:
                for lead in res["organic"]:
                    link = lead.get('link', '')
                    # PDFs ko skip karo
                    if ".pdf" in link.lower(): continue
                    
                    scraped_email = fetch_emails_from_url(link)
                    leads_data.append({
                        "Agency": lead['title'],
                        "Website": link,
                        "Email": scraped_email
                    })
                
                st.session_state.leads = leads_data
                st.success(f"Found {len(leads_data)} potential agencies!")
                st.table(pd.DataFrame(leads_data))

with tabs[1]:
    if 'leads' in st.session_state:
        for i, lead in enumerate(st.session_state.leads):
            if lead['Email'] != "No Email Found" and lead['Email'] != "Connection Error":
                with st.expander(f"Contact: {lead['Agency']}"):
                    st.write(f"**Target Email:** {lead['Email']}")
                    if st.button(f"Generate & Send to {lead['Agency']}", key=f"btn_{i}"):
                        # Generate Pitch using Groq
                        prompt = f"Write a 2-line business pitch for {lead['Agency']}. Website: {lead['Website']}"
                        pitch = client.chat.completions.create(
                            messages=[{"role": "user", "content": prompt}],
                            model="llama-3.3-70b-versatile"
                        ).choices[0].message.content
                        
                        # Send Email
                        msg = MIMEText(pitch)
                        msg['Subject'] = "Partnership Proposal"
                        msg['From'] = GMAIL_USER
                        msg['To'] = lead['Email']
                        
                        try:
                            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                            server.login(GMAIL_USER, GMAIL_PASS)
                            server.sendmail(GMAIL_USER, lead['Email'], msg.as_string())
                            server.quit()
                            st.success(f"Sent to {lead['Email']}!")
                        except:
                            st.error("Failed to send. Check App Password.")
    else:
        st.info("Pehle 'Lead Hunter' tab mein leads nikalen.")
