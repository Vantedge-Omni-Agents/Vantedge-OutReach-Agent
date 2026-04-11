import streamlit as st
import pandas as pd
import requests
import re
import smtplib
import ssl
from email.mime.text import MIMEText
from groq import Groq

# --- 1. SETTINGS ---
st.set_page_config(page_title="Vantedge-Outreach-Pro", layout="wide")
st.title("Vantedge-Outreach-Pro 🚀")

# Ensure Secrets are present
if "GROQ_API_KEY" not in st.secrets or "SERPER_API_KEY" not in st.secrets:
    st.error("API Keys missing! Check your Secrets tab.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 2. ENGINE ---
def get_email(url):
    try:
        # Added a custom header and longer timeout to bypass blockers
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text)
        # Filter junk results
        clean = [e.lower() for e in set(emails) if not any(x in e.lower() for x in ['png', 'jpg', 'wix', 'sentry', 'gif', 'image'])]
        return clean[0] if clean else None
    except:
        return None

# --- 3. UI TABS ---
tab1, tab2 = st.tabs(["🔍 Lead Hunter", "✉️ AI Pitcher"])

with tab1:
    col1, col2 = st.columns(2)
    niche = col1.text_input("Niche", "Dental Clinic")
    city = col2.text_input("City", "London")
    
    if st.button("Hunt Verified Leads"):
        with st.spinner("Vantedge-Pro is searching deep..."):
            headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
            # Query for more specific landing pages
            query = f'"{niche}" {city} website email "contact us"'
            
            try:
                res = requests.post("https://google.serper.dev/search", headers=headers, json={"q": query, "num": 20}).json()
                results = res.get("organic", [])
                
                final_leads = []
                for item in results:
                    # Check for email in snippet first (instant lead!)
                    snippet_email = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', item.get('snippet', ''))
                    
                    email = snippet_email[0] if snippet_email else get_email(item['link'])
                    
                    if email:
                        final_leads.append({"Business": item['title'], "Website": item['link'], "Email": email})
                
                st.session_state.leads_data = final_leads
                if final_leads:
                    st.success(f"Found {len(final_leads)} leads!")
                    st.table(pd.DataFrame(final_leads))
                else:
                    st.error("No emails found. Try a broader location like 'United Kingdom'.")
            except Exception as e:
                st.error(f"Search failed: {e}")

with tab2:
    if 'leads_data' in st.session_state and st.session_state.leads_data:
        offer = st.text_area("Your Business Offer", "AI lead generation and outreach automation.")
        
        for i, lead in enumerate(st.session_state.leads_data):
            with st.expander(f"Pitch for: {lead['Business']}"):
                
                if st.button(f"Generate Pitch", key=f"gen_{i}"):
                    try:
                        # Using llama-3.1 model
                        prompt = f"Write a professional 2-sentence cold email to {lead['Business']} offering {offer}."
                        resp = client.chat.completions.create(
                            messages=[{"role": "user", "content": prompt}],
                            model="llama-3.1-8b-instant"
                        )
                        st.session_state[f"msg_{i}"] = resp.choices[0].message.content
                        st.rerun() # Refresh to show text
                    except Exception as e:
                        st.error(f"AI Error: {e}")

                draft = st.text_area("Edit Email:", value=st.session_state.get(f"msg_{i}", ""), key=f"edit_{i}")
                
                if st.button(f"Send to {lead['Email']}", key=f"send_{i}"):
                    try:
                        context = ssl.create_default_context()
                        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                            server.login(st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASSWORD"])
                            msg = MIMEText(draft)
                            msg['Subject'] = "Inquiry"
                            msg['From'] = st.secrets["GMAIL_USER"]
                            msg['To'] = lead['Email']
                            server.send_message(msg)
                        st.success("Sent!")
                    except Exception as e:
                        st.error(f"Gmail Error: {e}. Use App Password!")
    else:
        st.info("First Fetch Leads to Use Auto-Pitch Function")
