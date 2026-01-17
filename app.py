import streamlit as st
import joblib
import numpy as np
import os
import requests
import folium
from streamlit_folium import st_folium
from twilio.rest import Client

# ==============================================================================
# MODULE 1: CONFIGURATION & CREDENTIALS
# ==============================================================================
CONFIG = {
    "APP_TITLE": "Vizag Cyclone Command Center",
    "API_KEY": "22223eb27d4a61523a6bbad9f42a14a7",
    "MODEL_PATH": "cyclone_model.joblib",
    "TARGET_CITY": "Visakhapatnam",
    "DEFAULT_COORDS": [17.6868, 83.2185] 
}

TWILIO_ACCOUNTS = {
    "Primary": {
        "SID": "ACc9b9941c778de30e2ed7ba57f87cdfbc",
        "AUTH": "15173b1522f7711143c50e5ba0369856",
        "PHONE": "+15075195618"
    }
}

# The emergency contacts who receive the silent backend alerts
SOS_CONTACTS = ["+91XXXXXXXXXX"] 

VOICE_URLS = {
    "📢 Regional Broadcast (English)": "https://drive.google.com/uc?export=download&id=1CWswvjAoIAO7h6C6Jh-uCsrOWFM7dnS_",
    "🇮🇳 Emergency Alert (Telugu)": "https://drive.google.com/uc?export=download&id=15xz_g_TvMAF2Icjesi3FyMV6MMS-RZHt"
}

st.set_page_config(page_title=CONFIG["APP_TITLE"], page_icon="🌪️", layout="wide")

# ==============================================================================
# MODULE 2: SILENT BACKEND ENGINE
# ==============================================================================
def backend_sos_broadcast(message_body):
    """Executes SOS alerts silently in the backend without showing UI logs."""
    try:
        acc = TWILIO_ACCOUNTS["Primary"]
        client = Client(acc["SID"], acc["AUTH"])
        for number in SOS_CONTACTS:
            # Silent execution: No st.write or st.success here
            client.messages.create(body=message_body, from_=acc["PHONE"], to=number)
        return True
    except:
        return False # Fails silently to prevent crashing the UI

def make_ai_voice_call(to_number, audio_url):
    """Triggered by user; UI feedback is allowed here."""
    try:
        acc = TWILIO_ACCOUNTS["Primary"]
        client = Client(acc["SID"], acc["AUTH"])
        twiml = f'<Response><Play>{audio_url}</Play></Response>'
        client.calls.create(twiml=twiml, to=to_number, from_=acc["PHONE"])
        return True
    except:
        return False

# ==============================================================================
# MODULE 3: DATA ENGINE
# ==============================================================================
def get_weather(city):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={CONFIG['API_KEY']}"
        r = requests.get(url, timeout=5).json()
        return r['coord']['lat'], r['coord']['lon'], r['main']['pressure'], r['name']
    except:
        return *CONFIG["DEFAULT_COORDS"], 1012, "Default (Simulated)"

lat, lon, pres, loc_name = get_weather(CONFIG["TARGET_CITY"])

# --- SILENT AUTOMATED TRIGGER ---
# This runs every time the page loads but never shows anything to the user.
if pres < 1000:
    if 'auto_sos_sent' not in st.session_state:
        alert_body = f"BACKEND ALERT: Pressure at {pres} hPa in {loc_name}. Risk detected."
        backend_sos_broadcast(alert_body)
        st.session_state.auto_sos_sent = True

# ==============================================================================
# MODULE 4: CLEAN UI LAYOUT
# ==============================================================================
st.title(f"🌪️ {CONFIG['APP_TITLE']}")

tab_live, tab_sim, tab_ops = st.tabs(["📡 Live Data Monitor", "🧪 Storm Simulation", "🚨 Emergency Ops"])

with tab_live:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Live Pressure", f"{pres} hPa")
        st.metric("Region", loc_name)
        # We removed the st.error red box so users don't see the alert trigger.

    with col2:
        m = folium.Map(location=[lat, lon], zoom_start=11)
        folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri', name='Satellite').add_to(m)
        st_folium(m, height=500, use_container_width=True)

with tab_ops:
    st.header("🚨 Administrative Dispatch")
    recipient = st.text_input("Contact Number", placeholder="+91XXXXXXXXXX")
    selected_voice = st.selectbox("Select Voice", list(VOICE_URLS.keys()))

    if st.button("📞 Start AI Voice Dispatch"):
        if make_ai_voice_call(recipient, VOICE_URLS[selected_voice]):
            st.success("Dispatch command sent.")