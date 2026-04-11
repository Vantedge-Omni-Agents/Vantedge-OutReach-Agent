import streamlit as st
import pandas as pd
import requests
import re
import smtplib
from email.mime.text import MIMEText
from groq import Groq
from urllib.parse import urlparse

# --- 1. BRANDING & SETUP ---
st.set_page_config(page_title="Vantedge God-Mode", layout="wide")
st.title("Vantedge Pro: Smart Hunter & AI Pitcher 🚀")

# Groq AI Setup
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 2. DEEP EMAIL SCRAPER ---
def deep_scrape_email(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        # Home Page scan
        r = requests.get(url, headers=headers, timeout=8)
        text = r.text
        
        # Agar home page pe email na mile, toh common pages dhoondo
        if not re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text):
            # Contact/About pages dhoondo
            sub_pages = re.findall(r'href=[\'"]?([^\'" >]+(?:contact|about|info)[^\'" >]*)[\'"]?', text, re.I)
            for sub in sub_pages[:2]: # Sirf pehle 2 sub-pages scan karein
                if not sub.startswith('http'):
                    base = urlparse(url).netloc
                    sub = f"https://{base}/{sub.lstrip('/')}"
                r_sub = requests.get(sub, headers=headers, timeout=5)
                text += r_sub.text

        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        valid = [e.lower() for e in set(emails) if not any(x in e.lower() for x in ['.png', '.jpg', 'sentry', 'wix'])]
        return valid[0] if valid else None
    except:
        return None

# --- 3. UI TABS ---
tab1, tab2 = st.tabs(["🔍 Aggressive Hunter", "✉️ AI Pitcher"])

with tab1:
    col1, col2 = st.columns(2)
    n_in = col1.text_input("Niche", value="Real Estate Agency")
    c_in = col2.text_input("City", value="Karachi")
    
    if st.button("Start Aggressive Hunt"):
        with st.spinner("Hunting for unique direct leads..."):
            headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
            # Google se 100 results mangwayein
            payload = {"q": f'"{n_in}" {c_in} website -site:clutch.co -site:linkedin.com', "num": 100}
            res = requests.post("https://google.serper.dev/search", headers=headers, json=payload).json()
            
            leads = []
            seen_links = set() # Anti-duplication logic
            p_bar = st.progress(0)
            
            if "organic" in res:
                for i, item in enumerate(res["organic"]):
                    link = item['link']
                    if link not in seen_links:
                        email = deep_scrape_email(link)
                        if email:
                            leads.append({"Business": item['title'], "Website": link, "Email": email})
                            seen_links.add(link)
                    p_bar.progress((i + 1) / len(res["organic"]))
            
            st.session_state.leads = leads
            if leads:
                st.success(f"Found {len(leads)} Unique Leads!")
                st.table(pd.DataFrame(leads))
            else:
                st.error("No emails found. Try a different city or broaden your niche.")

with tab2:
    if 'leads' in st.session_state and st.session_state.leads:
        user_prompt = st.text_area("AI Pitch Instructions", placeholder="e.g. Tell them I can help them get 10x more leads through SEO.")
        
        for i, lead in enumerate(st.session_state.leads):
            with st.expander(f"Pitch: {lead['Business']}"):
                if st.button(f"Draft AI Pitch", key=f"gen_{i}"):
                    full_prompt = f"Write a short, professional cold email to {lead['Business']} about {user_prompt}. Website: {lead['Website']}."
                    completion = client.chat.completions.create(
                        messages=[{"role": "user", "content": full_prompt}],
                        model="llama3-8b-8192",
                    )
                    st.session_state[f"text_{i}"] = completion.choices[0].message.content
                
                # Editable Pitch
                edited_pitch = st.text_area("Edit Pitch:", value=st.session_state.get(f"text_{i}", ""), height=200, key=f"edit_{i}")
                
                if st.button(f"Send to {lead['Email']}", key=f"send_{i}"):
                    try:
                        server = smtplib.SMTP("smtp.gmail.com", 587)
                        server.starttls()
                        server.login(st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASSWORD"])
                        msg = MIMEText(edited_pitch)
                        msg['Subject'] = f"Proposal for {lead['Business']}"
                        msg['From'] = st.secrets["GMAIL_USER"]
