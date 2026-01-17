import streamlit as st
import joblib
import numpy as np
import os
import requests
from twilio.rest import Client  #

# ==============================================================================
# MODULE 1: CONFIGURATION & CREDENTIALS
# ==============================================================================
CONFIG = {
    "APP_TITLE": "Vizag Cyclone Command Center",
    "API_KEY": "22223eb27d4a61523a6bbad9f42a14a7",
    "MODEL_PATH": "cyclone_model.joblib",
    "TARGET_CITY": "Visakhapatnam",
    "DEFAULT_COORDS": (17.6868, 83.2185)
}

# Twilio Credentials
TWILIO_ACCOUNTS = {
    "Primary": {
        "SID": "ACc9b9941c778de30e2ed7ba57f87cdfbc",
        "AUTH": "3cb1dfcb6a9a3cae88f4eff47e9458df",
        "PHONE": "+15075195618"
    },
    "Backup": {
        "SID": "ACa12e602647785572ebaf765659d26d23",
        "AUTH": "6460cb8dfe71e335741bb20bc14c452a",
        "PHONE": "+14176076960"
    }
}

# Voice Asset URLs (Direct download format for Twilio)
VOICE_MAP = {
    "📢 Regional Broadcast (English)": "https://drive.google.com/file/d/1CWswvjAoIAO7h6C6Jh-uCsrOWFM7dnS_/view?usp=sharing",
    "🇮🇳 Emergency Alert (Telugu)": "https://drive.google.com/file/d/15xz_g_TvMAF2Icjesi3FyMV6MMS-RZHt/view?usp=sharingt"
}

st.set_page_config(page_title=CONFIG["APP_TITLE"], page_icon="🌪️", layout="wide")

# ==============================================================================
# MODULE 2: EMERGENCY SERVICES (TWILIO)
# ==============================================================================
class EmergencyService:
    @staticmethod
    def trigger_voice_call(to_number, audio_url, account_key="Primary"):
        """Initiates a Twilio call playing a custom AI voice file."""
        try:
            acc = TWILIO_ACCOUNTS[account_key]
            client = Client(acc["SID"], acc["AUTH"])
            
            # TwiML instructions to play the audio file
            twiml_content = f'<Response><Play>{audio_url}</Play></Response>'
            
            call = client.calls.create(
                twiml=twiml_content,
                to=to_number,
                from_=acc["PHONE"]
            )
            return True, call.sid
        except Exception as e:
            return False, str(e)

# ==============================================================================
# MODULE 3: CORE LOGIC & WEATHER
# ==============================================================================
class PhysicsFallbackModel:
    def predict(self, X):
        pressure = X[0][2]
        if pressure < 960: return np.array([3])
        if pressure < 990: return np.array([2])
        if pressure < 1005: return np.array([1])
        return np.array([0])

@st.cache_resource
def load_cyclone_engine():
    if not os.path.exists(CONFIG["MODEL_PATH"]):
        return PhysicsFallbackModel(), True
    try:
        model = joblib.load(CONFIG["MODEL_PATH"])
        return model, False
    except:
        return PhysicsFallbackModel(), True

model_engine, is_fallback = load_cyclone_engine()

def get_weather(city):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={CONFIG['API_KEY']}"
        r = requests.get(url, timeout=5).json()
        return r['coord']['lat'], r['coord']['lon'], r['main']['pressure'], r['name']
    except:
        return *CONFIG["DEFAULT_COORDS"], 1012, "Default (Simulated)"

# ==============================================================================
# MODULE 4: UI LAYOUT
# ==============================================================================
st.title(f"🌪️ {CONFIG['APP_TITLE']}")

# Fetch Data
lat, lon, pres, loc_name = get_weather(CONFIG["TARGET_CITY"])
risk_level = int(model_engine.predict([[lat, lon, pres]])[0])

with st.sidebar:
    st.header("🎙️ Voice Dispatch Center")
    selected_voice = st.selectbox("Select Language Alert", list(VOICE_MAP.keys()))
    
    # In-app preview
    if st.button("🔊 Preview Audio in Browser"):
        st.audio(VOICE_MAP[selected_voice], format="audio/mp3")
    
    st.divider()
    account_choice = st.radio("Twilio Account", ["Primary", "Backup"])

tab_live, tab_sim, tab_ops = st.tabs(["📡 Live Data Monitor", "🧪 Storm Simulation", "🚨 Emergency Ops"])

# --- EMERGENCY OPS TAB ---
with tab_ops:
    st.header("🚨 AI Voice Call Dispatch")
    st.info("Directly alert local authorities or residents via AI-generated voice calls.")
    
    col_a, col_b = st.columns(2)
    with col_a:
        recipient_no = st.text_input("Recipient Phone Number", placeholder="+91XXXXXXXXXX")
    with col_b:
        st.write("Current Selection:")
        st.write(f"**Voice:** {selected_voice}")
        st.write(f"**Route:** Twilio {account_choice}")

    if st.button("📞 Trigger Emergency AI Call", type="primary"):
        if recipient_no:
            with st.spinner("Initiating call..."):
                success, result = EmergencyService.trigger_voice_call(
                    recipient_no, 
                    VOICE_MAP[selected_voice], 
                    account_choice
                )
                if success:
                    st.success(f"✅ Call connected! SID: {result}")
                else:
                    st.error(f"❌ Call failed: {result}")
        else:
            st.warning("Please enter a valid phone number first.")

# (Rest of your original Dashboard logic for Live Monitor and Simulation...)