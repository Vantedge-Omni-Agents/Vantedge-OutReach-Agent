import streamlit as st
import pandas as pd  # Pandas ko 'pd' ke taur par import kiya gaya hai
import requests
import json
import resend
from groq import Groq

# --- 1. CONFIGURATION & SECRETS ---
st.set_page_config(page_title="Vantedge Intelligence OS", layout="wide", page_icon="🚀")

# Secrets fetch karne ka safe tareeka
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    RESEND_API_KEY = st.secrets["RESEND_API_KEY"]
    SERPER_API_KEY = st.secrets["SERPER_API_KEY"]
except Exception as e:
    st.error("⚠️ API Keys Missing! Please add them in Streamlit Cloud Secrets.")
    st.stop()

# Clients initialize karna
client_groq = Groq(api_key=GROQ_API_KEY)
resend.api_key = RESEND_API_KEY

# --- 2. CORE FUNCTIONS ---

def get_b2b_leads(niche, location):
    """Serper API se leads nikalne ke liye optimized function"""
    url = "https://google.serper.dev/search"
    # Query ko broad rakha hai taake 'No leads found' ka masla na ho
    search_query = f"{niche} companies in {location} contact email"
    payload = json.dumps({"q": search_query, "num": 10})
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        return response.json().get("organic", [])
    except Exception as e:
        st.error(f"Search Error: {str(e)}")
        return []

def generate_ai_pitch(target_name, context):
    """Groq se personalized pitch generate karna (llama-3.3 model ke saath)"""
    if not context:
        context = "a professional business looking for digital growth"
    
    # Stable model name
    model_name = "llama-3.3-70b-versatile"
    
    prompt = f"Write a short, punchy 2-line cold email to {target_name}. Focus on how Horbex Digital can help them scale. Context: {context}"
    
    try:
        completion = client_groq.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model_name,
            temperature=0.7
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"AI Generation Error: {str(e)}"

# --- 3. MAIN UI ---
st.title("Vantedge Intelligence Pro 🚀")
st.caption("Karachi-based AI Lead Gen System | 2026 Edition")

menu = st.sidebar.selectbox("Navigate System", ["Lead Hunter", "Outreach Agent"])

if menu == "Lead Hunter":
    st.header("🔍 B2B Data Extraction")
    col1, col2 = st.columns(2)
    niche_input = col1.text_input("Target Niche", placeholder="e.g. Real Estate, Solar Agencies")
    loc_input = col2.text_input("Target Location", placeholder="e.g. Karachi, Dubai, USA")
    
    if st.button("Extract Leads"):
        if niche_input and loc_input:
            with st.spinner("Mining high-intent leads..."):
                leads_data = get_b2b_leads(niche_input, loc_input)
                if leads_data:
                    st.session_state.leads = leads_data
                    st.success(f"Successfully extracted {len(leads_data)} leads!")
                    # DataFrame display (pd error fixed here)
                    df = pd.DataFrame(leads_data)[['title', 'link', 'snippet']]
                    st.table(df)
                else:
                    st.warning("No leads found. Try adding keywords like 'hiring' or 'marketing'.")
        else:
            st.error("Please fill both niche and location.")

elif menu == "Outreach Agent":
    st.header("🤖 AI Autonomous Outreach")
    if 'leads' in st.session_state:
        for i, lead in enumerate(st.session_state.leads):
            with st.expander(f"Lead: {lead['title']}"):
                st.write(f"**Context:** {lead.get('snippet', 'No data available')}")
                
                if st.button(f"Generate AI Pitch", key=f"gen_{i}"):
                    with st.spinner("AI is crafting your message..."):
                        pitch = generate_ai_pitch(lead['title'], lead.get('snippet', ''))
                        st.session_state[f"pitch_{i}"] = pitch
                        st.info(pitch)
                
                # Agar pitch generate ho chuki hai toh send button dikhao
                if f"pitch_{i}" in st.session_state:
                    if st.button(f"Send to {lead['title']}", key=f"send_{i}"):
                        try:
                            # Demo ke liye aapke email par jayega
                            resend.Emails.send({
                                "from": "Vantedge AI <onboarding@resend.dev>",
                                "to": ["m.salmanraja000@gmail.com"],
                                "subject": f"Inquiry for {lead['title']}",
                                "html": f"<p>{st.session_state[f'pitch_{i}']}</p>"
                            })
                            st.success("✅ Pitch dispatched successfully!")
                        except Exception as e:
                            st.error(f"Mail Error: {str(e)}")
    else:
        st.info("No leads available. Please run Lead Hunter first.")
