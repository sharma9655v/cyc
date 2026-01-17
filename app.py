import streamlit as st
import joblib
import numpy as np
import os
import requests
import folium
from streamlit_folium import st_folium
from twilio.rest import Client

# ==============================================================================
# 1. CONFIGURATION & EMERGENCY CONTACTS
# ==============================================================================
CONFIG = {
    "APP_TITLE": "Vizag Cyclone Command Center",
    "API_KEY": "22223eb27d4a61523a6bbad9f42a14a7",
    "TARGET_CITY": "Visakhapatnam",
    "DEFAULT_COORDS": [17.6868, 83.2185] 
}

# Twilio Credentials
TWILIO_ACCOUNTS = {
    "Primary": {
        "SID": "ACc9b9941c778de30e2ed7ba57f87cdfbc",
        "AUTH": "15173b1522f7711143c50e5ba0369856",
        "PHONE": "+15075195618"
    }
}

# --- ADDING TWO PHONE NUMBERS HERE ---
# Ensure numbers use E.164 format: + [Country Code] [Number]
EMERGENCY_CONTACTS = [
    "+91XXXXXXXXXX",  # Primary Contact (e.g., Command Head)
    "+91YYYYYYYYYY"   # Secondary Contact (e.g., Field Supervisor)
]

VOICE_URLS = {
    "📢 Regional Broadcast (English)": "https://drive.google.com/uc?export=download&id=1CWswvjAoIAO7h6C6Jh-uCsrOWFM7dnS_",
    "🇮🇳 Emergency Alert (Telugu)": "https://drive.google.com/uc?export=download&id=15xz_g_TvMAF2Icjesi3FyMV6MMS-RZHt"
}
VOICE_FILES = {
    "📢 Regional Broadcast (English)": "alert_detailed.mp3",
    "🇮🇳 Emergency Alert (Telugu)": "alert_telugu_final.mp3"
}

st.set_page_config(page_title=CONFIG["APP_TITLE"], page_icon="🌪️", layout="wide")

# ==============================================================================
# 2. BACKEND BROADCAST ENGINE
# ==============================================================================
def broadcast_sos_to_all(message_body):
    """Loops through the contact list and sends SMS to everyone."""
    try:
        acc = TWILIO_ACCOUNTS["Primary"]
        client = Client(acc["SID"], acc["AUTH"])
        
        # This loop ensures both numbers receive the message
        for contact_number in EMERGENCY_CONTACTS:
            client.messages.create(
                body=message_body,
                from_=acc["PHONE"],
                to=contact_number
            )
        return True
    except Exception as e:
        print(f"Backend Broadcast Error: {e}")
        return False

def make_ai_voice_call(to_number, audio_url):
    """Triggers a voice call to a specific recipient."""
    try:
        acc = TWILIO_ACCOUNTS["Primary"]
        client = Client(acc["SID"], acc["AUTH"])
        twiml = f'<Response><Play>{audio_url}</Play></Response>'
        client.calls.create(twiml=twiml, to=to_number, from_=acc["PHONE"])
        return True
    except:
        return False

# ==============================================================================
# 3. LEVEL 5 RISK ENGINE
# ==============================================================================
class CycloneLevelModel:
    def predict(self, pressure):
        if pressure < 920: return 5  # Super Cyclone
        if pressure < 945: return 4  # Extremely Severe
        if pressure < 965: return 3  # Very Severe
        if pressure < 985: return 2  # Severe
        if pressure < 1005: return 1 # Cyclonic Storm
        return 0

risk_engine = CycloneLevelModel()

def fetch_weather():
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={CONFIG['TARGET_CITY']}&appid={CONFIG['API_KEY']}"
        data = requests.get(url, timeout=5).json()
        return data['coord']['lat'], data['coord']['lon'], data['main']['pressure'], data['name']
    except:
        return *CONFIG["DEFAULT_COORDS"], 1012, "Visakhapatnam (Offline)"

lat, lon, pres, loc_name = fetch_weather()
current_level = risk_engine.predict(pres)

# SILENT TRIGGER: Level 3+ triggers backend SOS to BOTH contacts
if current_level >= 3:
    if 'sos_sent' not in st.session_state:
        sos_text = f"🚨 BACKEND SOS: Level {current_level} risk at {loc_name}. Pressure: {pres}hPa."
        broadcast_sos_to_all(sos_text)
        st.session_state.sos_sent = True

# ==============================================================================
# 4. USER INTERFACE
# ==============================================================================
st.title(f"🌪️ {CONFIG['APP_TITLE']}")

with st.sidebar:
    st.header("🛡️ Control Center")
    selected_voice = st.selectbox("Select Alert Language", list(VOICE_URLS.keys()))
    
    st.divider()
    st.subheader("🎙️ Voice Preview")
    if os.path.exists(VOICE_FILES[selected_voice]):
        with open(VOICE_FILES[selected_voice], "rb") as f:
            st.audio(f.read(), format="audio/mp3")

tab_live, tab_sim, tab_ops = st.tabs(["📡 Live Monitor", "🧪 Simulation", "🚨 Emergency Ops"])

with tab_live:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Barometric Pressure", f"{pres} hPa")
        st.metric("Intensity Level", f"Level {current_level}/5")
        
        if current_level >= 3:
            st.error(f"⚠️ MAJOR ALERT: High risk detected. Backend alerts sent to {len(EMERGENCY_CONTACTS)} contacts.")

    with col2:
        m = folium.Map(location=[lat, lon], zoom_start=11)
        folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri', name='Satellite').add_to(m)
        colors = ["blue", "green", "orange", "red", "darkred", "black"]
        folium.Marker([lat, lon], icon=folium.Icon(color=colors[current_level], icon='warning')).add_to(m)
        st_folium(m, height=450, use_container_width=True)

with tab_ops:
    st.header("🚨 Administrative Commands")
    st.info(f"The SOS Broadcast will notify: {', '.join(EMERGENCY_CONTACTS)}")
    
    if st.button("📢 Manual Broadcast SOS to All Contacts", type="primary"):
        manual_msg = f"MANUAL ALERT: Emergency protocol activated for {loc_name}. Current Pressure: {pres} hPa."
        if broadcast_sos_to_all(manual_msg):
            st.success("SOS Message sent successfully to all recipients.")
        else:
            st.error("Broadcast failed. Check terminal logs.")

    st.divider()
    st.subheader("📞 Specific Voice Dispatch")
    target_num = st.text_input("Enter number for AI Call", placeholder="+91...")
    if st.button("Start AI Voice Call"):
        if target_num and make_ai_voice_call(target_num, VOICE_URLS[selected_voice]):
            st.success(f"Voice call initiated to {target_num}")