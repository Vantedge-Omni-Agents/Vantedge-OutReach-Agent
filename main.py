import streamlit as st
import pandas as pd
import requests
import re
import smtplib
import ssl
from email.mime.text import MIMEText
from groq import Groq

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="Vantedge Pro", layout="wide")
st.title("Vantedge Pro: Hunter & AI Pitcher 🚀")

# API Keys Check
groq_key = st.secrets.get("GROQ_API_KEY")
serper_key = st.secrets.get("SERPER_API_KEY")

if not groq_key or not serper_key:
    st.error("Secrets missing! Please check your Streamlit settings.")
    st.stop()

client = Groq(api_key=groq_key)

# --- 2. THE SEARCH ENGINE ---
def scrape_email(url):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text)
        valid = [e.lower() for e in set(emails) if not any(x in e.lower() for x in ['png', 'jpg', 'wix', 'sentry'])]
        return valid[0] if valid else None
    except:
        return None

# --- 3. UI TABS ---
tab1, tab2 = st.tabs(["🔍 Lead Hunter", "✉️ AI Pitcher"])

with tab1:
    c1, c2 = st.columns(2)
    n_in = c1.text_input("Niche", "Real Estate Agency")
    c_in = c2.text_input("City", "Dubai")
    
    if st.button("Hunt Unique Leads"):
        with st.spinner("Hunting..."):
            headers = {'X-API-KEY': serper_key, 'Content-Type': 'application/json'}
            payload = {"q": f'"{n_in}" {c_in} website -site:clutch.co', "num": 40}
            
            try:
                res = requests.post("https://google.serper.dev/search", headers=headers, json=payload).json()
                results = res.get("organic", [])
                leads = []
                seen_links = set() 
                
                p_bar = st.progress(0)
                for i, item in enumerate(results):
                    link = item['link']
                    if link not in seen_links:
                        email = scrape_email(link)
                        if email:
                            leads.append({"Business": item['title'], "Website": link, "Email": email})
                            seen_links.add(link)
                    p_bar.progress((i + 1) / len(results))
                
                st.session_state.leads = leads
                if leads:
                    st.success(f"Found {len(leads)} Unique Leads!")
                    st.table(pd.DataFrame(leads))
                else:
                    st.warning("No emails found.")
            except Exception as e:
                st.error(f"Search Error: {e}")

with tab2:
    if 'leads' in st.session_state and st.session_state.leads:
        selling_point = st.text_area("What are you offering?", "AI Automation & Lead Generation")
        
        for i, lead in enumerate(st.session_state.leads):
            with st.expander(f"Pitch: {lead['Business']}"):
                # FIXED: Using latest model 'llama-3.3-70b-versatile'
                if st.button(f"Generate AI Pitch", key=f"g_{i}"):
                    try:
                        prompt = f"Write a short cold email to {lead['Business']} selling {selling_point}. Site: {lead['Website']}"
                        resp = client.chat.completions.create(
                            messages=[{"role":"user","content":prompt}], 
                            model="llama-3.3-70b-versatile" # YEH MODEL BILKUL LATEST HAI
                        )
                        st.session_state[f"msg_{i}"] = resp.choices[0].message.content
                    except Exception as e:
                        st.error(f"AI Error: {e}")

                final_msg = st.text_area("Edit text:", value=st.session_state.get(f"msg_{i}", ""), height=150, key=f"e_{i}")
                
                if st.button(f"Send Email", key=f"s_{i}"):
                    try:
                        # FIXED: Added SSL Context for safer login
                        context = ssl.create_default_context()
                        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                            server.login(st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASSWORD"])
                            msg = MIMEText(final_msg)
                            msg['Subject'] = f"Proposal for {lead['Business']}"
                            msg['From'] = st.secrets["GMAIL_USER"]
                            msg['To'] = lead['Email']
                            server.send_message(msg)
                        st.success("Sent!")
                    except Exception as e:
                        st.error(f"Gmail Login Error: {e}. App Password check karein!")
    else:
        st.info("Pehle leads hunt karein.")
