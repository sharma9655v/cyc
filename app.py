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

# AI Voice Assets (Converted for Twilio & Local Playback)
VOICE_MAP = {
    "📢 Regional Broadcast (English)": "https://drive.google.com/uc?export=download&id=1CWswvjAoIAO7h6C6Jh-uCsrOWFM7dnS_",
    "🇮🇳 Emergency Alert (Telugu)": "https://drive.google.com/uc?export=download&id=15xz_g_TvMAF2Icjesi3FyMV6MMS-RZHt"
}

st.set_page_config(page_title=CONFIG["APP_TITLE"], page_icon="🌪️", layout="wide")

# ==============================================================================
# MODULE 2: SIMULTANEOUS DISPATCH LOGIC
# ==============================================================================
def trigger_voice_call(to_number, audio_url, account_key="Primary"):
    """Triggers remote call via Twilio and local audio in dashboard."""
    try:
        # 1. Trigger Remote AI Voice (Twilio)
        acc = TWILIO_ACCOUNTS[account_key]
        client = Client(acc["SID"], acc["AUTH"])
        twiml_content = f'<Response><Play>{audio_url}</Play></Response>'
        
        call = client.calls.create(
            twiml=twiml_content,
            to=to_number,
            from_=acc["PHONE"]
        )
        
        # 2. Trigger Local AI Voice (Dashboard)
        st.audio(audio_url, format="audio/mp3", autoplay=True)
        
        return True, call.sid
    except Exception as e:
        return False, str(e)

# (Module 3: Cyclone Engine remains the same as previous version)
# ==============================================================================
# MODULE 4: DASHBOARD UI
# ==============================================================================
st.title(f"🌪️ {CONFIG['APP_TITLE']}")

# Real-time Logic
lat, lon, pres, loc_name = [17.6868, 83.2185, 1012, "Visakhapatnam"] # Placeholder logic
risk_level = 2 # Example severity

with st.sidebar:
    st.header("🎙️ Voice Dispatch Center")
    selected_voice = st.selectbox("Select Language Alert", list(VOICE_MAP.keys()))
    account_choice = st.radio("Twilio Account", ["Primary", "Backup"])

tab_live, tab_sim, tab_ops = st.tabs(["📡 Live Data Monitor", "🧪 Storm Simulation", "🚨 Emergency Ops"])

# --- EMERGENCY OPS (SIMULTANEOUS DISPATCH) ---
with tab_ops:
    st.header("🚨 AI Voice Call & Local Dispatch")
    st.write("Clicking the button below triggers the AI voice alert locally and via Twilio.")
    
    col_left, col_right = st.columns(2)
    with col_left:
        recipient = st.text_input("Recipient Phone Number", placeholder="+91XXXXXXXXXX")
    
    if st.button("📞 Dispatch Simultaneous Alerts", type="primary"):
        if recipient:
            with st.spinner("Dispatching..."):
                success, result = trigger_voice_call(recipient, VOICE_MAP[selected_voice], account_choice)
                if success:
                    st.success(f"✅ Alert dispatched! Twilio SID: {result}")
                    st.info("🔊 Local audio playing in dashboard...")
                else:
                    st.error(f"❌ Failed: {result}")
        else:
            st.warning("Please enter a phone number.")

# --- SATELLITE MAP (LEFT SIDE VOICE OVER MONITOR) ---
with tab_live:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Live Pressure", f"{pres} hPa")
        if risk_level >= 2:
            st.error("🚨 EMERGENCY LEVEL REACHED")
            # Auto-plays English alert for the monitoring user
            st.audio(VOICE_MAP["📢 Regional Broadcast (English)"], autoplay=True)

    with c2:
        m = folium.Map(location=[lat, lon], zoom_start=10)
        folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                         attr='Esri', name='Satellite').add_to(m)
        st_folium(m, height=400, use_container_width=True)