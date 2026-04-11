import streamlit as st
import pandas as pd
import requests
import re
import smtplib
from email.mime.text import MIMEText
from urllib.parse import urlparse

# --- 1. BRANDING ---
st.set_page_config(page_title="Vantedge Final Boss", layout="wide")
st.title("Vantedge Direct Client Hunter 🚀")

# Directory sites ko block karne ke liye list
EXCLUDE = ['clutch.co', 'semrush.com', 'linkedin.com', 'facebook.com', 'yelp', 'directory', 'list']

def get_deep_email(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        # Step 1: Home page check karein
        res = requests.get(url, headers=headers, timeout=5)
        text = res.text
        
        # Step 2: Agar email na mile, toh 'Contact' page dhoondein
        if not re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text):
            contact_links = re.findall(r'href=[\'"]?([^\'" >]+contact[^\'" >]*)[\'"]?', text, re.I)
            if contact_links:
                contact_url = contact_links[0]
                if not contact_url.startswith('http'):
                    base = urlparse(url).netloc
                    contact_url = f"https://{base}/{contact_url.lstrip('/')}"
                res = requests.get(contact_url, headers=headers, timeout=5)
                text += res.text

        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        valid = [e.lower() for e in set(emails) if not any(x in e.lower() for x in ['.png', '.jpg', '.webp', 'sentry'])]
        return valid[0] if valid else None
    except:
        return None

# --- 2. UI ---
tab1, tab2 = st.tabs(["🔍 Hunter", "📧 Outreach"])

with tab1:
    c1, c2 = st.columns(2)
    niche = c1.text_input("Specific Niche", value="Real Estate Marketing")
    city = c2.text_input("City", value="Dubai")
    
    if st.button("Hunt Direct Clients"):
        with st.spinner("Deep scanning for direct clients..."):
            headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
            # Hum 100 results mangwa rahe hain
            payload = {"q": f'"{niche}" {city} -site:clutch.co -site:linkedin.com', "num": 100}
            res = requests.post("https://google.serper.dev/search", headers=headers, json=payload).json()
            
            final_leads = []
            if "organic" in res:
                for item in res["organic"]:
                    link = item['link']
                    if not any(x in link for x in EXCLUDE):
                        email = get_deep_email(link)
                        if email:
                            final_leads.append({"Business": item['title'], "Website": link, "Email": email})
            
            st.session_state.leads = final_leads
            if final_leads:
                st.table(pd.DataFrame(final_leads))
            else:
                st.error("No direct leads found. Try a different city or niche.")

with tab2:
    if 'leads' in st.session_state and st.session_state.leads:
        for i, lead in enumerate(st.session_state.leads):
            with st.expander(f"Pitch: {lead['Business']}"):
                if st.button(f"Send AI Pitch", key=f"p_{i}"):
                    try:
                        server = smtplib.SMTP("smtp.gmail.com", 587)
                        server.starttls()
                        server.login(st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASSWORD"])
                        msg = MIMEText(f"Hello {lead['Business']}, let's talk.")
                        msg['Subject'] = "Proposal"
                        msg['From'] = st.secrets["GMAIL_USER"]
                        msg['To'] = lead['Email']
                        server.sendmail(st.secrets["GMAIL_USER"], lead['Email'], msg.as_string())
                        server.quit()
                        st.success("Sent!")
                    except Exception as e:
                        st.error(f"Error: {e}")
