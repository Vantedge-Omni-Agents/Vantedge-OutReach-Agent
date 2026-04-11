import streamlit as st
import pandas as pd
import requests
import json
import smtplib
from email.mime.text import MIMEText
from groq import Groq

# --- 1. TASKBAR & LOGO SETUP ---
# Ye code browser ke tab (taskbar) mein logo aur naam set karta hai
logo_url = "https://raw.githubusercontent.com/Vantedge-Omni-Agents/Vantedge-OutReach-Agent/main/logo.png"

st.set_page_config(
    page_title="Vantedge Intelligence", 
    page_icon=logo_url, 
    layout="wide"
)

# Sidebar mein logo aur title
st.sidebar.image(logo_url, width=150)
st.sidebar.title("Vantedge Control")

# --- 2. API & GMAIL SECRETS ---
try:
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
    SERPER_KEY = st.secrets["SERPER_API_KEY"]
    MY_EMAIL = st.secrets["GMAIL_USER"]
    MY_PASS = st.secrets["GMAIL_PASSWORD"]
except Exception as e:
    st.error("Please add API keys and Gmail secrets in Streamlit settings.")
    st.stop()

client = Groq(api_key=GROQ_KEY)

# --- 3. HELPER FUNCTIONS ---
def send_email(target, subject, message):
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = f"Vantedge AI <{MY_EMAIL}>"
    msg['To'] = target
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(MY_EMAIL, MY_PASS)
            server.sendmail(MY_EMAIL, target, msg.as_string())
        return True
    except:
        return False

# --- 4. APP UI ---
st.title("Vantedge Intelligence Pro 🚀")

tab1, tab2 = st.tabs(["Lead Hunter", "AI Outreach"])

with tab1:
    niche = st.text_input("Niche (e.g. Tech)")
    city = st.text_input("City (e.g. Karachi)")
    
    if st.button("Find Leads"):
        query = f"{niche} companies in {city} email"
        url = "https://google.serper.dev/search"
        headers = {'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json'}
        data = json.dumps({"q": query, "num": 10})
        
        res = requests.post(url, headers=headers, data=data).json()
        if "organic" in res:
            st.session_state.data = res["organic"]
            st.table(pd.DataFrame(res["organic"])[['title', 'link']])

with tab2:
    if 'data' in st.session_state:
        for i, item in enumerate(st.session_state.data):
            with st.expander(f"Lead: {item['title']}"):
                email_addr = st.text_input("Email", key=f"e{i}")
                if st.button("Generate & Send", key=f"b{i}"):
                    # AI Pitch Generation
                    prompt = f"Write a 2-line business email to {item['title']}. Use: {item.get('snippet','')}"
                    chat
