import streamlit as st
import pandas as pd
import requests
import re
import smtplib
from email.mime.text import MIMEText
from urllib.parse import urlparse

# --- 1. SETTINGS ---
st.set_page_config(page_title="Vantedge Intelligence", layout="wide")
st.title("Vantedge Direct OutReach 🚀")

# --- 2. DIRECT CLIENT FILTER ---
# Directory sites ko nikalne ke liye list
EXCLUDE_LIST = [
    'clutch.co', 'semrush.com', 'linkedin.com', 'facebook.com', 
    'yelp.com', 'upcity.com', 'expertido.com', 'agencyspotter.com',
    'yellowpages.com', 'crunchbase.com'
]

def is_direct_client(url):
    domain = urlparse(url).netloc.lower()
    return not any(site in domain for site in EXCLUDE_LIST)

def get_direct_leads(niche, city):
    all_results = []
    headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
    
    # Page 1 se 3 tak scan (Quantity barhane ke liye)
    for start in [0, 10, 20]:
        payload = {"q": f'"{niche}" {city} -site:clutch.co', "num": 50, "start": start}
        try:
            res = requests.post("https://google.serper.dev/search", headers=headers, json=payload).json()
            if "organic" in res:
                all_results.extend(res["organic"])
        except:
            continue
    return all_results

def extract_clean_email(url):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text)
        # Kachra extensions nikalna
        valid = [e.lower() for e in set(emails) if not any(x in e.lower() for x in ['.png', '.jpg', '.webp', 'sentry.io'])]
        return valid[0] if valid else None
    except:
        return None

# --- 3. UI TABS ---
tab1, tab2 = st.tabs(["🔍 Direct Lead Hunter", "📧 Auto Outreach"])

with tab1:
    col1, col2 = st.columns(2)
    n_in = col1.text_input("Niche", value="Marketing Agency")
    c_in = col2.text_input("City", value="Dubai")
    
    if st.button("Hunt Direct Clients"):
        with st.spinner("Filtering out directories and hunting direct clients..."):
            raw_data = get_direct_leads(n_in, c_in)
            final_leads = []
            progress = st.progress(0)
            
            for i, item in enumerate(raw_data):
                link = item['link']
                # Check agar ye directory site toh nahi
                if is_direct_client(link):
                    email = extract_clean_email(link)
                    if email:
                        final_leads.append({"Business": item['title'], "Website": link, "Email": email})
                progress.progress((i + 1) / len(raw_data))
            
            st.session_state.leads = final_leads
            if final_leads:
                st.success(f"Found {len(final_leads)} Direct Client Leads!")
                st.table(pd.DataFrame(final_leads))
            else:
                st.warning("No direct emails found. Try broadening the niche slightly.")

with tab2:
    if 'leads' in st.session_state and st.session_state.leads:
        st.subheader("Auto Outreach Control")
        for i, lead in enumerate(st.session_state.leads):
            with st.expander(f"Lead: {lead['Business']}"):
                st.write(f"Email: {lead['Email']}")
                if st.button(f"Send AI Pitch", key=f"pitch_{i}"):
                    try:
                        server = smtplib.SMTP("smtp.gmail.com", 587)
                        server.starttls()
                        # Yahan App Password lazmi hai
                        server.login(st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASSWORD"])
                        
                        msg = MIMEText(f"Hi {lead['Business']},\n\nWe saw your website {lead['Website']} and want to work with you.")
                        msg['Subject'] = "Collaboration Proposal"
                        msg['From'] = st.secrets["GMAIL_USER"]
                        msg['To'] = lead['Email']
                        
                        server.sendmail(st.secrets["GMAIL_USER"], lead['Email'], msg.as_string())
                        server.quit()
                        st.success("Sent!")
                    except Exception as e:
                        st.error(f"Gmail Error: {e}")
    else:
        st.info("Pehle leads extract karein.")
