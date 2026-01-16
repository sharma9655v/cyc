import streamlit as st
import joblib
import numpy as np
import requests
import os
from twilio.rest import Client
import folium
from streamlit_folium import st_folium

# ==============================================================================
# 🔑 CONFIGURATION
# ==============================================================================
WEATHER_API_KEY = "22223eb27d4a61523a6bbad9f42a14a7"

# Account 1 Credentials
TWILIO_SID_1 = "ACc9b9941c778de30e2ed7ba57f87cdfbc" 
TWILIO_AUTH_1 = "3cb1dfcb6a9a3cae88f4eff47e9458df"
TWILIO_PHONE_1 = "+15075195618"

# Account 2 Credentials (Backup)
TWILIO_SID_2 = "ACa12e602647785572ebaf765659d26d23"
TWILIO_AUTH_2 = "26210979738809eaf59a678e98fe2c0f"
TWILIO_PHONE_2 = "+14176076960"

# Hosted MP3 Links
URL_ENGLISH_MP3 = "YOUR_PUBLIC_LINK_FOR_alert_detailed.mp3"
URL_TELUGU_MP3 = "YOUR_PUBLIC_LINK_FOR_alert_telugu_final.mp3"

MODEL_FILE = "cyclone_model.joblib"

st.set_page_config(page_title="Vizag SOS Dual-Link", page_icon="🌪️", layout="wide")

# ==============================================================================
# 🆘 SOS FUNCTION (DUAL ACCOUNT FAILOVER)
# ==============================================================================
def trigger_sos_dual(target_phone, language="English"):
    accounts = [
        {"sid": TWILIO_SID_1, "token": TWILIO_AUTH_1, "from": TWILIO_PHONE_1},
        {"sid": TWILIO_SID_2, "token": TWILIO_AUTH_2, "from": TWILIO_PHONE_2}
    ]
    
    audio_url = URL_TELUGU_MP3 if language == "Telugu" else URL_ENGLISH_MP3
    twiml_content = f'<Response><Play>{audio_url}</Play></Response>'
    
    last_error = ""
    for idx, acc in enumerate(accounts):
        try:
            client = Client(acc["sid"], acc["token"])
            client.calls.create(twiml=twiml_content, to=target_phone, from_=acc["from"])
            return f"SUCCESS (Account {idx+1})"
        except Exception as e:
            last_error = str(e)
            continue
            
    return f"FAILED BOTH ACCOUNTS: {last_error}"

# ==============================================================================
# 🔮 MODEL LOADING (DEBUGGED)
# ==============================================================================
@st.cache_resource
def load_model():
    if not os.path.exists(MODEL_FILE):
        st.warning(f"⚠️ Model file '{MODEL_FILE}' not found. Please upload it.")
        return None
    try:
        return joblib.load(MODEL_FILE)
    except ModuleNotFoundError as e:
        # This fixes your specific error
        st.error(f"❌ Missing Library: {e}. Check your requirements.txt file.")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error loading model: {e}")
        return None

model = load_model()

# ==============================================================================
# 📊 DASHBOARD UI
# ==============================================================================
st.title("🌪️ Vizag Cyclone Command Center (Dual SOS)")

with st.sidebar:
    st.header("🚨 Emergency Contacts")
    c1 = st.text_input("Primary Contact", "+917678495189")
    c2 = st.text_input("Family Contact", "+918130631551")
    
    st.divider()
    call_lang = st.radio("Select MP3 Language", ["English", "Telugu"])
    
    if st.button("🚨 TRIGGER SOS CALLS", type="primary", use_container_width=True):
        for t in [c1, c2]:
            if len(t) > 10:
                with st.spinner(f"Initiating call to {t}..."):
                    result = trigger_sos_dual(t, call_lang)
                    if "SUCCESS" in result: st.success(f"✅ {t}: {result}")
                    else: st.error(f"❌ {t}: {result}")

# Data Display
if model:
    # (Existing Weather and Map logic here)
    st.info("Model loaded successfully. Real-time prediction active.")
else:
    st.error("System is running without the prediction model. SOS remains active.")