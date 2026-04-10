import pandas as pd  # <--- Ye 'as pd' likhna zaroori hai
import streamlit as st
import requests
import json
# ... baqi imports

# --- 1. FETCHING SECRETS ---
# Ye values aap Streamlit Cloud ke dashboard par 'Secrets' mein dalenge
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    RESEND_API_KEY = st.secrets["RESEND_API_KEY"]
    SERPER_API_KEY = st.secrets["SERPER_API_KEY"]
except KeyError:
    st.error("Secrets not found! Please add them in Streamlit Cloud Settings.")
    st.stop()

# Initializing Clients
client_groq = Groq(api_key=GROQ_API_KEY)
resend.api_key = RESEND_API_KEY

# --- 2. APP LOGIC ---
st.title("Vantedge Omni-Agent 🚀")

tab1, tab2 = st.tabs(["Hunter Pro", "AI Outreach"])

with tab1:
    niche = st.text_input("Niche", "Tech Startups")
    location = st.text_input("Location", "USA")
    
    if st.button("Start Extraction"):
        # Fix for "No leads found" - Using more flexible query
        query = f"{niche} companies in {location} contact email"
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query, "num": 10})
        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        
        response = requests.post(url, headers=headers, data=payload).json()
        if "organic" in response:
            st.session_state.leads = response["organic"]
            st.success(f"Found {len(response['organic'])} leads!")
            st.write(pd.DataFrame(response["organic"])[['title', 'link']])
        else:
            st.error("No leads found. Try broader keywords.")

with tab2:
    if 'leads' in st.session_state:
        lead = st.selectbox("Select Lead", [l['title'] for l in st.session_state.leads])
        if st.button("Send AI Pitch"):
            # Groq Logic
            st.info(f"Sending automated pitch to {lead}...")
            # Resend integration logic here...
    else:
        st.write("Run Hunter first.")
