import streamlit as st
import pandas as pd
import requests
import json
import smtplib
from email.mime.text import MIMEText
from groq import Groq

# --- 1. TASKBAR & DYNAMIC LOGO SETUP ---
# GitHub ke 'Raw' links aapki specific repository se
# Note: GitHub links mein space ki jagah '%20' use hota hai
DARK_THEME_LOGO = "https://raw.githubusercontent.com/Vantedge-Omni-Agents/Vantedge-OutReach-Agent/main/logo.png" # White icon for dark bg
LIGHT_THEME_LOGO = "https://raw.githubusercontent.com/Vantedge-Omni-Agents/Vantedge-OutReach-Agent/main/black%20logo.png" # Black icon for light bg

# Browser Tab Configuration (Taskbar)
st.set_page_config(
    page_title="Vantedge-OutReach-Agent",
    page_icon=DARK_THEME_LOGO, # Browser tab icon
    layout="wide"
)

# Theme based logic for Sidebar Logo
try:
    # Streamlit theme check
    if st.get_option("theme.base") == "dark":
        logo_url = DARK_THEME_LOGO
    else:
        logo_url = LIGHT_THEME_LOGO
except:
    logo_url = DARK_THEME_LOGO # Safe fallback

# Sidebar Branding
st.sidebar.image(logo_url, use_container_width=True)
st.sidebar.title("Vantedge-OutReach-Beta")

# --- 2. SECRETS & CLIENTS ---
try:
    GROQ_API = st.secrets["GROQ_API_KEY"]
    SERPER_API = st.secrets["SERPER_API_KEY"]
    GMAIL_USER = st.secrets["GMAIL_USER"]
    GMAIL_PASS = st.secrets["GMAIL_PASSWORD"]
except Exception as e:
    st.error("Missing Secrets! Please check Streamlit Cloud Dashboard.")
    st.stop()

client_groq = Groq(api_key=GROQ_API)

# --- 3. EMAIL LOGIC ---
def send_gmail(to_email, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = f"Vantedge Agent <{GMAIL_USER}>"
    msg['To'] = to_email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.sendmail(GMAIL_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Gmail Error: {e}")
        return False

# --- 4. APP INTERFACE ---
st.title("Vantedge-OutReach-Intelligence 🚀")

tabs = st.tabs(["Lead Hunter", "AI Outreach"])

with tabs[0]:
    c1, c2 = st.columns(2)
    niche = c1.text_input("Target Niche", placeholder="e.g. Solar Companies")
    city = c2.text_input("Target City", placeholder="e.g. Dubai")
    
    if st.button("Start Extraction"):
        with st.spinner("Finding leads..."):
            query = f"{niche} in {city} contact email"
            url = "https://google.serper.dev/search"
            headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
            res = requests.post(url, headers=headers, data=json.dumps({"q": query})).json()
            
            if "organic" in res:
                st.session_state.leads = res["organic"]
                st.success(f"Extracted {len(res['organic'])} leads!")
                st.table(pd.DataFrame(res["organic"])[['title', 'link']])

with tabs[1]:
    if 'leads' in st.session_state:
        for i, lead in enumerate(st.session_state.leads):
            with st.expander(f"Lead: {lead['title']}"):
                target = st.text_input("Email Address", key=f"target_{i}")
                if st.button("Send AI Pitch", key=f"btn_{i}"):
                    # AI Contextual Pitch
                    prompt = f"Write a professional 2-line intro to {lead['title']}. Use context: {lead.get('snippet','')}"
                    chat = client_groq.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama-3.3-70b-versatile"
                    )
                    pitch = chat.choices[0].message.content
                    
                    if target and send_gmail(target, "Partnership Opportunity", pitch):
                        st.success(f"Pitch sent to {target}!")
                        st.info(pitch)
    else:
        st.info("No leads found yet. Use Lead Hunter first.")
    
