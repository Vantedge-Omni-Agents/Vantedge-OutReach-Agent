import streamlit as st
from groq import Groq

# --- 1. CONFIG ---
# Secrets mein check karein key sahi paste hui hai
api_key = st.secrets["GROQ_API_KEY"]

try:
    client = Groq(api_key=api_key)
except Exception as e:
    st.error(f"Client Initialize Error: {e}")

# --- 2. THE PITCH GENERATOR FUNCTION ---
def generate_pitch(business_name, website, offer):
    # Error 400 se bachne ke liye hum try-except block use karenge
    try:
        # Simple and clean prompt
        prompt_content = f"Write a 3-line professional cold email for {business_name} ({website}). Offer: {offer}."
        
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt_content,
                }
            ],
            model="llama3-8b-8192", # Model name bilkul sahi hona chahiye
            temperature=0.5,
            max_tokens=300 # Zyada tokens se bhi kabhi error aata hai, limit rakhein
        )
        return response.choices[0].message.content
    except Exception as e:
        # Agar Error 400 aata hai toh yahan show hoga
        return f"Groq Error: {str(e)}"

# --- 3. UI EXAMPLE ---
st.subheader("AI Pitch Tester")
biz = st.text_input("Business Name", "Example Corp")
web = st.text_input("Website", "www.example.com")
off = st.text_area("Your Offer", "Lead generation services")

if st.button("Generate Now"):
    with st.spinner("Talking to Groq..."):
        result = generate_pitch(biz, web, off)
        st.write(result)
