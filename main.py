import streamlit as st
import pandas as pd
import requests
import re
import smtplib
from email.mime.text import MIMEText

# --- 1. SETTINGS ---
st.set_page_config(page_title="Vantedge Hybrid Hunter", layout="wide")
st.title("Vantedge Lead Intelligence 🚀")

# --- 2. THE ENGINE ---
def get_leads_hybrid(niche, city):
    all_organic = []
    headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
    
    # Do different queries taake leads har surat milen
    queries = [f'"{niche}" {city} website', f'{niche} services {city}']
    
    for q in queries:
        payload = {"q": q, "num": 40}
        try:
            res = requests.post("https://google.serper.dev/search", headers=headers, json=payload).json()
            if "organic" in res:
                all_organic.extend(res["organic"])
        except:
            continue
    return all_organic

def find_email_anywhere(url):
    try:
        # Timeout thora barha diya hai taake slow sites bhi load hon
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=8)
        content = r.text
        
        # Sirf home page par email dhoondna
        found = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
        
        # Basic filtering
        clean = [e.lower() for e in set(found) if not any(x in e.lower() for x in ['.png', '.jpg', 'sentry', 'wix', 'example'])]
        return clean[0] if clean else None
    except:
        return None

# --- 3. UI ---
tab1, tab2 = st.tabs(["🔍 Hunter", "📧 Outreach"])

with tab1:
    c1, c2 = st.columns(2)
    n_in = c1.text_input("Niche", value="Real Estate Agency")
    c_in = c2.text_input("City", value="Karachi")
    
    if st.button("Start Hybrid Hunting"):
        with st.spinner("Searching every corner of the web..."):
            results = get_leads_hybrid(n_in, c_in)
            
            # Remove duplicates based on link
            unique_results = {item['link']: item for item in results}.values()
            
            leads = []
            p_bar = st.progress(0)
            
            for i, item in enumerate(unique_results):
                link = item['link']
                # Ignore obvious directory giants but keep everything else
                if not any(x in link for x in ['clutch.co', 'linkedin.com', 'facebook.com']):
                    email = find_email_anywhere(link)
                    if email:
                        leads.append({"Business": item['title'], "Website": link, "Email": email})
                p_bar.progress((i + 1) / len(unique_results))
            
            st.session_state.leads = leads
            if leads:
                st.success(f"Successfully found {len(leads)} leads!")
                st.table(pd.DataFrame(leads))
            else:
                st.warning("No leads with emails found. Try a slightly different term like 'Property' instead of 'Real Estate'.")

with tab2:
    if 'leads' in st.session_state and st.session_state.leads:
        for i, lead in enumerate(st.session_state.leads):
            with st.expander(f"Lead: {lead['Business']}"):
                if st.button(f"Send Pitch", key=f"btn_{i}"):
                    try:
                        server = smtplib.SMTP("smtp.gmail.com", 587)
                        server.starttls()
                        server.login(st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASSWORD"])
                        msg = MIMEText(f"Hello {lead['Business']}, I am interested in your services.")
                        msg['Subject'] = "Business Inquiry"
                        msg['From'] = st.secrets["GMAIL_USER"]
                        msg['To'] = lead['Email']
                        server.sendmail(st.secrets["GMAIL_USER"], lead['Email'], msg.as_string())
                        server.quit()
                        st.success("Email Sent!")
                    except Exception as e:
                        st.error(f"Error: {e}")
