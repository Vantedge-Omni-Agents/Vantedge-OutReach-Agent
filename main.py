import streamlit as st
import pandas as pd
import requests
import json
import smtplib
from email.mime.text import MIMEText
from groq import Groq

# --- 1. DYNAMIC LOGO LOGIC ---
# GitHub links for both versions
LIGHT_LOGO = "https://raw.githubusercontent.com/Vantedge-Omni-Agents/Vantedge-OutReach-Agent/main/logo_dark.png" 
DARK_LOGO = "https://raw.githubusercontent.com/Vantedge-Omni-Agents/Vantedge-OutReach-Agent/main/logo_light.png"

# Theme detect karne ke liye trick
# Streamlit settings se theme uthata hai
ms = st.session_state
if "themes" not in ms: 
    ms.themes = "light" # Default

# Taskbar Setup
st.set_page_config(page_title="Vantedge-OutReach-Intelligence", layout="wide")

# Theme ke hisab se logo select karein
# Note: Ye 'base' check karne ke liye custom CSS/JS lagta hai, 
# magar sabse asaan tareeka 'Sidebar' icon use karna hai.
logo_to_use = DARK_LOGO if st.get_option("theme.base") == "dark" else LIGHT_LOGO

# Sidebar Branding
st.sidebar.image(logo_to_use, width=150)
st.sidebar.title("Vantedge-OutReach-Beta")

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

# --- 4. APP UI (Lead Hunter & Outreach) ---
st.title("Vantedge-OutReach-Intelligence  🚀")

tab1, tab2 = st.tabs(["Lead Hunter", "AI Outreach"])

with tab1:
    niche = st.text_input("Niche")
    city = st.text_input("City")
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
                    prompt = f"Write a 2-line business email to {item['title']}. Context: {item.get('snippet','')}"
                    chat = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
                    pitch = chat.choices[0].message.content
                    if email_addr and send_email(email_addr, "Business Inquiry", pitch):
                        st.success("Email sent!")
                        st.write(pitch)
