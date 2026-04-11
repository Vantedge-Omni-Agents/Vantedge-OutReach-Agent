import streamlit as st
import pandas as pd
import requests
import json
import smtplib
from email.mime.text import MIMEText
from groq import Groq

# --- 1. CONFIG & LOGO LINKS ---
# GitHub ke 'Raw' links
DARK_THEME_LOGO = "https://raw.githubusercontent.com/Vantedge-Omni-Agents/Vantedge-OutReach-Agent/main/logo.png"
LIGHT_THEME_LOGO = "https://raw.githubusercontent.com/Vantedge-Omni-Agents/Vantedge-OutReach-Agent/main/black%20logo.png"

# Taskbar Setup (Sabse upar hona lazmi hai)
st.set_page_config(
    page_title="Vantedge-OutReach-Agent",
    page_icon=DARK_THEME_LOGO,
    layout="wide"
)

# --- 2. 100% DYNAMIC CSS LOGO ---
# Ye browser theme switch hote hi logo badal dega
st.markdown(
    f"""
    <style>
    [data-testid="stSidebarNav"]::before {{
        content: "";
        display: block;
        background-image: url("{DARK_THEME_LOGO}");
        background-size: contain;
        background-repeat: no-repeat;
        height: 80px;
        width: 120px;
        margin: 20px auto;
    }}
    @media (prefers-color-scheme: light) {{
        [data-testid="stSidebarNav"]::before {{
            background-image: url("{LIGHT_THEME_LOGO}");
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True
)

st.sidebar.title("Vantedge Control")

# --- 3. API SECRETS HANDLING (FIXING THE ERROR) ---
try:
    # Hum variables ko direct load kar rahe hain taake NameError na aaye
    SERPER_KEY = st.secrets["SERPER_API_KEY"]
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
    GMAIL_USER = st.secrets["GMAIL_USER"]
    GMAIL_PASS = st.secrets["GMAIL_PASSWORD"]
except Exception as e:
    st.error(f"⚠️ Secrets Error: {e}. Please check your Streamlit Cloud Secrets.")
    st.stop()

client_groq = Groq(api_key=GROQ_KEY)

# --- 4. CORE FUNCTIONS ---
def send_email(target, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = f"Vantedge Agent <{GMAIL_USER}>"
    msg['To'] = target
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.sendmail(GMAIL_USER, target, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Gmail Error: {e}")
        return False

# --- 5. MAIN UI ---
st.title("Vantedge-OutReach-Intelligence 🚀")
tabs = st.tabs(["Lead Hunter", "AI Outreach"])

with tabs[0]:
    c1, c2 = st.columns(2)
    niche = c1.text_input("Target Niche")
    city = c2.text_input("Target City")
    
    if st.button("Start Extraction"):
        with st.spinner("Searching..."):
            url = "https://google.serper.dev/search"
            headers = {
                'X-API-KEY': SERPER_KEY, # FIX: Yahan ab error nahi aayega
                'Content-Type': 'application/json'
            }
            query = f"{niche} in {city} contact email"
            payload = json.dumps({"q": query, "num": 10})
            
            response = requests.post(url, headers=headers, data=payload).json()
            if "organic" in response:
                st.session_state.leads = response["organic"]
                st.table(pd.DataFrame(response["organic"])[['title', 'link']])
            else:
                st.error("No leads found. Check API quota.")

with tabs[1]:
    if 'leads' in st.session_state:
        for i, lead in enumerate(st.session_state.leads):
            with st.expander(f"Lead: {lead['title']}"):
                email = st.text_input("Email", key=f"mail_{i}")
                if st.button("Send AI Pitch", key=f"btn_{i}"):
                    prompt = f"Write a 2-line intro to {lead['title']}. Context: {lead.get('snippet','')}"
                    chat = client_groq.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama-3.3-70b-versatile"
                    )
                    pitch = chat.choices[0].message.content
                    if email and send_email(email, "Collaboration Inquiry", pitch):
                        st.success("✅ Sent!")
    else:
        st.info("Pehle leads nikalen.")
