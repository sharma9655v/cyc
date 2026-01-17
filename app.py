import streamlit as st
import joblib
import numpy as np
import requests
import os
from twilio.rest import Client
import folium
from streamlit_folium import st_folium

# ==========================================
# 🔑 CONFIGURATION
# ==========================================
# ⚠️ CAUTION: Ensure no extra spaces are in these strings to avoid 401 errors
WEATHER_API_KEY = "22223eb27d4a61523a6bbad9f42a14a7"
MODEL_FILE = "cyclone_model.joblib"

# Primary Account
TWILIO_SID_1 = "ACc9b9941c778de30e2ed7ba57f87cdfbc" 
TWILIO_AUTH_1 = "3cb1dfcb6a9a3cae88f4eff47e9458df"
TWILIO_PHONE_1 = "+15075195618"

# Backup Account
TWILIO_SID_2 = "ACa12e602647785572ebaf765659d26d23"
TWILIO_AUTH_2 = "26210979738809eaf59a678e98fe2c0f"
TWILIO_PHONE_2 = "+14176076960"

# Direct Google Drive Links (Verified Format)
URL_ENGLISH = "https://drive.google.com/uc?export=download&id=1KKMmH10hPuqEc3-X8uAa7BLqlz5TzMdn"
URL_TELUGU = "https://drive.google.com/uc?export=download&id=18nSmhQKoV-Epc-e2qX9kvJyZkZaFB_X1"

st.set_page_config(page_title="Vizag Cyclone Command", layout="wide")

# ==========================================
# 🔮 MODEL LOADING (FIXES SKLEARN ERROR)
# ==========================================
@st.cache_resource
def load_prediction_model():
    if not os.path.exists(MODEL_FILE):
        return None
    try:
        # Requires scikit-learn in requirements.txt
        return joblib.load(MODEL_FILE)
    except Exception:
        return None

model = load_prediction_model()

# ==========================================
# 🆘 SOS CALL FUNCTION (DUAL FAILOVER)
# ==========================================
def trigger_sos_call(target_phone, lang):
    audio_url = URL_TELUGU if lang == "Telugu" else URL_ENGLISH
    twiml = f'<Response><Play>{audio_url}</Play></Response>'
    
    accounts = [
        {"sid": TWILIO_SID_1, "token": TWILIO_AUTH_1, "from": TWILIO_PHONE_1},
        {"sid": TWILIO_SID_2, "token": TWILIO_AUTH_2, "from": TWILIO_PHONE_2}
    ]
    
    last_err = ""
    for idx, acc in enumerate(accounts):
        try:
            client = Client(acc["sid"], acc["token"])
            client.calls.create(twiml=twiml, to=target_phone, from_=acc["from"])
            return f"SUCCESS (Account {idx+1})"
        except Exception as e:
            last_err = str(e)
            continue
    return f"Failed: {last_err}"

# ==========================================
# 📊 UI DASHBOARD
# ==========================================
st.title("🌪️ Vizag Cyclone Command Center")

with st.sidebar:
    st.header("🚨 Emergency SOS")
    p1 = st.text_input("Primary Contact", "+917678495189")
    p2 = st.text_input("Family Contact", "+918130631551")
    
    st.divider()
    lang = st.radio("Call Audio Language", ["English", "Telugu"])
    
    if st.button("🚨 TRIGGER SOS CALLS", type="primary", use_container_width=True):
        for phone in [p1, p2]:
            if len(phone) > 10:
                with st.spinner(f"Calling {phone}..."):
                    status = trigger_sos_call(phone, lang)
                    if "SUCCESS" in status:
                        st.success(f"✅ {phone}: {status}")
                    else:
                        st.error(f"❌ {phone}: {status}")

# Prediction & Map Display
c1, c2 = st.columns([1, 2])
with c1:
    if model:
        st.success("🤖 Prediction Model Online")
    else:
        st.warning("⚠️ Prediction Offline (Check requirements.txt)")
    
    st.metric("Region", "Visakhapatnam")
    st.info("Direct MP3 SOS Links Integrated.")

with c2:
    m = folium.Map(location=[17.68, 83.21], zoom_start=11)
    folium.Circle([17.68, 83.21], radius=15000, color='red', fill=True).add_to(m)
    st_folium(m, height=450, use_container_width=True)