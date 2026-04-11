import streamlit as st
import pandas as pd
import requests
import re
import smtplib
from email.mime.text import MIMEText
from groq import Groq

# --- 1. CONFIG & SETUP ---
st.set_page_config(page_title="Vantedge Pro Intelligence", layout="wide")
st.title("Vantedge Pro: Smart Hunter & AI Pitcher 🚀")

# AI Client Setup
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 2. THE ENGINE (With Anti-Duplication) ---
def get_verified_leads(niche, city):
    headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
    all_raw_results = []
    
    # 2 Pages scan for more quantity
    for start in [0, 10]:
        payload = {"q": f'"{niche}" {city} website', "num": 40, "start": start}
        try:
            res = requests.post("https://google.serper.dev/search", headers=headers, json=payload).json()
            if "organic" in res:
                all_raw_results.extend(res["organic"])
        except:
            continue
            
    # --- ANTI-DUPLICATION LOGIC ---
    unique_links = {}
    for item in all_raw_results:
        link = item['link']
        if link not in unique_links: # Duplicate check
            unique_links[link] = item
            
    return list(unique_links.values())

def find_email(url):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=7)
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text)
        blacklist = ['semrush', 'sentry', 'wix', 'png', 'jpg', 'example']
        valid = [e.lower() for e in set(emails) if not any(x in e.lower() for x in blacklist)]
        return valid[0] if valid else None
    except:
        return None

# --- 3. UI TABS ---
tab1, tab2 = st.tabs(["🔍 Smart Hunter", "✉️ AI Pitcher"])

with tab1:
    c1, c2 = st.columns(2)
    n_in = c1.text_input("Target Niche", value="Real Estate Agency")
    c_in = c2.text_input("Target City", value="Dubai")
    
    if st.button("Hunt Unique Leads"):
        with st.spinner("Hunting unique clients (No Duplicates)..."):
            results = get_verified_leads(n_in, c_in)
            leads = []
            p_bar = st.progress(0)
            
            for i, item in enumerate(results):
                # Filter obvious directory giants
                if not any(x in item['link'] for x in ['clutch.co', 'linkedin.com', 'facebook.com']):
                    email = find_email(item['link'])
                    if email:
                        leads.append({"Business": item['title'], "Website": item['link'], "Email": email})
                p_bar.progress((i + 1) / len(results))
            
            st.session_state.leads = leads
            if leads:
                st.success(f"Found {len(leads)} Unique Leads!")
                st.table(pd.DataFrame(leads))
            else:
                st.error("No direct emails found. Try a different city.")

with tab2:
    if 'leads' in st.session_state and st.session_state.leads:
        st.subheader("Personalized AI Outreach")
        
        # User sets the tone/instructions for AI
        ai_instruction = st.text_area("What are you selling?", 
                                     placeholder="e.g. Tell them we can help rank their website on Google for free for 1 month.")

        for i, lead in enumerate(st.session_state.leads):
            with st.expander(f"Pitch to: {lead['Business']}"):
                
                # --- AI GENERATION BUTTON ---
                if st.button(f"Generate AI Pitch for {lead['Business']}", key=f"gen_{i}"):
                    prompt = f"Write a short, professional cold email to {lead['Business']} regarding {ai_instruction}. Mention their website {lead['Website']}."
                    chat_completion = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama3-8b-8192",
                    )
                    st.session_state[f"pitch_text_{i}"] = chat_completion.choices[0].message.content

                # --- EDITABLE PITCH AREA ---
                final_pitch = st.text_area("Edit your pitch here:", 
                                         value=st.session_state.get(f"pitch_text_{i}", ""), 
                                         height=200, key=f"edit_{i}")
                
                if st.button(f"Send to {lead['Email']}", key=f"send_{i}"):
                    try:
                        server = smtplib.SMTP("smtp.gmail.com", 587)
                        server.starttls()
                        server.login(st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASSWORD"])
                        
                        msg = MIMEText(final_pitch)
                        msg['Subject'] = f"Proposal for {lead['Business']}"
                        msg['From'] = st.secrets["GMAIL_USER"]
                        msg['To'] = lead['Email']
                        
                        server.sendmail(st.secrets["GMAIL_USER"], lead['Email'], msg.as_string())
                        server.quit()
                        st.success("Email Delivered! 🚀")
                    except Exception as e:
                        st.error(f"Gmail Error: {e}")
    else:
        st.info("Pehle 'Smart Hunter' se leads nikaalein.")
