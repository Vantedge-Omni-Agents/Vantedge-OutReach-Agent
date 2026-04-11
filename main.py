import streamlit as st
import pandas as pd
import requests
import json
import smtplib
from email.mime.text import MIMEText
from groq import Groq

# --- 1. LOGO LINKS ---
# GitHub 'Raw' Links
WHITE_LOGO = "https://raw.githubusercontent.com/Vantedge-Omni-Agents/Vantedge-OutReach-Agent/main/logo.png"
BLACK_LOGO = "https://raw.githubusercontent.com/Vantedge-Omni-Agents/Vantedge-OutReach-Agent/main/black%20logo.png"

# --- 2. THEME DETECTION & TASKBAR ---
st.set_page_config(
    page_title="Vantedge-OutReach-Intelligence",
    page_icon=WHITE_LOGO,
    layout="wide"
)

# Robust Logo Logic: Sidebar ke top par hamesha dikhega
def display_logo():
    # Streamlit theme sensing hack
    is_dark = st.get_option("theme.base") == "dark"
    logo_url = WHITE_LOGO if is_dark else BLACK_LOGO
    st.sidebar.image(logo_url, use_container_width=True)

display_logo()
st.sidebar.title("Vantedge Control")

# --- 3. SECRETS LOADING ---
try:
    SERPER_KEY = st.secrets["SERPER_API_KEY"]
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
    GMAIL_USER = st.secrets["GMAIL_USER"]
    GMAIL_PASS = st.secrets["GMAIL_PASSWORD"]
except Exception as e:
    st.error(f"Secrets missing: {e}")
    st.stop()

client = Groq(api_key=GROQ_KEY)

# --- 4. GMAIL SMTP (Error Fix) ---
def send_email(target, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = f"Vantedge Agent <{GMAIL_USER}>"
    msg['To'] = target
    try:
        # Port 465 for SSL is more stable
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, target, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        # Ye error aapko video mein 'BadCredentials' dikha raha tha
        st.error(f"Gmail Error: Make sure you are using an 'App Password', not your main password!")
        return False

# --- 5. UI APP ---
st.title("Vantedge-OutReach-Intelligence 🚀")
tabs = st.tabs(["Lead Hunter", "AI Outreach"])

with tabs[0]:
    c1, c2 = st.columns(2)
    niche = c1.text_input("Niche")
    city = c2.text_input("City")
    if st.button("Start Extraction"):
        with st.spinner("Finding leads..."):
            url = "https://google.serper.dev/search"
            headers = {'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json'}
            query = f"{niche} in {city} contact email"
            res = requests.post(url, headers=headers, data=json.dumps({"q": query})).json()
            if "organic" in res:
                st.session_state.leads = res["organic"]
                st.table(pd.DataFrame(res["organic"])[['title', 'link']])

with tabs[1]:
    if 'leads' in st.session_state:
        for i, lead in enumerate(st.session_state.leads):
            with st.expander(f"Lead: {lead['title']}"):
                target_mail = st.text_input("Receiver Email", key=f"m_{i}")
                if st.button("Send AI Pitch", key=f"b_{i}"):
                    prompt = f"Write a 2-line business email to {lead['title']}."
                    pitch = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama-3.3-70b-versatile"
                    ).choices[0].message.content
                    if send_email(target_mail, "Business Inquiry", pitch):
                        st.success("Email sent!")
    else:
        st.info("Pehle leads search karein.")
