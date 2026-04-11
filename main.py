import streamlit as st
import pandas as pd
import requests
import re
import smtplib
from email.mime.text import MIMEText
from groq import Groq

# --- 1. SETUP ---
st.set_page_config(page_title="Vantedge Pro", layout="wide")
st.title("Vantedge Pro: Hunter & AI Pitcher 🚀")

# Groq Setup
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("Groq API Key missing in Secrets!")

# --- 2. THE ENGINE (No Duplicates & Deep Search) ---
def get_verified_leads(niche, city):
    headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
    all_results = []
    
    # 2 Pages for more quantity
    for start in [0, 10]:
        payload = {"q": f'"{niche}" {city} website', "num": 50, "start": start}
        try:
            res = requests.post("https://google.serper.dev/search", headers=headers, json=payload).json()
            if "organic" in res:
                all_results.extend(res["organic"])
        except:
            continue
    return all_results

def extract_email(url):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=7)
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text)
        # Filter junk
        valid = [e.lower() for e in set(emails) if not any(x in e.lower() for x in ['png', 'jpg', 'wix', 'sentry'])]
        return valid[0] if valid else None
    except:
        return None

# --- 3. INTERFACE ---
tab1, tab2 = st.tabs(["🔍 Hunter", "✉️ AI Pitcher"])

with tab1:
    c1, c2 = st.columns(2)
    target_niche = c1.text_input("Niche", "Real Estate Agency")
    target_city = c2.text_input("City", "Dubai")
    
    if st.button("Hunt Unique Leads"):
        with st.spinner("Hunting..."):
            raw_data = get_verified_leads(target_niche, target_city)
            leads = []
            seen_links = set() # ANTI-DUPLICATION
            
            p_bar = st.progress(0)
            for i, item in enumerate(raw_data):
                link = item['link']
                if link not in seen_links and not any(x in link for x in ['clutch.co', 'linkedin.com']):
                    email = extract_email(link)
                    if email:
                        leads.append({"Business": item['title'], "Website": link, "Email": email})
                        seen_links.add(link)
                p_bar.progress((i + 1) / len(raw_data))
            
            st.session_state.leads = leads
            if leads:
                st.success(f"Found {len(leads)} Unique Leads!")
                st.table(pd.DataFrame(leads))
            else:
                st.warning("No direct emails found. Try a different city.")

with tab2:
    if 'leads' in st.session_state and st.session_state.leads:
        selling_point = st.text_area("What are you selling?", "SEO services to rank #1")
        
        for i, lead in enumerate(st.session_state.leads):
            with st.expander(f"Pitch: {lead['Business']}"):
                # AI generation
                if st.button(f"Generate Pitch", key=f"g_{i}"):
                    prompt = f"Write a short cold email to {lead['Business']} selling {selling_point}. Site: {lead['Website']}"
                    resp = client.chat.completions.create(messages=[{"role":"user","content":prompt}], model="llama3-8b-8192")
                    st.session_state[f"txt_{i}"] = resp.choices[0].message.content
                
                # EDITABLE BOX
                final_text = st.text_area("Edit & Send:", value=st.session_state.get(f"txt_{i}", ""), height=150, key=f"e_{i}")
                
                if st.button(f"Send to {lead['Email']}", key=f"s_{i}"):
                    try:
                        server = smtplib.SMTP("smtp.gmail.com", 587)
                        server.starttls()
                        server.login(st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASSWORD"])
                        msg = MIMEText(final_text)
                        msg['Subject'] = "Business Proposal"
                        msg['From'] = st.secrets["GMAIL_USER"]
                        msg['To'] = lead['Email']
                        server.sendmail(st.secrets["GMAIL_USER"], lead['Email'], msg.as_string())
                        server.quit()
                        st.success("Sent!")
                    except Exception as e:
                        st.error(f"Error: {e}")
    else:
        st.info("Pehle leads nikalein.")
