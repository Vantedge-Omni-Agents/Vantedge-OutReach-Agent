import streamlit as st
import pandas as pd
import requests
import re
import smtplib
from email.mime.text import MIMEText
from groq import Groq

# --- 1. CONFIG & SAFETY ---
st.set_page_config(page_title="Vantedge Pro", layout="wide")
st.title("Vantedge Pro: Lead Hunter & AI Pitcher 🚀")

# API Keys Check
groq_key = st.secrets.get("GROQ_API_KEY")
serper_key = st.secrets.get("SERPER_API_KEY")

if not groq_key or not serper_key:
    st.error("Secrets mein API Keys missing hain! Pehle 'Manage App' -> 'Secrets' mein keys check karein.")
    st.stop()

client = Groq(api_key=groq_key)

# --- 2. THE ENGINE ---
def scrape_email(url):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text)
        # Filter junk like images/wix
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
            payload = {"q": f'"{n_in}" {c_in} website -site:clutch.co -site:linkedin.com', "num": 40}
            
            try:
                res = requests.post("https://google.serper.dev/search", headers=headers, json=payload).json()
                results = res.get("organic", [])
                
                leads = []
                seen_links = set() # ANTI-DUPLICATION
                
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
                    st.warning("No direct emails found. Niche ya City thori change karke dekhein.")
            except Exception as e:
                st.error(f"Search Error: {e}")

with tab2:
    if 'leads' in st.session_state and st.session_state.leads:
        selling_point = st.text_area("What are you selling?", "Lead generation and automation services.")
        
        for i, lead in enumerate(st.session_state.leads):
            with st.expander(f"Pitch: {lead['Business']}"):
                # AI generation with Error Handling
                if st.button(f"Generate Pitch", key=f"g_{i}"):
                    try:
                        prompt = f"Write a short cold email to {lead['Business']} selling {selling_point}. Website: {lead['Website']}"
                        resp = client.chat.completions.create(messages=[{"role":"user","content":prompt}], model="llama3-8b-8192")
                        st.session_state[f"msg_{i}"] = resp.choices[0].message.content
                    except Exception as e:
                        st.error(f"AI Error: {e}. Shayad API key block hai.")

                # Editable Pitch
                final_msg = st.text_area("Edit text:", value=st.session_state.get(f"msg_{i}", ""), height=150, key=f"e_{i}")
                
                if st.button(f"Send Email", key=f"s_{i}"):
                    try:
                        server = smtplib.SMTP("smtp.gmail.com", 587)
                        server.starttls()
                        server.login(st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASSWORD"])
                        msg = MIMEText(final_msg)
                        msg['Subject'] = "Business Proposal"
                        msg['From'] = st.secrets["GMAIL_USER"]
                        msg['To'] = lead['Email']
                        server.sendmail(st.secrets["GMAIL_USER"], lead['Email'], msg.as_string())
                        server.quit()
                        st.success("Sent!")
                    except Exception as e:
                        st.error(f"Gmail Login Error: {e}. App Password update karein!")
    else:
        st.info("Pehle 'Lead Hunter' tab mein ja kar leads nikalein.")
