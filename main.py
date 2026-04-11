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

# Theme Based Logo Logic
is_dark = st.get_option("theme.base") == "dark"
st.sidebar.image(DARK_LOGO if is_dark else LIGHT_LOGO, use_container_width=True)
st.sidebar.title("Vantedge Control")

# --- 2. ADVANCED EMAIL SCRAPER ---
def auto_fetch_email(url):
    try:
        # Business website ko scan karna
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=8)
        
        # Regex to find emails
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', response.text)
        
        # Filter junk (like images or generic dev emails)
        clean_emails = [e for e in set(emails) if not e.endswith(('.png', '.jpg', '.gif', 'sentry.io', 'example.com'))]
        
        return clean_emails[0] if clean_emails else "Email Not Found"
    except:
        return "Not Reachable"

# --- 3. SECRETS ---
try:
    SERPER_KEY = st.secrets["SERPER_API_KEY"]
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
    GMAIL_USER = st.secrets["GMAIL_USER"]
    GMAIL_PASS = st.secrets["GMAIL_PASSWORD"]
except Exception as e:
    st.error(f"Missing Secrets: {e}")
    st.stop()

client = Groq(api_key=GROQ_KEY)

# --- 4. APP UI ---
st.title("Vantedge-OutReach-Intelligence 🚀")
tabs = st.tabs(["Lead Hunter", "AI Outreach"])

with tabs[0]:
    c1, c2 = st.columns(2)
    niche = c1.text_input("Niche (e.g. Real Estate Agency)")
    city = c2.text_input("City (e.g. Lahore)")
    
    if st.button("Start Auto-Extraction"):
        with st.spinner("Hunting for real business websites..."):
            # Query refined to skip PDFs and directories
            search_query = f'"{niche}" in {city} -filetype:pdf -site:facebook.com'
            url = "https://google.serper.dev/search"
            headers = {'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json'}
            res = requests.post(url, headers=headers, data=json.dumps({"q": search_query})).json()
            
            leads_data = []
            if "organic" in res:
                for result in res["organic"]:
                    site_url = result.get('link', '')
                    email = auto_fetch_email(site_url) # Automatic Fetching
                    
                    leads_data.append({
                        "Business Name": result['title'],
                        "Website": site_url,
                        "Found Email": email
                    })
                
                st.session_state.leads = leads_data
                st.success("Extraction Complete!")
                st.table(pd.DataFrame(leads_data))

with tabs[1]:
    if 'leads' in st.session_state:
        for i, lead in enumerate(st.session_state.leads):
            if lead['Found Email'] not in ["Email Not Found", "Not Reachable"]:
                with st.expander(f"Pitch to: {lead['Business Name']}"):
                    st.write(f"**Target:** {lead['Found Email']}")
                    if st.button(f"Generate & Send AI Pitch", key=f"send_{i}"):
                        # AI Generation
                        prompt = f"Write a short, professional pitch to {lead['Business Name']} for marketing services."
                        pitch = client.chat.completions.create(
                            messages=[{"role": "user", "content": prompt}],
                            model="llama-3.3-70b-versatile"
                        ).choices[0].message.content
                        
                        # Sending Logic
                        try:
                            msg = MIMEText(pitch)
                            msg['Subject'] = "Business Proposal"
                            msg['From'] = GMAIL_USER
                            msg['To'] = lead['Found Email']
                            
                            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                            server.login(GMAIL_USER, GMAIL_PASS)
                            server.sendmail(GMAIL_USER, lead['Found Email'], msg.as_string())
                            server.quit()
                            st.success(f"Email sent to {lead['Found Email']}!")
                        except:
                            st.error("Check your Gmail App Password.")
    else:
        st.info("First Fetch the Leads From The Lead Hunter Tab!.")
