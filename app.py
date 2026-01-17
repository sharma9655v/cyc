import streamlit as st
import joblib
import numpy as np
import os
import requests
import folium
from streamlit_folium import st_folium
from twilio.rest import Client #

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
        "AUTH": "b9664b1b9fec1c6ab71cb83d4dd8fede",
        "PHONE": "+15075195618"
    },
    "Backup": {
        "SID": "ACa12e602647785572ebaf765659d26d23",
        "AUTH": "9ddfac5b5499f2093b49c82c397380ca",
        "PHONE": "+14176076960"
    }
}

# Twilio URLs remain for the remote AI voice call
VOICE_URLS = {
    "📢 Regional Broadcast (English)": "https://drive.google.com/uc?export=download&id=1CWswvjAoIAO7h6C6Jh-uCsrOWFM7dnS_",
    "🇮🇳 Emergency Alert (Telugu)": "https://drive.google.com/uc?export=download&id=15xz_g_TvMAF2Icjesi3FyMV6MMS-RZHt"
}

st.set_page_config(page_title=CONFIG["APP_TITLE"], page_icon="🌪️", layout="wide")

# ==============================================================================
# MODULE 2: TWILIO CALL ENGINE
# ==============================================================================
def make_ai_voice_call(to_number, audio_url, account_key="Primary"):
    """Triggers the remote AI voice call via Twilio."""
    try:
        acc = TWILIO_ACCOUNTS[account_key]
        client = Client(acc["SID"], acc["AUTH"])
        twiml = f'<Response><Play>{audio_url}</Play></Response>'
        call = client.calls.create(twiml=twiml, to=to_number, from_=acc["PHONE"])
        return True, call.sid
    except Exception as e:
        return False, str(e)

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

# ==============================================================================
# MODULE 4: UI TABS
# ==============================================================================
st.title(f"🌪️ {CONFIG['APP_TITLE']}")

with st.sidebar:
    st.header("⚙️ Dispatch Settings")
    selected_voice_label = st.selectbox("Select AI Voice Language", list(VOICE_URLS.keys()))
    
    # Audio players removed from here
    st.divider()
    account_choice = st.radio("Twilio Account", ["Primary", "Backup"])

tab_live, tab_sim, tab_ops = st.tabs(["📡 Live Data Monitor", "🧪 Storm Simulation", "🚨 Emergency Ops"])

# --- LIVE MONITOR ---
with tab_live:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Live Pressure", f"{pres} hPa")
        st.metric("Region", loc_name)
        if pres < 1000:
            st.error("🚨 ALERT: Cyclone risk detected.")

    with col2:
        m = folium.Map(location=[lat, lon], zoom_start=11)
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri', name='Satellite'
        ).add_to(m)
        
        folium.Marker(
            [lat, lon], 
            popup="Visakhapatnam Command Center",
            icon=folium.Icon(color='red', icon='warning', prefix='fa')
        ).add_to(m)

        st_folium(m, height=500, use_container_width=True)

# --- EMERGENCY OPS ---
with tab_ops:
    st.header("🚨 AI Voice Dispatch System")
    
    # Audio players removed from here
    recipient = st.text_input("Emergency Contact Number", placeholder="+91XXXXXXXXXX")

    if st.button("📞 Initiate AI Voice Call", type="primary"):
        if recipient:
            with st.spinner("Connecting to Twilio and playing AI Voice..."):
                # System still uses the URL for the phone call
                success, result = make_ai_voice_call(
                    recipient, 
                    VOICE_URLS[selected_voice_label], 
                    account_choice
                )
                if success:
                    st.success(f"✅ Call Initiated! SID: {result}")
                else:
                    st.error(f"❌ Dispatch Failed: {result}")
        else:
            st.warning("Please provide a phone number.")

# --- SIMULATION ---
with tab_sim:
    s_pres = st.slider("Simulate Low Pressure (hPa)", 880, 1030, 1010)
    st.metric("Predicted Severity", "High" if s_pres < 995 else "Normal")