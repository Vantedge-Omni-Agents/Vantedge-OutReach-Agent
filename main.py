import streamlit as st
import pandas as pd
import requests
import json
import smtplib
from email.mime.text import MIMEText
from groq import Groq

# --- 1. SETUP & SECRETS ---
st.set_page_config(page_title="Vantedge Intelligence OS", layout="wide", page_icon="🚀")

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    SERPER_API_KEY = st.secrets["SERPER_API_KEY"]
    GMAIL_USER = st.secrets["GMAIL_USER"]
    GMAIL_PASSWORD = st.secrets["GMAIL_PASSWORD"]
except Exception as e:
    st.error("⚠️ API Keys ya Gmail Secrets missing hain! Streamlit settings check karein.")
    st.stop()

client_groq = Groq(api_key=GROQ_API_KEY)

# --- 2. CORE FUNCTIONS ---

def send_gmail_outreach(to_email, subject, body):
    """Seedha aapke Gmail account se email bhejta hai"""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = f"Salman (Vantedge) <{GMAIL_USER}>"
    msg['To'] = to_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Gmail Send Error: {e}")
        return False

def get_leads(niche, location):
    """High-quality leads fetch karne ke liye"""
    url = "https://google.serper.dev/search"
    query = f"{niche} companies in {location} contact email"
    payload = json.dumps({"q": query, "num": 10})
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    
    res = requests.post(url, headers=headers, data=payload).json()
    return res.get("organic", [])

def generate_pitch(target, context):
    """Groq AI se personalized message generate karna"""
    model = "llama-3.3-70b-versatile"
    prompt = f"Write a professional 2-line intro email to {target}. Pitch Horbex Digital's marketing services. Context: {context}"
    
    try:
        chat = client_groq.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model
        )
        return chat.choices[0].message.content
    except Exception as e:
        return f"AI Error: {e}"

# --- 3. MAIN UI ---
st.title("Vantedge Intelligence Pro 🚀")
st.caption("Direct Gmail Integration | AI-Driven Outreach")

tab1, tab2 = st.tabs(["🔍 Lead Hunter", "📧 AI Outreach"])

with tab1:
    c1, c2 = st.columns(2)
    niche = c1.text_input("Business Niche")
    loc = c2.text_input("Location")
    
    if st.button("Start Extraction"):
        with st.spinner("Finding leads..."):
            leads = get_leads(niche, loc)
            st.session_state.leads = leads
            st.success(f"Found {len(leads)} leads!")
            st.table(pd.DataFrame(leads)[['title', 'link']])

with tab2:
    if 'leads' in st.session_state:
        for i, lead in enumerate(st.session_state.leads):
            with st.expander(f"Lead: {lead['title']}"):
                # Manual Email Input (kyunke Serper hamesha email nahi deta)
                target_email = st.text_input(f"Recipient Email for {lead['title']}", key=f"email_{i}")
                
                if st.button(f"Draft AI Pitch", key=f"draft_{i}"):
                    pitch = generate_pitch(lead['title'], lead.get('snippet', ''))
                    st.session_state[f"p_{i}"] = pitch
                    st.info(pitch)
                
                if f"p_{i}" in st.session_state:
                    if st.button(f"Send via My Gmail", key=f"send_{i}"):
                        if target_email:
                            if send_gmail_outreach(target_email, "Business Collaboration", st.session_state[f"p_{i}"]):
                                st.success("🚀 Email sent! Check your Gmail Sent folder.")
                        else:
                            st.warning("Pehle recipient ka email address likhein.")
    else:
        st.info("Pehle 'Lead Hunter' tab mein leads nikalen.")
