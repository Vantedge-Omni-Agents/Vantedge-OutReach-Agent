import streamlit as st
import pandas as pd
import requests
from groq import Groq

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Vantedge-Outreach-Pro", layout="wide")
st.title("Vantedge-Outreach-Pro 🚀")

# --- 2. API CHECK ---
if "GROQ_API_KEY" not in st.secrets or "SERPER_API_KEY" not in st.secrets:
    st.error("API Keys missing in Secrets!")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 3. UI INPUTS ---
c1, c2 = st.columns(2)
niche = c1.text_input("Niche", "Dental Clinic")
city = c2.text_input("City", "Miami")
offer = st.text_area("Your Offer", "I provide high-quality AI automation and lead generation.")

# --- 4. MAIN ENGINE ---
if st.button("Start Automatic Process"):
    with st.spinner("Hunting Leads & Generating Pitches..."):
        
        # SEARCH LEADS (Using Places API for guaranteed results)
        headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
        payload = {"q": f"{niche} in {city}", "num": 30}
        
        try:
            res = requests.post("https://google.serper.dev/places", headers=headers, json=payload).json()
            leads = res.get("places", [])
        except Exception as e:
            st.error("Search failed. Check Serper API.")
            leads = []

        if not leads:
            st.error("No leads found. Try 'Real Estate' in 'Miami'.")
        else:
            st.success(f"Boom! Found {len(leads)} businesses. Writing pitches now...")
            st.markdown("---")
            
            # GENERATE PITCHES
            for i, lead in enumerate(leads):
                business = lead.get('title', 'Business')
                # Generating a clean mock email for the demo if not found
                email = f"info@{business.lower().replace(' ', '').replace(',', '')}.com"
                
                try:
                    # AI Call
                    prompt = f"Write a punchy 1-sentence cold email to {business} offering {offer}. Keep it highly professional."
                    ai_resp = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama-3.1-8b-instant"
                    )
                    pitch = ai_resp.choices[0].message.content
                    
                    # UI Display (No nested buttons that reset state)
                    with st.expander(f"📍 {business} | ✉️ {email}"):
                        st.text_area("AI Draft:", value=pitch, height=100, key=f"pitch_{i}")
                        if st.button("Send", key=f"send_{i}"):
                            st.success("Sent! 🚀")
                except:
                    continue # Agar kisi ek mein masla aaye toh baaqi app crash na ho
