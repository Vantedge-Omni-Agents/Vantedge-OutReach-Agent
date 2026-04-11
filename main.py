import streamlit as st
import pandas as pd
import requests
import re
from groq import Groq

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Vantedge-Outreach-Pro", layout="wide")
st.title("Vantedge-Outreach-Pro 🚀")
st.markdown("### Automatic Lead Generation & AI Pitching")

# API Keys Check
if "GROQ_API_KEY" not in st.secrets or "SERPER_API_KEY" not in st.secrets:
    st.error("API Keys missing in Secrets!")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 2. THE ENGINE ---
def get_email(url):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text)
        valid = [e.lower() for e in set(emails) if not any(x in e.lower() for x in ['png', 'jpg', 'wix', 'sentry'])]
        return valid[0] if valid else None
    except:
        return None

# --- 3. MAIN INTERFACE ---
c1, c2 = st.columns(2)
niche = c1.text_input("Niche", "Marketing Agency")
city = c2.text_input("City", "New York")
offer = st.text_area("Your Business Offer", "I provide high-quality AI automation and lead generation.")

if st.button("Start Automatic Outreach Process"):
    with st.spinner("Step 1: Hunting 30+ Leads..."):
        headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
        # Optimized query for maximum results
        query = f'"{niche}" {city} website email OR "contact us"'
        res = requests.post("https://google.serper.dev/search", headers=headers, json={"q": query, "num": 50}).json()
        
        results = res.get("organic", [])
        leads = []
        
        for item in results:
            if len(leads) >= 35: break # Target 30+
            
            # Fast check snippet for email
            snip_email = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', item.get('snippet', ''))
            email = snip_email[0] if snip_email else get_email(item['link'])
            
            if email:
                leads.append({"Business": item['title'], "Email": email, "Website": item['link']})

        if leads:
            st.success(f"Step 1 Complete! Found {len(leads)} Leads.")
            
            # --- AUTOMATIC PITCH GENERATION ---
            st.markdown("---")
            st.markdown("### Step 2: Automatic AI Pitch Generation")
            
            for i, lead in enumerate(leads):
                with st.container():
                    st.info(f"Generating for: {lead['Business']}")
                    try:
                        # Using stable llama-3.1-8b-instant
                        prompt = f"Write a 1-sentence professional cold email to {lead['Business']} offering {offer}."
                        ai_resp = client.chat.completions.create(
                            messages=[{"role": "user", "content": prompt}],
                            model="llama-3.1-8b-instant"
                        )
                        pitch = ai_resp.choices[0].message.content
                        
                        # Display directly
                        col_a, col_b = st.columns([3, 1])
                        col_a.text_area(f"Pitch for {lead['Email']}", value=pitch, height=100, key=f"pitch_{i}")
                        if col_b.button(f"Send to {lead['Business']}", key=f"send_{i}"):
                            col_b.success("Sent!")
                    except Exception as e:
                        st.error(f"AI Skip: {e}")
        else:
            st.error("No leads found. Please try a broader city like 'Chicago' or 'London'.")
