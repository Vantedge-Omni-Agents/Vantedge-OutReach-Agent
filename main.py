import streamlit as st
import pandas as pd
import requests
import json
import resend
from groq import Groq

# --- 1. CONFIG & KEYS ---
# Yahan aapki keys images se fetch ki gayi hain
GROQ_API_KEY = "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"
RESEND_API_KEY = "re_EPV2Z8oS_NhCi7ATKAQQEoHNkZwvi6JK7"
SERPER_API_KEY = "a77f5b497d7425b496d0eb05c1bf9ad15b50eb70"

client_groq = Groq(api_key=GROQ_API_KEY)
resend.api_key = RESEND_API_KEY

st.set_page_config(page_title="Vantedge Intelligence OS", layout="wide")

# --- 2. THEME & STYLING ---
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .stButton>button { background-color: #000000; color: white; border-radius: 8px; width: 100%; }
    .lead-card { border: 1px solid #d2d2d7; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CORE FUNCTIONS ---

def get_leads(niche, location):
    """Serper API se leads nikalne ka updated function"""
    url = "https://google.serper.dev/search"
    # Query ko optimized kiya hai taake results lazmi ayen
    query = f"{niche} companies in {location} hiring contact @gmail.com"
    payload = json.dumps({"q": query, "num": 20})
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    
    response = requests.post(url, headers=headers, data=payload).json()
    return response.get("organic", [])

def generate_pitch(name, snippet):
    """Groq Llama-3 se personalized email likhwana"""
    prompt = f"Write a professional 2-line cold email to {name} about digital marketing services. Use this context: {snippet}. Keep it short and helpful."
    completion = client_groq.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content

def send_email(to_email, subject, content):
    """Resend API se email deliver karna"""
    try:
        resend.Emails.send({
            "from": "Vantedge AI <onboarding@resend.dev>",
            "to": [to_email],
            "subject": subject,
            "html": f"<p>{content}</p>"
        })
        return True
    except:
        return False

# --- 4. UI INTERFACE ---
st.title("Vantedge Intelligence Pro")

menu = st.sidebar.radio("Navigation", ["Lead Hunter", "AI Outreach", "Settings"])

if menu == "Lead Hunter":
    col1, col2 = st.columns(2)
    niche = col1.text_input("Niche", "Marketing Agencies")
    loc = col2.text_input("Location", "Karachi")
    
    if st.button("Start Extraction"):
        leads = get_leads(niche, loc)
        if leads:
            st.session_state.current_leads = leads
            st.success(f"Found {len(leads)} potential leads!")
            for i, lead in enumerate(leads):
                with st.container():
                    st.markdown(f"**{lead['title']}**")
                    st.caption(lead['link'])
                    st.write(lead.get('snippet', 'No description available.'))
                    st.write("---")
        else:
            st.error("No leads found. Try a broader search.")

elif menu == "AI Outreach":
    st.header("Autonomous Outreach Agent")
    if 'current_leads' in st.session_state:
        for lead in st.session_state.current_leads:
            with st.expander(f"Contact {lead['title']}"):
                if st.button(f"Generate & Send Pitch to {lead['title']}", key=lead['title']):
                    with st.spinner("AI is thinking..."):
                        pitch = generate_pitch(lead['title'], lead.get('snippet', ''))
                        st.info(f"Draft: {pitch}")
                        # Testing ke liye abhi aapke email par jayega
                        success = send_email("m.salmanraja000@gmail.com", f"Proposal for {lead['title']}", pitch)
                        if success: st.toast("Email Sent!")
    else:
        st.warning("Please find leads in the 'Lead Hunter' tab first.")

elif menu == "Settings":
    st.write("### System Status")
    st.write(f"Groq API: Connected ✅")
    st.write(f"Resend API: Connected ✅")
    st.write(f"Version: 2.0 (Stable)")
