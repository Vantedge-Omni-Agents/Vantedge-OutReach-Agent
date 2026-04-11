import streamlit as st
import pandas as pd
import requests
import re
import smtplib
from email.mime.text import MIMEText
from groq import Groq

# --- 1. CONFIG ---
st.set_page_config(page_title="Vantedge Pro", layout="wide")
st.title("Vantedge Pro: Lead Hunter & AI Pitcher 🚀")

# --- 2. SECURE API SETUP ---
def get_ai_client():
    try:
        return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except:
        st.error("GROQ_API_KEY missing in Streamlit Secrets!")
        return None

# --- 3. ENGINE (Anti-Duplicate & Deep Scan) ---
def get_leads(niche, city):
    headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
    # Hum specific queries use kar rahe hain taake direct business websites milen
    payload = {"q": f'"{niche}" {city} -site:clutch.co -site:linkedin.com', "num": 50}
    try:
        res = requests.post("https://google.serper.dev/search", headers=headers, json=payload).json()
        return res.get("organic", [])
    except:
        return []

def scrape_email(url):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        # Deep email extraction regex
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text)
        # Removing kachra (images, junk domains)
        valid = [e.lower() for e in set(emails) if not any(x in e.lower() for x in ['png', 'jpg', 'wix', 'sentry'])]
        return valid[0] if valid else None
    except:
        return None

# --- 4. INTERFACE ---
tab1, tab2 = st.tabs(["🔍 Lead Hunter", "✉️ AI Pitcher"])

with tab1:
    c1, c2 = st.columns(2)
    n_in = c1.text_input("Target Niche", "Marketing Agency")
    c_in = c2.text_input("Target City", "Dubai")
    
    if st.button("Hunt Unique Leads"):
        with st.spinner("Hunting direct clients..."):
            raw_data = get_leads(n_in, c_in)
            leads = []
            seen_links = set() # ANTI-DUPLICATION
            
            p_bar = st.progress(0)
            for i, item in enumerate(raw_data):
                link = item['link']
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
                st.warning("No direct business emails found. Try a different city.")

with tab2:
    if 'leads' in st.session_state and st.session_state.leads:
        client = get_ai_client()
        user_pitch_prompt = st.text_area("What's your offer?", "Help them get more clients via AI automation.")
        
        for i, lead in enumerate(st.session_state.leads):
            with st.expander(f"Draft for: {lead['Business']}"):
                if st.button(f"Generate AI Pitch", key=f"g_{i}"):
                    prompt = f"Write a short, professional cold email to {lead['Business']} about {user_pitch_prompt}. Site: {lead['Website']}"
                    if client:
                        resp = client.chat.completions.create(messages=[{"role":"user","content":prompt}], model="llama3-8b-8192")
                        st.session_state[f"msg_{i}"] = resp.choices[0].message.content
                
                # Editable Box
                final_text = st.text_area("Edit your pitch:", value=st.session_state.get(f"msg_{i}", ""), height=200, key=f"e_{i}")
                
                if st.button(f"Send to {lead['Email']}", key=f"s_{i}"):
                    try:
                        server = smtplib.SMTP("smtp.gmail.com", 587)
                        server.starttls()
                        server.login(st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASSWORD"])
                        msg = MIMEText(final_text)
                        msg['Subject'] = "Collaboration Proposal"
                        msg['From'] = st.secrets["GMAIL_USER"]
                        msg['To'] = lead['Email']
                        server.sendmail(st.secrets["GMAIL_USER"], lead['Email'], msg.as_string())
                        server.quit()
                        st.success("Sent Successfully!")
                    except Exception as e:
                        st.error(f"Gmail Error (Check App Password): {e}")
    else:
        st.info("Pehle leads hunt karein.")
