import streamlit as st
import pandas as pd  # <--- Fix 1: Alias 'pd' defined
import requests
import json
import resend
from groq import Groq

# --- 1. SECRETS FETCHING ---
# Streamlit Cloud ke 'Secrets' section mein ye keys lazmi honi chahiye
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    RESEND_API_KEY = st.secrets["RESEND_API_KEY"]
    SERPER_API_KEY = st.secrets["SERPER_API_KEY"]
except Exception as e:
    st.error("Secrets Error: Please add API keys in Streamlit Cloud Settings.")
    st.stop()

# Initializing Clients
client_groq = Groq(api_key=GROQ_API_KEY) # <--- Fix 2: Key now defined
resend.api_key = RESEND_API_KEY

# --- 2. APP UI ---
st.set_page_config(page_title="Vantedge Omni-Agent", layout="wide")

st.title("Vantedge Intelligence OS 🚀")
st.sidebar.title("Vantedge Menu")
app_mode = st.sidebar.selectbox("Choose Mode", ["Lead Hunter", "AI Outreach"])

# --- 3. LEAD HUNTER LOGIC ---
if app_mode == "Lead Hunter":
    st.header("B2B Lead Extraction")
    col1, col2 = st.columns(2)
    niche = col1.text_input("Niche", "Marketing Agencies")
    location = col2.text_input("Location", "Karachi")
    
    if st.button("Start Extraction"):
        query = f"{niche} companies in {location} contact email"
        url = "https://google.serper.dev/search"
        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        payload = json.dumps({"q": query, "num": 10})
        
        response = requests.post(url, headers=headers, data=payload).json()
        
        if "organic" in response:
            st.session_state.leads = response["organic"]
            st.success(f"Found {len(response['organic'])} leads!")
            
            # Displaying Data
            df = pd.DataFrame(response["organic"])[['title', 'link', 'snippet']]
            st.write(df) # <--- 'pd' error fixed here
        else:
            st.error("No leads found. Try broader keywords.")

# --- 4. AI OUTREACH LOGIC ---
elif app_mode == "AI Outreach":
    st.header("AI Outreach Agent")
    if 'leads' in st.session_state:
        for lead in st.session_state.leads:
            with st.expander(f"Contact {lead['title']}"):
                if st.button(f"Generate Pitch for {lead['title']}", key=lead['link']):
                    prompt = f"Write a short 2-line professional email to {lead['title']}. Use context: {lead.get('snippet','')}"
                    chat = client_groq.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama3-8b-8192"
                    )
                    pitch = chat.choices[0].message.content
                    st.info(pitch)
                    
                    if st.button("Send via Resend", key=f"send_{lead['link']}"):
                        # Email sending logic
                        st.toast("Email Dispatched!")
    else:
        st.warning("Please run Lead Hunter first.")
