import streamlit as st
import requests
import smtplib
import ssl
from email.mime.text import MIMEText
from groq import Groq

# --- 1. PAGE SETUP & MEMORY ---
st.set_page_config(page_title="Vantedge-Outreach-Pro", layout="wide")
st.title("Vantedge-Outreach-Pro 🚀")

# System Memory: Ye leads aur pitches ko screen se gayab nahi hone dega
if 'leads_data' not in st.session_state:
    st.session_state.leads_data = []
if 'ai_pitches' not in st.session_state:
    st.session_state.ai_pitches = {}

# --- 2. API CHECK ---
if "GROQ_API_KEY" not in st.secrets or "SERPER_API_KEY" not in st.secrets:
    st.error("API Keys missing in Secrets!")
    st.stop()

# Email Secrets Check
if "GMAIL_USER" not in st.secrets or "GMAIL_PASSWORD" not in st.secrets:
    st.warning("⚠️ GMAIL_USER aur GMAIL_PASSWORD secrets mein add karein taake actual email send ho sakay.")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 3. UI INPUTS ---
c1, c2 = st.columns(2)
niche = c1.text_input("Niche", "Digital Marketing Agency")
city = c2.text_input("City", "USA")
offer = st.text_area("Your Offer", "I provide high-quality AI automation and lead generation.")

# --- 4. HUNT LEADS BUTTON ---
if st.button("Start Automatic Process"):
    with st.spinner("Hunting Leads..."):
        headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
        payload = {"q": f"{niche} in {city}", "num": 50}
        
        try:
            res = requests.post("https://google.serper.dev/places", headers=headers, json=payload).json()
            leads = res.get("places", [])
            
            # Leads ko memory mein save kar liya!
            st.session_state.leads_data = leads
            st.session_state.ai_pitches = {} # Purani pitches clear kar dein
            st.rerun() # Screen update karein
        except Exception as e:
            st.error(f"Search failed: {e}")

# --- 5. SHOW LEADS & SEND EMAILS ---
if st.session_state.leads_data:
    st.success(f"Boom! Found {len(st.session_state.leads_data)} businesses.")
    st.markdown("---")
    
    for i, lead in enumerate(st.session_state.leads_data):
        business_name = lead.get('title', 'Business')
        # Agar map data mein email na ho toh website ki base par ek email banate hain
        email_address = f"info@{business_name.lower().replace(' ', '').replace(',', '')}.com"
        
        # Agar AI pitch abhi tak nahi bani is business ke liye, toh banao
        if i not in st.session_state.ai_pitches:
            try:
                prompt = f"Write a punchy 1-sentence cold email to {business_name} offering {offer}. Professional tone."
                ai_resp = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.1-8b-instant"
                )
                # Pitch ko memory mein save kar liya!
                st.session_state.ai_pitches[i] = ai_resp.choices[0].message.content
            except:
                st.session_state.ai_pitches[i] = "Error generating pitch. Please write manually."

        # UI Display
        with st.expander(f"📍 {business_name} | ✉️ {email_address}"):
            
            # Text area ko session state se link kar diya hai. Ab edit karne par data delete nahi hoga!
            current_draft = st.text_area(
                "Edit your pitch (Changes are saved automatically):", 
                value=st.session_state.ai_pitches[i], 
                height=120, 
                key=f"edit_pitch_{i}"
            )
            
            # THE REAL SEND BUTTON
            if st.button(f"Send Email to {business_name}", key=f"send_btn_{i}"):
                with st.spinner("Sending actual email..."):
                    try:
                        # Asal Gmail sending logic
                        context = ssl.create_default_context()
                        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                            server.login(st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASSWORD"])
                            msg = MIMEText(current_draft)
                            msg['Subject'] = f"Partnership Inquiry - Vantedge Leads"
                            msg['From'] = st.secrets["GMAIL_USER"]
                            msg['To'] = email_address
                            
                            server.send_message(msg)
                        st.success("✅ Email successfully sent via Gmail!")
                    except Exception as e:
                        st.error(f"Failed to send email. Error: {e}. (Please ensure your Gmail App Password is correct in secrets)")
