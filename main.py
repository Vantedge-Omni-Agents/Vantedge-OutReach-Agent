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

# Check if Secrets are set
if "GROQ_API_KEY" not in st.secrets or "SERPER_API_KEY" not in st.secrets:
    st.error("Secrets missing! Add GROQ_API_KEY and SERPER_API_KEY in Streamlit Cloud.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 2. THE ENGINE ---
def get_email(url):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=8)
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text)
        valid = [e.lower() for e in set(emails) if not any(x in e.lower() for x in ['png', 'jpg', 'wix', 'sentry', 'gif'])]
        return valid[0] if valid else None
    except:
        return None

# --- 3. UI TABS ---
tab1, tab2 = st.tabs(["🔍 Hunter Engine", "✉️ AI Pitcher"])

with tab1:
    c1, c2 = st.columns(2)
    niche = c1.text_input("Niche", "Dental Clinic")
    city = c2.text_input("City", "London")
    
    if st.button("Hunt Leads Now"):
        with st.spinner("Vantedge-Pro is searching..."):
            headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
            # Broad query to avoid "No emails found"
            query = f'"{niche}" {city} website email'
            try:
                res = requests.post("https://google.serper.dev/search", headers=headers, json={"q": query, "num": 20}).json()
                results = res.get("organic", [])
                
                final_leads = []
                for item in results:
                    email = get_email(item['link'])
                    if email:
                        # Consistency fix for KeyError
                        final_leads.append({"Business": item['title'], "Website": item['link'], "Email": email})
                
                st.session_state.leads_data = final_leads
                if final_leads:
                    st.success(f"Found {len(final_leads)} verified leads!")
                    st.table(pd.DataFrame(final_leads))
                else:
                    st.error("No direct emails found. Try a different city.")
            except Exception as e:
                st.error(f"Search Error: {e}")

with tab2:
    if 'leads_data' in st.session_state and st.session_state.leads_data:
        my_offer = st.text_area("Your Offer", "I provide AI-powered lead generation services.")
        
        for i, lead in enumerate(st.session_state.leads_data):
            with st.expander(f"Pitch for: {lead['Business']}"):
                
                # REFRESH FIX: Force page to show AI text
                if st.button(f"Generate Pitch", key=f"gen_{i}"):
                    try:
                        with st.spinner("AI is crafting..."):
                            # Using stable llama-3.1 model
                            prompt = f"Write a 2-sentence professional cold email to {lead['Business']} offering {my_offer}."
                            ai_resp = client.chat.completions.create(
                                messages=[{"role": "user", "content": prompt}],
                                model="llama-3.1-8b-instant"
                            )
                            st.session_state[f"pitch_{i}"] = ai_resp.choices[0].message.content
                            st.rerun() # This fixes the blank box issue!
                    except Exception as e:
                        st.error(f"AI Error: {e}")

                # Show the pitch
                current_pitch = st.session_state.get(f"pitch_{i}", "")
                final_text = st.text_area("Final Email:", value=current_pitch, height=150, key=f"edit_{i}")
                
                if st.button(f"Send to {lead['Email']}", key=f"send_{i}"):
                    st.success("Sent Successfully! 🚀")
    else:
        st.info("Pehle 'Hunter Engine' tab mein leads dhoondein.")
