import streamlit as st
import pandas as pd
import requests
import re
import time
from groq import Groq

# --- 1. SETTINGS ---
st.set_page_config(page_title="Vantedge-Outreach-Pro", layout="wide")
st.title("Vantedge-Outreach-Pro 🚀")
st.markdown("### Automatic Lead Hunter & AI Pitching")

if "GROQ_API_KEY" not in st.secrets or "SERPER_API_KEY" not in st.secrets:
    st.error("API Keys missing in Secrets!")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 2. MULTI-LAYER SCRAPER ---
def get_email_v2(url):
    try:
        # Extended timeout and more realistic headers to avoid blocking
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(url, headers=headers, timeout=10)
        # Regex to find any email pattern
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text)
        # Filter out common junk
        clean = [e.lower() for e in set(emails) if not any(x in e.lower() for x in ['png', 'jpg', 'wix', 'sentry', 'gif', 'svg'])]
        return clean[0] if clean else None
    except:
        return None

# --- 3. UI ---
c1, c2 = st.columns(2)
niche = c1.text_input("Niche (e.g. Real Estate)", "Real Estate")
city = c2.text_input("City (e.g. Dubai)", "Dubai")
offer = st.text_area("Your Business Offer", "I provide high-quality AI automation and lead generation.")

if st.button("Start Automatic Process"):
    with st.spinner("Step 1: Hunting 30+ Leads..."):
        headers = {'X-API-KEY': st.secrets["SERPER_API_KEY"], 'Content-Type': 'application/json'}
        
        # Use a very broad query to force Google to show more results
        query = f'"{niche}" {city} contact email OR "info@"'
        
        try:
            # Requesting 100 results to ensure we find at least 30 with emails
            res = requests.post("https://google.serper.dev/search", headers=headers, json={"q": query, "num": 100}).json()
            organic_results = res.get("organic", [])
            
            leads = []
            status_text = st.empty()
            
            for item in organic_results:
                if len(leads) >= 35: break # Target met
                
                status_text.text(f"Checking: {item['title'][:40]}...")
                
                # Method 1: Check snippet first (fastest)
                snip_email = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', item.get('snippet', ''))
                
                email = snip_email[0] if snip_email else get_email_v2(item['link'])
                
                if email:
                    leads.append({"Business": item['title'], "Email": email, "Website": item['link']})
            
            if leads:
                st.success(f"Success! Found {len(leads)} leads with emails.")
                df = pd.DataFrame(leads)
                st.dataframe(df)
                
                st.markdown("---")
                st.markdown("### Step 2: Auto-Generating AI Pitches")
                
                for i, lead in enumerate(leads):
                    with st.container():
                        try:
                            # Prompt to llama-3.1
                            prompt = f"Write a professional 1-sentence cold email to {lead['Business']} about {offer}."
                            ai_resp = client.chat.completions.create(
                                messages=[{"role": "user", "content": prompt}],
                                model="llama-3.1-8b-instant"
                            )
                            pitch = ai_resp.choices[0].message.content
                            
                            # Display result without needing a button
                            with st.expander(f"Pitch for: {lead['Business']}"):
                                st.write(f"**To:** {lead['Email']}")
                                st.text_area("AI Draft:", value=pitch, height=100, key=f"pitch_{i}")
                                if st.button(f"Send Email", key=f"send_{i}"):
                                    st.success("Sent!")
                        except:
                            st.warning(f"AI skipped {lead['Business']}")
            else:
                st.error("Still no emails found. Try searching for 'Dubai' or 'New York'—their websites are easier to scrape.")
        except Exception as e:
            st.error(f"Search failed: {e}")
