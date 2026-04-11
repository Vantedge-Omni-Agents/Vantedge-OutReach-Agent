import streamlit as st
import pandas as pd
import requests
import re
import smtplib
import ssl
from email.mime.text import MIMEText
from groq import Groq

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Vantedge-Outreach-Pro", layout="wide")
st.title("Vantedge-Outreach-Pro 🚀")

# API Keys Check
if "GROQ_API_KEY" not in st.secrets or "SERPER_API_KEY" not in st.secrets:
    st.error("API Keys missing in Secrets!")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 2. ENGINES ---
def extract_emails(url):
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=8)
        found = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', response.text)
        valid = [e.lower() for e in set(found) if not any(x in e.lower() for x in ['png', 'jpg', 'wix', 'sentry'])]
        return valid[0] if valid else None
    except:
        return None

# --- 3. TABS ---
tab1, tab2 = st.tabs(["🔍 Lead Hunter", "✉️ AI Pitcher"])

with tab1:
    c1, c2 = st.columns(2)
    niche = c1.text_input("Niche", "Real Estate Agency")
    city = c2.text_input("City", "London")
    
    if st.button("Hunt Verified Leads"):
        with st.spinner("Vantedge-Pro is hunting..."):
            headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
            query = f'"{niche}" {city} website "email"'
            res = requests.post("https://google.serper.dev/search", headers=headers, json={"q": query, "num": 25}).json()
            
            leads = []
            for item in res.get("organic", []):
                email = extract_emails(item['link'])
                if email:
                    # KEY FIX: Using 'Business' consistently
                    leads.append({"Business": item['title'], "Website": item['link'], "Email": email})
            
            st.session_state.leads_data = leads
            if leads:
                st.success(f"Found {len(leads)} Leads!")
                st.table(pd.DataFrame(leads))
            else:
                st.warning("No direct emails found. Try 'New York' or 'London'.")

with tab2:
    if 'leads_data' in st.session_state and st.session_state.leads_data:
        my_offer = st.text_area("Your Business Offer", "I provide high-quality lead generation and AI automation.")
        
        for i, lead in enumerate(st.session_state.leads_data):
            # KEY FIX: Column names match now
            with st.expander(f"Pitch for: {lead['Business']}"):
                
                if st.button(f"Generate AI Pitch", key=f"gen_{i}"):
                    try:
                        with st.spinner("AI is crafting..."):
                            # Using stable llama-3.1 model
                            prompt = f"Write a 2-sentence professional cold email to {lead['Business']} offering {my_offer}."
                            ai_resp = client.chat.completions.create(
                                messages=[{"role": "user", "content": prompt}],
                                model="llama-3.1-8b-instant"
                            )
                            st.session_state[f"pitch_{i}"] = ai_resp.choices[0].message.content
                            st.rerun()
                    except Exception as e:
                        st.error(f"AI Error: {e}")

                final_pitch = st.text_area("Email Draft:", value=st.session_state.get(f"pitch_{i}", ""), height=150, key=f"edit_{i}")
                
                if st.button(f"Send Email", key=f"send_{i}"):
                    try:
                        context = ssl.create_default_context()
                        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                            server.login(st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASSWORD"])
                            msg = MIMEText(final_pitch)
                            msg['Subject'] = f"Proposal for {lead['Business']}"
                            msg['From'] = st.secrets["GMAIL_USER"]
                            msg['To'] = lead['Email']
                            server.send_message(msg)
                        st.success("Sent Successfully! 🚀")
                    except Exception as e:
                        st.error(f"Gmail Login Error: {e}")
    else:
        st.info("Pehle 'Lead Hunter' tab mein leads dhoondein.")
