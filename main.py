import streamlit as st
import pandas as pd
import requests
import re
import smtplib
import ssl
from email.mime.text import MIMEText
from groq import Groq

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="Vantedge Pro Intelligence", layout="wide")
st.title("Vantedge Pro: Hunter & AI Pitcher 🚀")

# API Keys Check from Secrets
if "GROQ_API_KEY" not in st.secrets or "SERPER_API_KEY" not in st.secrets:
    st.error("API Keys missing hain! Manage App -> Secrets mein check karein.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 2. THE SEARCH & SCRAPE ENGINE ---
def scrape_email(url):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=7)
        # Deep Regex for finding emails
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text)
        # Junk filter (Removing images/wix trash)
        valid = [e.lower() for e in set(emails) if not any(x in e.lower() for x in ['png', 'jpg', 'wix', 'sentry', 'gif', 'jpeg'])]
        return valid[0] if valid else None
    except:
        return None

# --- 3. UI TABS ---
tab1, tab2 = st.tabs(["🔍 Smart Lead Hunter", "✉️ AI Outreach Control"])

with tab1:
    c1, c2 = st.columns(2)
    niche = c1.text_input("Target Niche (e.g., Dental Clinic)", "Roofing Contractors")
    city = c2.text_input("Target City", "Miami")
    
    if st.button("Hunt Verified Leads"):
        with st.spinner("Searching deep for direct emails..."):
            headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
            # POWERFUL SEARCH QUERY: Specifically targets contact/email pages
            search_query = f'"{niche}" {city} "email" OR "contact us" website -site:clutch.co -site:yelp.com -site:facebook.com'
            payload = {"q": search_query, "num": 50}
            
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
                    st.success(f"Mubarak ho! {len(leads)} Unique Leads mil gayi hain!")
                    st.table(pd.DataFrame(leads))
                else:
                    st.warning("Abhi koi email nahi mila. Niche change karke 'Plumbers' ya 'Lawyers' try karein.")
            except Exception as e:
                st.error(f"Search Error: {e}")

with tab2:
    if 'leads' in st.session_state and st.session_state.leads:
        offer = st.text_area("Your Service Offer", "I will provide high-quality B2B leads and AI automation for your business.")
        
        for i, lead in enumerate(st.session_state.leads):
            with st.expander(f"Pitch: {lead['Business']}"):
                # FIXED MODEL: Using llama-3.1-8b-instant to avoid Decommissioned Error
                if st.button(f"Generate AI Pitch", key=f"g_{i}"):
                    try:
                        prompt = f"Write a professional 2-sentence cold email to {lead['Business']} offering {offer}. Website: {lead['Website']}"
                        resp = client.chat.completions.create(
                            messages=[{"role":"user","content":prompt}], 
                            model="llama-3.1-8b-instant" 
                        )
                        st.session_state[f"msg_{i}"] = resp.choices[0].message.content
                    except Exception as e:
                        st.error(f"Groq AI Error: {e}")

                final_text = st.text_area("Final Email:", value=st.session_state.get(f
