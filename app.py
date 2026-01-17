import streamlit as st
import joblib
import numpy as np
import os
import requests
import folium
from streamlit_folium import st_folium
from twilio.rest import Client

# ==============================================================================
# 1. CONFIGURATION & DUAL TWILIO ACCOUNTS
# ==============================================================================
CONFIG = {
    "APP_TITLE": "Vizag Cyclone Command Center",
    "API_KEY": "22223eb27d4a61523a6bbad9f42a14a7",
    "TARGET_CITY": "Visakhapatnam",
    "DEFAULT_COORDS": [17.6868, 83.2185] 
}

# --- BOTH TWILIO ACCOUNTS INTEGRATED ---
TWILIO_ACCOUNTS = {
    "Primary": {
        "SID": "ACc9b9941c778de30e2ed7ba57f87cdfbc",
        "AUTH": "15173b1522f7711143c50e5ba0369856",
        "PHONE": "+15075195618"
    },
    "Backup": {
        "SID": "ACa12e602647785572ebaf765659d26d23",
        "AUTH": "9ddfac5b5499f2093b49c82c397380ca",
        "PHONE": "+14176076960"
    }
}

# Dual contacts for SOS alerts
EMERGENCY_CONTACTS = ["+91XXXXXXXXXX", "+91YYYYYYYYYY"]

VOICE_ASSETS = {
    "📢 Regional Broadcast (English)": {
        "url": "https://drive.google.com/uc?export=download&id=1CWswvjAoIAO7h6C6Jh-uCsrOWFM7dnS_",
        "local": "alert_detailed.mp3"
    },
    "🇮🇳 Emergency Alert (Telugu)": {
        "url": "https://drive.google.com/uc?export=download&id=15xz_g_TvMAF2Icjesi3FyMV6MMS-RZHt",
        "local": "alert_telugu_final.mp3"
    }
}

st.set_page_config(page_title=CONFIG["APP_TITLE"], page_icon="🌪️", layout="wide")

# Custom UI Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4259; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. REDUNDANT BACKEND ENGINES (Dual Account Support)
# ==============================================================================
def broadcast_sos_to_contacts(message_body, account_choice):
    """Sends SMS using the selected Twilio account."""
    try:
        acc = TWILIO_ACCOUNTS[account_choice]
        client = Client(acc["SID"], acc["AUTH"])
        for number in EMERGENCY_CONTACTS:
            client.messages.create(body=message_body, from_=acc["PHONE"], to=number)
        return True
    except Exception as e:
        print(f"Twilio Error ({account_choice}): {e}")
        return False

def trigger_ai_call(to_number, audio_url, account_choice):
    """Initiates a phone call using the selected Twilio account."""
    try:
        acc = TWILIO_ACCOUNTS[account_choice]
        client = Client(acc["SID"], acc["AUTH"])
        twiml = f'<Response><Play>{audio_url}</Play></Response>'
        client.calls.create(twiml=twiml, to=to_number, from_=acc["PHONE"])
        return True
    except Exception as e:
        print(f"Twilio Call Error ({account_choice}): {e}")
        return False

# ==============================================================================
# 3. LEVEL 5 RISK ENGINE & WEATHER DATA
# ==============================================================================
def calculate_risk_level(pressure):
    if pressure < 920: return 5  # Super Cyclone
    if pressure < 945: return 4  
    if pressure < 965: return 3  
    if pressure < 985: return 2  
    if pressure < 1005: return 1 
    return 0

def fetch_weather():
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={CONFIG['TARGET_CITY']}&appid={CONFIG['API_KEY']}"
        data = requests.get(url, timeout=5).json()
        return data['coord']['lat'], data['coord']['lon'], data['main']['pressure'], data['name']
    except:
        return *CONFIG["DEFAULT_COORDS"], 1012, "Visakhapatnam (Default)"

lat, lon, pres, loc_name = fetch_weather()
risk_level = calculate_risk_level(pres)

# ==============================================================================
# 4. USER INTERFACE
# ==============================================================================
st.title(f"🌪️ {CONFIG['APP_TITLE']}")

with st.sidebar:
    st.header("⚙️ Dispatch Control")
    selected_voice = st.selectbox("Select AI Alert Language", list(VOICE_ASSETS.keys()))
    
    # --- DUAL ACCOUNT SELECTION ---
    st.divider()
    st.subheader("🔑 Twilio Routing")
    account_choice = st.radio("Active Twilio Account", ["Primary", "Backup"], help="Select Backup if Primary account fails.")
    
    st.divider()
    st.subheader("🎙️ Local Voice Preview")
    local_path = VOICE_ASSETS[selected_voice]["local"]
    if os.path.exists(local_path):
        with open(local_path, "rb") as f:
            st.audio(f.read(), format="audio/mp3")

# --- BACKEND AUTOMATION ---
if risk_level >= 3 and 'sos_sent' not in st.session_state:
    sos_msg = f"🚨 ALERT: Level {risk_level} Risk in {loc_name}. Pressure: {pres} hPa."
    broadcast_sos_to_contacts(sos_msg, account_choice)
    st.session_state.sos_sent = True

tab_live, tab_sim, tab_ops = st.tabs(["📡 Live Data Monitor", "🧪 Storm Simulation", "🚨 Emergency Ops"])

# --- LIVE MONITOR ---
with tab_live:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Barometric Pressure", f"{pres} hPa")
        st.metric("Intensity Level", f"Level {risk_level}/5")
        if risk_level >= 3:
            st.error(f"⚠️ CRITICAL RISK: SOS dispatched via {account_choice} account.")

    with col2:
        m = folium.Map(location=[lat, lon], zoom_start=11)
        folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri', name='Satellite').add_to(m)
        colors = ["blue", "green", "orange", "red", "darkred", "black"]
        folium.Marker([lat, lon], icon=folium.Icon(color=colors[risk_level], icon='warning')).add_to(m)
        st_folium(m, height=450, use_container_width=True)

# --- EMERGENCY OPS ---
with tab_ops:
    st.header("🚨 Command Dispatch")
    st.info(f"Currently Routing through: **{account_choice} Account**")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📢 Broadcast SOS")
        if st.button("Broadcast to All Contacts", type="primary"):
            if broadcast_sos_to_contacts("MANUAL ALERT: Emergency Protocol Activated.", account_choice):
                st.success(f"✅ Sent via {account_choice} SID.")
            else:
                st.error("❌ Broadcast failed. Try switching accounts in the sidebar.")
                
    with c2:
        st.subheader("📞 Specific Call")
        target = st.text_input("Mobile Number", placeholder="+91...")
        if st.button("Start AI Voice Call"):
            if trigger_ai_call(target, VOICE_ASSETS[selected_voice]["url"], account_choice):
                st.success("✅ Call Initiated.")
            else:
                st.warning("❌ Call failed.")