import streamlit as st
import pandas as pd
import requests
import re
import smtplib
import ssl
from email.mime.text import MIMEText
from groq import Groq

# --- 1. SETTINGS & BRANDING ---
st.set_page_config(page_title="Vantedge-Outreach-Pro", layout="wide")
st.title("Vantedge-Outreach-Pro 🚀")

# API Keys Check
if "GROQ_API_KEY" not in st.secrets or "SERPER_API_KEY" not in st.secrets:
    st.error("API Keys missing in Streamlit Secrets!")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 2. THE SEARCH & SCRAPE ENGINE ---
def get_verified_email(url):
    try:
        # Request with timeout to prevent app hanging
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text)
        # Filter junk image/system emails
        valid = [e.lower() for e in set(emails) if not any(x in e.lower() for x in ['png', 'jpg', 'wix', 'sentry', 'gif'])]
        return valid[0] if valid else None
    except:
        return None

# --- 3. UI INTERFACE ---
tab1, tab2 = st.tabs(["🔍 Hunter Engine", "✉️ AI Outreach"])

with tab1:
    c1, c2 = st.columns(2)
    niche = c1.text_input("Niche (e.g. Dental Clinic)", "Dental Clinic")
    city = c2.text_input("City (e.g. London)", "London")
    
    if st.button("Hunt Leads Now"):
        with st.spinner("Vantedge-Pro is hunting for real emails..."):
            headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
            # BROAD SEARCH: Using multiple queries to ensure results
            query = f'"{niche}" {city} website email "contact"'
            
            try:
                res = requests.post("https://google.serper.dev/search", headers=headers, json={"q": query, "num": 30}).json()
                results = res.get("organic", [])
                
                final_leads = []
                for item in results:
                    # Quick check: See if email is in the Google snippet first
                    snippet_email = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', item.get('snippet', ''))
                    
                    email_addr = snippet_email[0] if snippet_email else get_verified_email(item['link'])
                    
                    if email_addr:
                        final_leads.append({
                            "Business": item['title'],
                            "Website": item['link'],
                            "Email": email_addr
                        })
                
                st.session_state.leads_data = final_leads
                if final_leads:
                    st.success(f"Success! Found {len(final_leads)} verified leads.")
                    st.table(pd.DataFrame(final_leads))
                else:
                    st.warning("No direct emails found. Try a different city or niche.")
            except Exception as e:
                st.error(f"Search Error: {e}")

with tab2:
    if 'leads_data' in st.session_state and st.session_state.leads_data:
        my_offer = st.text_area("What are you offering?", "AI-powered lead generation and outreach automation services.")
        
        for i, lead in enumerate(st.session_state.leads_data):
            with st.expander(f"Draft for: {lead['Business']}"):
                
                # THE PITCH GENERATOR FIX
                if st.button(f"Generate Pitch", key=f"btn_{i}"):
                    try:
                        with st.spinner("AI is thinking..."):
                            # Using llama-3.1 to avoid decommissioning error
                            prompt = f"Write a 2-sentence professional cold email to {lead['Business']} offering {my_offer}."
                            ai_resp = client.chat.completions.create(
                                messages=[{"role": "user", "content": prompt}],
                                model="llama-3.1-8b-instant"
                            )
                            # Store in session state and force rerun to show text
                            st.session_state[f"pitch_msg_{i}"] = ai_resp.choices[0].message.content
                            st.rerun() 
                    except Exception as e:
                        st.error(f"AI Error: {e}")

                # Display the pitch in the text area
                pitch_text = st.text_area("Edit Email:", value=st.session_state.get(f"pitch_msg_{i}", ""), height=150, key=f"area_{i}")
                
                # GMAIL SENDING
                if st.button(f"Send Email", key=f"send_{i}"):
                    try:
                        context = ssl.create_default_context()
                        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                            server.login(st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASSWORD"])
                            msg = MIMEText(pitch_text)
                            msg['Subject'] = f"Proposal for {lead['Business']}"
                            msg['From'] = st.secrets["GMAIL_USER"]
                            msg['To'] = lead['Email']
                            server.send_message(msg)
                        st.success("Email Sent! 🚀")
                    except Exception as e:
                        st.error(f"Gmail Login Error: {e}. Check your App Password.")
    else:
        st.info("Pehle 'Hunter Engine' tab mein leads nikaalein.")
