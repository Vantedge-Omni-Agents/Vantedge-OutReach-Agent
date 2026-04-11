import streamlit as st
import pandas as pd
import requests
import re
import smtplib
from email.mime.text import MIMEText
from groq import Groq

# --- 1. CONFIG ---
st.set_page_config(page_title="Vantedge Pro", layout="wide")
st.title("Vantedge Pro: Hunter & AI Pitcher 🚀")

# Groq Setup safely
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("GROQ_API_KEY missing in secrets!")

# --- 2. THE ENGINE ---
def get_leads(niche, city):
    headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
    payload = {"q": f"{niche} in {city} email contact", "num": 40}
    try:
        res = requests.post("https://google.serper.dev/search", headers=headers, json=payload).json()
        return res.get("organic", [])
    except:
        return []

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
    n_in = c1.text_input("Niche", "Real Estate")
    c_in = c2.text_input("City", "Dubai")
    
    if st.button("Hunt Unique Leads"):
        with st.spinner("Searching..."):
            raw_data = get_leads(n_in, c_in)
            leads = []
            seen_links = set() # ANTI-DUPLICATION
            
            p_bar = st.progress(0)
            for i, item in enumerate(raw_data):
                link = item['link']
                # Link duplication check
                if link not in seen_links:
                    email = scrape_email(link)
                    if email:
                        leads.append({"Business": item['title'], "Website": link, "Email": email})
                        seen_links.add(link)
                p_bar.progress((i + 1) / len(raw_data))
            
            st.session_state.leads = leads
            if leads:
                st.success(f"Found {len(leads)} Unique Leads!")
                st.table(pd.DataFrame(leads))
            else:
                st.warning("No emails found. Try a broader term like 'Agencies' or 'Services'.")

with tab2:
    if 'leads' in st.session_state and st.session_state.leads:
        selling = st.text_area("What are you offering?", "Lead generation and AI automation")
        
        for i, lead in enumerate(st.session_state.leads):
            with st.expander(f"Pitch: {lead['Business']}"):
                if st.button(f"Generate Pitch", key=f"g_{i}"):
                    prompt = f"Write a short cold email to {lead['Business']} selling {selling}. Site: {lead['Website']}"
                    resp = client.chat.completions.create(messages=[{"role":"user","content":prompt}], model="llama3-8b-8192")
                    st.session_state[f"msg_{i}"] = resp.choices[0].message.content
                
                # Editable Text
                final_msg = st.text_area("Edit text:", value=st.session_state.get(f"msg_{i}", ""), height=150, key=f"e_{i}")
                
                if st.button(f"Send Email", key=f"s_{i}"):
                    try:
                        server = smtplib.SMTP("smtp.gmail.com", 587)
                        server.starttls()
                        server.login(st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASSWORD"])
                        msg = MIMEText(final_msg)
                        msg['Subject'] = "Business Inquiry"
                        msg['From'] = st.secrets["GMAIL_USER"]
                        msg['To'] = lead['Email']
                        server.sendmail(st.secrets["GMAIL_USER"], lead['Email'], msg.as_string())
                        server.quit()
                        st.success("Sent!")
                    except Exception as e:
                        st.error(f"Gmail Error: {e}")
    else:
        st.info("Pehle leads nikalein.")
