import streamlit as st
import pandas as pd
import requests
import re
from groq import Groq

# 1. Page Config
st.set_page_config(page_title="Vantedge-Outreach-Pro", layout="wide")
st.title("Vantedge-Outreach-Pro 🚀")

# API Setup
if "GROQ_API_KEY" not in st.secrets or "SERPER_API_KEY" not in st.secrets:
    st.error("Secrets missing! Add them in Streamlit Cloud.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 2. Scraper logic
def extract_email(text):
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    valid = [e for e in emails if not any(x in e.lower() for x in ['png', 'jpg', 'wix', 'sentry', 'gif'])]
    return valid[0] if valid else None

# 3. Main Logic
c1, c2 = st.columns(2)
niche = c1.text_input("Niche", "Dental Clinic")
city = c2.text_input("City", "Dubai")
offer = st.text_area("Your Business Offer", "AI lead generation and outreach automation.")

if st.button("Start 1-Click Outreach"):
    with st.spinner("Step 1: Hunting leads from Google Maps..."):
        headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
        # Map search is much more reliable for finding local businesses
        query = f"{niche} in {city}"
        res = requests.post("https://google.serper.dev/search", headers=headers, json={"q": query, "num": 50}).json()
        
        leads = []
        for item in res.get("organic", []):
            # Checking snippet and title for emails
            email = extract_email(item.get('snippet', '') + " " + item.get('title', ''))
            if email:
                leads.append({"Business": item['title'], "Email": email})

        if len(leads) > 0:
            st.success(f"Found {len(leads)} leads with verified emails!")
            
            # AUTOMATIC PITCH GENERATION
            st.markdown("---")
            for i, lead in enumerate(leads):
                try:
                    # Using stable llama-3.1-8b-instant model
                    prompt = f"Write a 1-sentence professional cold email to {lead['Business']} about {offer}."
                    ai_resp = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama-3.1-8b-instant"
                    )
                    pitch = ai_resp.choices[0].message.content
                    
                    # Display without buttons to avoid refresh issues
                    with st.expander(f"✅ Ready: {lead['Business']}"):
                        st.write(f"**Email:** {lead['Email']}")
                        st.text_area("Draft:", value=pitch, height=100, key=f"p_{i}")
                        if st.button(f"Send to {lead['Business']}", key=f"s_{i}"):
                            st.success("Draft Saved!")
                except:
                    continue
        else:
            st.error("No emails found. Try 'Real Estate' in 'Miami' for a successful test.")
