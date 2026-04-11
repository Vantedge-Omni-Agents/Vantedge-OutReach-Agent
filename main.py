import streamlit as st
import pandas as pd
import requests
import json
import smtplib
from email.mime.text import MIMEText
from groq import Groq

# --- 1. DYNAMIC BRANDING SETUP ---
# In links ko replace mat karna, ye GitHub ke 'Raw' links hain jo Streamlit handle kar sakta hai
DARK_LOGO = "https://raw.githubusercontent.com/Vantedge-Omni-Agents/Vantedge-OutReach-Agent/main/logo_light.png" # Safed logo (kaale background ke liye)
LIGHT_LOGO = "https://raw.githubusercontent.com/Vantedge-Omni-Agents/Vantedge-OutReach-Agent/main/logo_dark.png"  # Kaala logo (safed background ke liye)

# Browser Tab & Taskbar Setup
st.set_page_config(
    page_title="Vantedge-OutReach-Intelligence",
    page_icon="🚀",
    layout="wide"
)

# Theme detection logic
# Agar user ne Dark Mode rakha hai toh white logo dikhao, warna black
try:
    if st.get_option("theme.base") == "dark":
        logo_to_use = DARK_LOGO
    else:
        logo_to_use = LIGHT_LOGO
except:
    logo_to_use = DARK_LOGO # Fallback

# Sidebar mein Logo display
st.sidebar.image(logo_to_use, use_container_width=True)
st.sidebar.title("Vantedge-OutReach-Beta")

# --- 2. SECRETS & API SETUP ---
try:
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
    SERPER_KEY = st.secrets["SERPER_API_KEY"]
    MY_EMAIL = st.secrets["GMAIL_USER"]
    MY_PASS = st.secrets["GMAIL_PASSWORD"]
except Exception as e:
    st.error("Secrets missing! Check Streamlit Cloud Settings.")
    st.stop()

client = Groq(api_key=GROQ_KEY)

# --- 3. CORE LOGIC ---
def send_email(target, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = f"Vantedge Intelligence <{MY_EMAIL}>"
    msg['To'] = target
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(MY_EMAIL, MY_PASS)
            server.sendmail(MY_EMAIL, target, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Mail Error: {e}")
        return False

# --- 4. APP UI ---
st.title("Vantedge-OutReach-Intelligence 🚀")

tab1, tab2 = st.tabs(["Lead Hunter", "AI Outreach"])

with tab1:
    col1, col2 = st.columns(2)
    niche = col1.text_input("Niche", placeholder="e.g. Real Estate")
    city = col2.text_input("City", placeholder="e.g. Karachi")
    
    if st.button("Find Leads"):
        with st.spinner("Searching..."):
            query = f"{niche} companies in {city} email"
            url = "https://google.serper.dev/search"
            headers = {'X-API-KEY': SERPER_KEY, 'Content-Type': 'application/json'}
            data = json.dumps({"q": query, "num": 10})
            res = requests.post(url, headers=headers, data=data).json()
            
            if "organic" in res:
                st.session_state.leads = res["organic"]
                st.success(f"Found {len(res['organic'])} leads!")
                st.table(pd.DataFrame(res["organic"])[['title', 'link']])

with tab2:
    if 'leads' in st.session_state:
        for i, lead in enumerate(st.session_state.leads):
            with st.expander(f"Lead: {lead['title']}"):
                target_email = st.text_input("Email", key=f"email_{i}")
                if st.button("Generate & Send", key=f"btn_{i}"):
                    # AI Pitch
                    prompt = f"Write a 2-line pitch for {lead['title']}. Context: {lead.get('snippet','')}"
                    chat = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama-3.3-70b-versatile"
                    )
                    pitch = chat.choices[0].message.content
                    
                    if target_email and send_email(target_email, "Collaboration Inquiry", pitch):
                        st.success("✅ Email Sent Directly!")
                        st.info(pitch)
    else:
        st.info("Pehle Leads nikalen.")
