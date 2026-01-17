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
        "AUTH": "3cb1dfcb6a9a3cae88f4eff47e9458df",
        "PHONE": "+15075195618"
    },
    "Backup": {
        "SID": "ACa12e602647785572ebaf765659d26d23",
        "AUTH": "6460cb8dfe71e335741bb20bc14c452a",
        "PHONE": "+14176076960"
    }
}

# Mapping uploaded files for local playback and URLs for Twilio
VOICE_MAP = {
    "📢 Regional Broadcast (English)": {
        "file": "alert_detailed.mp3",
        "url": "https://drive.google.com/uc?export=download&id=1CWswvjAoIAO7h6C6Jh-uCsrOWFM7dnS_"
    },
    "🇮🇳 Emergency Alert (Telugu)": {
        "file": "alert_telugu_final.mp3",
        "url": "https://drive.google.com/uc?export=download&id=15xz_g_TvMAF2Icjesi3FyMV6MMS-RZHt"
    }
}

st.set_page_config(page_title=CONFIG["APP_TITLE"], page_icon="🌪️", layout="wide")

# ==============================================================================
# MODULE 2: VOICE & DISPATCH ENGINE
# ==============================================================================
def play_voice_local(file_path, autoplay=False):
    """Plays the uploaded mp3 files in the dashboard browser."""
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            st.audio(f.read(), format="audio/mp3", autoplay=autoplay)
    else:
        st.error(f"❌ Audio file {file_path} not found in directory.")

def trigger_twilio_call(to_number, audio_url, account_key="Primary"):
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
# MODULE 4: UI TABS (AS BEFORE)
# ==============================================================================
st.title(f"🌪️ {CONFIG['APP_TITLE']}")

with st.sidebar:
    st.header("🎙️ Voice Dispatch Center")
    selected_voice_label = st.selectbox("Select Language Alert", list(VOICE_MAP.keys()))
    
    # Sidebar manual playback
    if st.button("🔊 Preview Voice locally"):
        play_voice_local(VOICE_MAP[selected_voice_label]["file"])
    
    st.divider()
    account_choice = st.radio("Twilio Route", ["Primary", "Backup"])

tab_live, tab_sim, tab_ops = st.tabs(["📡 Live Data Monitor", "🧪 Storm Simulation", "🚨 Emergency Ops"])

# --- LIVE MONITOR ---
with tab_live:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Live Pressure", f"{pres} hPa")
        st.metric("Current Region", loc_name)
        # Condition-based autoplay
        if pres < 1000:
            st.error("🚨 HIGH RISK DETECTED")
            play_voice_local(VOICE_MAP["📢 Regional Broadcast (English)"]["file"], autoplay=True)

    with col2:
        m = folium.Map(location=[lat, lon], zoom_start=11)
        folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                         attr='Esri', name='Satellite').add_to(m)
        st_folium(m, height=450, use_container_width=True)

# --- EMERGENCY OPS (COMBINED VOICE SYSTEM) ---
with tab_ops:
    st.header("🚨 AI Voice Call Dispatch")
    st.write("Triggering this will play the audio on your dashboard and call the recipient.")
    
    recipient = st.text_input("Recipient Phone Number (+91...)", placeholder="+91XXXXXXXXXX")
    
    if st.button("📞 Dispatch Simultaneous AI Alerts", type="primary"):
        if recipient:
            with st.spinner("Executing combined dispatch..."):
                # 1. Play locally for operator
                play_voice_local(VOICE_MAP[selected_voice_label]["file"], autoplay=True)
                
                # 2. Trigger remote Twilio call
                success, result = trigger_twilio_call(recipient, VOICE_MAP[selected_voice_label]["url"], account_choice)
                
                if success:
                    st.success(f"✅ Call Initiated! SID: {result}")
                else:
                    st.error(f"❌ Call Failed: {result}")
        else:
            st.warning("Please enter a valid phone number.")

# --- SIMULATION ---
with tab_sim:
    s_pres = st.slider("Simulate Low Pressure", 880, 1030, 980)
    st.metric("Simulated Severity", "High" if s_pres < 990 else "Normal")