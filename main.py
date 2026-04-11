import streamlit as st
import pandas as pd
import requests
import re
import smtplib
import ssl
from email.mime.text import MIMEText
from groq import Groq

# --- 1. CONFIGURATION & BRANDING ---
st.set_page_config(page_title="Vantedge-Outreach-Pro", layout="wide")
st.title("Vantedge-Outreach-Pro 🚀")
st.markdown("### Professional AI Lead Generation & Outreach Agent")

# API Keys Check from Streamlit Secrets
if "GROQ_API_KEY" not in st.secrets or "SERPER_API_KEY" not in st.secrets:
    st.error("API Keys missing in Secrets! Please check your Streamlit dashboard.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 2. CORE ENGINES ---
def extract_emails(url):
    try:
        # Increased timeout for better scraping success
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=8)
        # Advanced Regex for email extraction
        found_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', response.text)
        # Filter out junk/image files from results
        valid_emails = [e.lower() for e in set(found_emails) if not any(x in e.lower() for x in ['png', 'jpg', 'jpeg', 'wix', 'sentry', 'gif'])]
        return valid_emails[0] if valid_emails else None
    except:
        return None

# --- 3. UI INTERFACE ---
tab1, tab2 = st.tabs(["🔍 Lead Hunter Engine", "✉️ AI Outreach Pitcher"])

with tab1:
    col1, col2 = st.columns(2)
    niche = col1.text_input("Industry/Niche", value="Real Estate Agency")
    city = col2.text_input("Target Location/City", value="London")
    
    if st.button("Hunt Verified Leads"):
        with st.spinner("Vantedge-Pro is hunting for direct business emails..."):
            headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
            
            # Level 3 Aggressive Search Query
            search_queries = [
                f'"{niche}" {city} website "email" -site:facebook.com',
                f'"{niche}" {city} contact page email',
                f'site:.com "{niche}" {city} "owner email"'
            ]
            
            final_leads = []
            links_tracker = set()
            
            progress_bar = st.progress(0)
            
            for idx, q in enumerate(search_queries):
                try:
                    payload = {"q": q, "num": 15}
                    search_res = requests.post("https://google.serper.dev/search", headers=headers, json=payload).json()
                    organic_results = search_res.get("organic", [])
                    
                    for item in organic_results:
                        target_url = item['link']
                        if target_url not in links_tracker:
                            # Faster check: try finding email in the search snippet first
                            snippet_email = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', item.get('snippet', ''))
                            
                            email_found = snippet_email[0] if snippet_email else extract_emails(target_url)
                            
                            if email_found:
                                final_leads.append({
                                    "Business Name": item['title'],
                                    "Website": target_url,
                                    "Email Address": email_found
                                })
                                links_tracker.add(target_url)
                except:
                    continue
                progress_bar.progress((idx + 1) / len(search_queries))
            
            st.session_state.leads_data = final_leads
            
            if final_leads:
                st.success(f"Success! Found {len(final_leads)} targeted leads.")
                st.table(pd.DataFrame(final_leads))
            else:
                st.warning("No direct emails found for this specific location. Try a broader city.")

with tab2:
    if 'leads_data' in st.session_state and st.session_state.leads_data:
        my_offer = st.text_area("Your Business Offer", "I provide high-quality digital marketing and automation services.")
        
        for i, lead in enumerate(st.session_state.leads_data):
            with st.expander(f"Generate Outreach for: {lead['Business Name']}"):
                
                # AI PITCH GENERATION
                if st.button(f"Generate Personalized Pitch", key=f"btn_gen_{i}"):
                    try:
                        with st.spinner("AI is crafting your email..."):
                            # Using llama-3.1 to avoid decommissioning error
                            prompt = f"Write a professional 2-sentence cold email to {lead['Business Name']} offering {my_offer}. Make it personalized for their website: {lead['Website']}."
                            ai_response = client.chat.completions.create(
                                messages=[{"role": "user", "content": prompt}],
                                model="llama-3.1-8b-instant"
                            )
                            st.session_state[f"pitch_{i}"] = ai_response.choices[0].message.content
                            st.rerun()
                    except Exception as e:
                        st.error(f"AI Generation Error: {e}")

                # Display and Edit Pitch
                current_pitch = st.text_area("Email Draft:", value=st.session_state.get(f"pitch_{i}", ""), height=150, key=f"edit_{i}")
                
                # SMTP EMAIL SENDING
                if st.button(f"Send to {lead['Email Address']}", key=f"send_btn_{i}"):
                    try:
                        email_sender = st.secrets["GMAIL_USER"]
                        email_password = st.secrets["GMAIL_PASSWORD"]
                        
                        context = ssl.create_default_context()
                        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                            server.login(email_sender, email_password)
                            msg = MIMEText(current_pitch)
                            msg['Subject'] = f"Proposal for {lead['Business Name']}"
                            msg['From'] = email_sender
                            msg['To'] = lead['Email Address']
                            server.send_message(msg)
                        st.success("Email Sent Successfully! 🚀")
                    except Exception as e:
                        st.error(f"Failed to send email: {e}. Ensure you are using a 16-digit App Password.")
    else:
        st.info("Please hunt for leads in the first tab to enable the AI Pitcher.")
