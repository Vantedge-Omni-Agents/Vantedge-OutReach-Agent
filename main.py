import streamlit as st
import pandas as pd
import requests
import re
import smtplib
import ssl
from email.mime.text import MIMEText
from groq import Groq

# --- 1. CONFIG ---
st.set_page_config(page_title="Vantedge Pro", layout="wide")
st.title("Vantedge Pro: Hunter & AI Pitcher 🚀")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def scrape_email(url):
    try:
        # Timeout barha diya taake heavy sites load ho sakain
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text)
        valid = [e.lower() for e in set(emails) if not any(x in e.lower() for x in ['png', 'jpg', 'wix', 'sentry', 'image'])]
        return valid[0] if valid else None
    except:
        return None

# --- 2. THE SMART SEARCH ENGINE ---
tab1, tab2 = st.tabs(["🔍 Smart Hunter", "✉️ AI Pitcher"])

with tab1:
    c1, c2 = st.columns(2)
    niche = c1.text_input("Niche", "Real Estate Agency")
    city = c2.text_input("City", "Dubai")
    
    if st.button("Hunt Leads (Aggressive Mode)"):
        with st.spinner("Searching multiple sources..."):
            headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
            
            # LEVEL 3 SEARCH: Multiple combinations to find emails
            # Ab ye directory sites ko bypass karke direct contact pages dhoondega
            queries = [
                f'"{niche}" {city} "email" site:.com',
                f'"{niche}" {city} "contact" website',
                f'"{niche}" in {city} "owner email"'
            ]
            
            all_leads = []
            seen_links = set()
            
            for q in queries:
                res = requests.post("https://google.serper.dev/search", headers=headers, json={"q": q, "num": 20}).json()
                results = res.get("organic", [])
                
                for item in results:
                    link = item['link']
                    if link not in seen_links:
                        # Direct check for email in snippet (fast mode)
                        email_in_snippet = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', item.get('snippet', ''))
                        
                        email = email_in_snippet[0] if email_in_snippet else scrape_email(link)
                        
                        if email:
                            all_leads.append({"Business": item['title'], "Website": link, "Email": email})
                            seen_links.add(link)

            st.session_state.leads = all_leads
            if all_leads:
                st.success(f"Mubarak! Found {len(all_leads)} leads without manual broadening.")
                st.table(pd.DataFrame(all_leads))
            else:
                st.error("Zero leads found. Check your API Key or try a different Country.")

# --- 3. THE AI PITCHER (LATEST MODEL) ---
with tab2:
    if 'leads' in st.session_state and st.session_state.leads:
        offer = st.text_area("Your Offer", "Lead generation and automation services.")
        for i, lead in enumerate(st.session_state.leads):
            with st.expander(f"Lead: {lead['Business']}"):
                # FIXED MODEL: llama-3.1-8b-instant
                if st.button(f"Generate Pitch", key=f"gen_{i}"):
                    try:
                        prompt = f"Write a 2-line professional cold email for {lead['Business']}."
                        resp = client.chat.completions.create(
                            messages=[{"role":"user","content":prompt}], 
                            model="llama-3.1-8b-instant" 
                        )
                        st.session_state[f"m_{i}"] = resp.choices[0].message.content
                    except Exception as e:
                        st.error(f"AI Error: {e}")
                
                st.text_area("Edit:", value=st.session_state.get(f"m_{i}", ""), key=f"e_{i}")
                
                # FIXED GMAIL: SSL Port 465
                if st.button(f"Send", key=f"s_{i}"):
                    try:
                        context = ssl.create_default_context()
                        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                            server.login(st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASSWORD"])
                            server.sendmail(st.secrets["GMAIL_USER"], lead['Email'], f"Subject: Proposal\n\n{st.session_state.get(f'm_{i}', '')}")
                        st.success("Sent!")
                    except Exception as e:
                        st.error(f"Gmail Login Failed: {e}")
