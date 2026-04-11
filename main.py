import streamlit as st
import pandas as pd
import requests
import re
from groq import Groq

st.set_page_config(page_title="Vantedge-Outreach-Pro", layout="wide")
st.title("Vantedge-Outreach-Pro 🚀")

# API Setup
if "GROQ_API_KEY" not in st.secrets or "SERPER_API_KEY" not in st.secrets:
    st.error("API Keys missing in Secrets!")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- TAB 1: HUNTER ---
tab1, tab2 = st.tabs(["🔍 Hunter", "✉️ Pitcher"])

with tab1:
    c1, c2 = st.columns(2)
    niche = c1.text_input("Niche", "Dental Clinic")
    city = c2.text_input("City", "London")
    
    if st.button("Hunt Leads"):
        with st.spinner("Searching..."):
            headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
            query = f'"{niche}" {city} website email'
            res = requests.post("https://google.serper.dev/search", headers=headers, json={"q": query}).json()
            
            leads = []
            for item in res.get("organic", []):
                # Search snippet for email first (Faster!)
                email = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', item.get('snippet', ''))
                if email:
                    leads.append({"Business": item['title'], "Email": email[0]})
            
            st.session_state.leads_data = leads
            if leads:
                st.table(pd.DataFrame(leads))
            else:
                st.error("No emails found. Try 'Dubai' for demo.")

# --- TAB 2: PITCHER ---
with tab2:
    if 'leads_data' in st.session_state and st.session_state.leads_data:
        offer = st.text_area("Your Offer", "I build AI Agents for businesses.")
        
        for i, lead in enumerate(st.session_state.leads_data):
            with st.expander(f"Pitch for: {lead['Business']}"):
                
                # CRITICAL FIX: The button now saves to session state and reruns
                if st.button(f"Generate Pitch", key=f"gen_{i}"):
                    try:
                        # Using stable llama-3.1 model
                        prompt = f"Write a 1-sentence email to {lead['Business']} about {offer}."
                        resp = client.chat.completions.create(
                            messages=[{"role": "user", "content": prompt}],
                            model="llama-3.1-8b-instant"
                        )
                        st.session_state[f"msg_{i}"] = resp.choices[0].message.content
                        st.rerun() # FORCE REFRESH TO SHOW TEXT
                    except Exception as e:
                        st.error(f"AI Error: {e}")

                # Display text directly from session state
                current_msg = st.session_state.get(f"msg_{i}", "")
                st.text_area("Edit Draft:", value=current_msg, height=100, key=f"edit_{i}")
                
                if st.button(f"Send to {lead['Email']}", key=f"send_{i}"):
                    st.success("Sent!")
    else:
        st.info("Pehle leads hunt karein.")
