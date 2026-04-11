import streamlit as st
import pandas as pd
import requests
import re
import smtplib
import ssl
from email.mime.text import MIMEText
from groq import Groq

# --- 1. SETTINGS ---
st.set_page_config(page_title="Vantedge Pro", layout="wide")
st.title("Vantedge Pro: Hunter & AI Pitcher 🚀")

# --- 2. API KEYS & CLIENT ---
# Check if keys exist to prevent crash
if "GROQ_API_KEY" not in st.secrets or "SERPER_API_KEY" not in st.secrets:
    st.error("Secrets missing! Manage App -> Secrets mein keys check karein.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 3. THE SEARCH ENGINE ---
def scrape_email(url):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text)
        # Deep filter for junk
        valid = [e.lower() for e in set(emails) if not any(x in e.lower() for x in ['png', 'jpg', 'wix', 'sentry', 'example'])]
        return valid[0] if valid else None
    except:
        return None

# --- 4. TABS ---
tab1, tab2 = st.tabs(["🔍 Smart Hunter", "✉️ AI Pitcher"])

with tab1:
    c1, c2 = st.columns(2)
    target_niche = c1.text_input("Niche", "Marketing Agency")
    target_city = c2.text_input("City", "Dubai")
    
    if st.button("Hunt Verified Leads"):
        with st.spinner("Finding direct business owners..."):
            headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
            # High-intent query to get real websites
            payload = {"q": f'"{target_niche}" {target_city} contact email -site:clutch.co -site:yelp.com', "num": 30}
            
            try:
                res = requests.post("https://google.serper.dev/search", headers=headers, json=payload).json()
                results = res.get("organic", [])
                
                leads = []
                seen_links = set() # NO DUPLICATES
                
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
                    st.success(f"Found {len(leads)} Unique Verified Leads!")
                    st.table(pd.DataFrame(leads))
                else:
                    st.warning("No emails found. Try a slightly broader city name.")
            except Exception as e:
                st.error(f"Search Error: {e}")

with tab2:
    if 'leads' in st.session_state and st.session_state.leads:
        my_offer = st.text_area("Your Offer", "I provide AI-powered lead generation to grow your business.")
        
        for i, lead in enumerate(st.session_state.leads):
            with st.expander(f"Pitch for: {lead['Business']}"):
                # --- FIXED GROQ CALL (LATEST MODEL) ---
                if st.button(f"Generate Pitch", key=f"g_{i}"):
                    try:
                        prompt = f"Write a professional 2-sentence cold email to {lead['Business']} offering {my_offer}. Website: {lead['Website']}"
                        # Using llama-3.1-8b-instant which is currently active and fast
                        resp = client.chat.completions.create(
                            messages=[{"role":"user","content":prompt}], 
                            model="llama-3.1-8b-instant" 
                        )
                        st.session_state[f"msg_{i}"] = resp.choices[0].message.content
                    except Exception as e:
                        st.error(f"AI Error: {e}")

                final_text = st.text_area("Edit & Send:", value=st.session_state.get(f"msg_{i}", ""), height=150, key=f"e_{i}")
                
                # --- FIXED GMAIL SENDING ---
                if st.button(f"Send to {lead['Email']}", key=f"s_{i}"):
                    try:
                        context = ssl.create_default_context()
                        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                            server.login(st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASSWORD"])
                            msg = MIMEText(final_text)
                            msg['Subject'] = f"Quick Question for {lead['Business']}"
                            msg['From'] = st.secrets["GMAIL_USER"]
                            msg['To'] = lead['Email']
                            server.send_message(msg)
                        st.success("Sent Successfully! 🚀")
                    except Exception as e:
                        st.error(f"Gmail Error: {e}. Check App Password!")
    else:
        st.info("Pehle leads nikalain.")
