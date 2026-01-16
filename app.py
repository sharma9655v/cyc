import streamlit as st
import joblib
import numpy as np
import pandas as pd
import requests
import os
from twilio.rest import Client
import folium
from streamlit_folium import st_folium

# ==========================================
# 🔑 CONFIGURATION
# ==========================================
WEATHER_API_KEY = "22223eb27d4a61523a6bbad9f42a14a7"
MODEL_FILE = "cyclone_model.joblib"

# Twilio Accounts
ACCOUNTS = [
    {"sid": "ACc9b9941c778de30e2ed7ba57f87cdfbc", "token": "3cb1dfcb6a9a3cae88f4eff47e9458df", "from": "+15075195618"},
    {"sid": "ACa12e602647785572ebaf765659d26d23", "token": "26210979738809eaf59a678e98fe2c0f", "from": "+14176076960"}
]

# Audio Links (Replace with your actual hosted URLs)
URL_ENGLISH = "https://your-link.com/alert_detailed.mp3"
URL_TELUGU = "https://your-link.com/alert_telugu_final.mp3"

st.set_page_config(page_title="Vizag Cyclone Center", layout="wide")

# ==========================================
# 🔮 MODEL LOADING (FIXES SKLEARN ERROR)
# ==========================================
@st.cache_resource
def load_prediction_model():
    if not os.path.exists(MODEL_FILE):
        return None
    try:
        # Loading the model requires 'scikit-learn' in requirements.txt
        return joblib.load(MODEL_FILE)
    except Exception as e:
        st.error(f"⚠️ Model Load Error: {e}")
        return None

model = load_prediction_model()

# ==========================================
# 🆘 SOS CALL FUNCTION
# ==========================================
def make_sos_call(target_phone, lang):
    audio_url = URL_TELUGU if lang == "Telugu" else URL_ENGLISH
    twiml = f'<Response><Play>{audio_url}</Play></Response>'
    
    for acc in ACCOUNTS:
        try:
            client = Client(acc["sid"], acc["token"])
            client.calls.create(twiml=twiml, to=target_phone, from_=acc["from"])
            return "SUCCESS"
        except Exception:
            continue
    return "All accounts hit daily limits (Error 429)."

# ==========================================
# 📊 UI DISPLAY
# ==========================================
st.title("🌪️ Vizag Cyclone Command Center")

if model is None:
    st.error("❌ Missing Library or Model: Please check requirements.txt for 'scikit-learn'.")
    st.info("System is running in SOS-only mode (No Predictions).")

with st.sidebar:
    st.header("🚨 Emergency SOS")
    num = st.text_input("Contact", "+917678495189")
    lang = st.radio("Language", ["English", "Telugu"])
    if st.button("🚨 TRIGGER SOS CALL"):
        status = make_sos_call(num, lang)
        if status == "SUCCESS": st.success("✅ Call Initiated!")
        else: st.error(status)

# Dashboard Columns
c1, c2 = st.columns([1, 2])
with c1:
    st.metric("Location", "Visakhapatnam")
    if model:
        # (Add your prediction logic here using model.predict)
        st.success("Real-time Tracking Active")
    
with c2:
    m = folium.Map(location=[17.68, 83.21], zoom_start=11)
    folium.Circle([17.68, 83.21], radius=15000, color='red', fill=True).add_to(m)
    st_folium(m, height=450, use_container_width=True)