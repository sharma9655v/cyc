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

# ==============================================================================
# 2. UTILITY FUNCTIONS
# ==============================================================================
def broadcast_sos_to_contacts(message_body, account_choice):
    try:
        acc = TWILIO_ACCOUNTS[account_choice]
        client = Client(acc["SID"], acc["AUTH"])
        for number in EMERGENCY_CONTACTS:
            client.messages.create(body=message_body, from_=acc["PHONE"], to=number)
        return True
    except: return False

def trigger_ai_call(to_number, audio_url, account_choice):
    try:
        acc = TWILIO_ACCOUNTS[account_choice]
        client = Client(acc["SID"], acc["AUTH"])
        twiml = f'<Response><Play>{audio_url}</Play></Response>'
        client.calls.create(twiml=twiml, to=to_number, from_=acc["PHONE"])
        return True
    except: return False

def calculate_risk_level(pressure):
    if pressure < 920: return 5, "Super Cyclone", "Critical"
    if pressure < 945: return 4, "Extremely Severe", "Severe"
    if pressure < 965: return 3, "Very Severe", "High"
    if pressure < 985: return 2, "Severe", "Moderate"
    if pressure < 1005: return 1, "Cyclonic Storm", "Low"
    return 0, "Normal", "None"

def fetch_weather():
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={CONFIG['TARGET_CITY']}&appid={CONFIG['API_KEY']}"
        data = requests.get(url, timeout=5).json()
        return data['coord']['lat'], data['coord']['lon'], data['main']['pressure'], data['name']
    except:
        return *CONFIG["DEFAULT_COORDS"], 1012, "Visakhapatnam (Default)"

# --- DATA FETCH ---
lat, lon, pres, loc_name = fetch_weather()
risk_lvl, risk_name, risk_desc = calculate_risk_level(pres)

# ==============================================================================
# 3. UI LAYOUT
# ==============================================================================
st.title(f"🌪️ {CONFIG['APP_TITLE']}")

with st.sidebar:
    st.header("⚙️ Dispatch Control")
    selected_voice = st.selectbox("Select Alert Language", list(VOICE_ASSETS.keys()))
    account_choice = st.radio("Active Twilio Account", ["Primary", "Backup"])
    st.divider()
    st.subheader("🎙️ Voice Preview")
    if os.path.exists(VOICE_ASSETS[selected_voice]["local"]):
        with open(VOICE_ASSETS[selected_voice]["local"], "rb") as f:
            st.audio(f.read(), format="audio/mp3")

tab_live, tab_sim, tab_ops = st.tabs(["📡 Live Data Monitor", "🧪 Storm Simulation", "🚨 Emergency Ops"])

# --- LIVE MONITOR ---
with tab_live:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Barometric Pressure", f"{pres} hPa")
        st.metric("Risk Status", risk_name)
        if risk_lvl >= 3:
            st.error(f"⚠️ LEVEL {risk_lvl} ALERT ACTIVE")
    with c2:
        m = folium.Map(location=[lat, lon], zoom_start=11)
        folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
        colors = ["blue", "green", "orange", "red", "darkred", "black"]
        folium.Marker([lat, lon], icon=folium.Icon(color=colors[risk_lvl])).add_to(m)
        st_folium(m, height=450, use_container_width=True)

# --- NEW: ENHANCED STORM SIMULATION ---
with tab_sim:
    st.header("🧪 Storm Impact Simulation")
    st.write("Adjust the pressure to forecast potential damage and wind speeds.")
    
    sim_p = st.slider("Simulate Surface Pressure (hPa)", 880, 1030, 975)
    s_lvl, s_name, _ = calculate_risk_level(sim_p)
    
    # Mathematical approximation of wind speed based on pressure drop
    # Approx: Wind Speed (knots) = 3.9 * sqrt(1013 - Pressure) [Image of wind speed vs pressure chart]
    est_wind = round(3.9 * ((1013 - sim_p)**0.5) * 1.852, 1) if sim_p < 1013 else 0

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Simulated Level", f"Level {s_lvl}")
    col_b.metric("Category", s_name)
    col_c.metric("Est. Wind Speed", f"{est_wind} km/h")

    st.divider()
    
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.subheader("🏚️ Expected Damage Assessment")
        damage_map = {
            0: "No damage expected. Conditions are stable.",
            1: "Damage to thatched huts, breaking of tree branches.",
            2: "Major damage to kutcha houses, uprooting of power poles.",
            3: "Extensive damage to kucha houses, some damage to old buildings.",
            4: "Large-scale uprooting of trees, communication network collapse.",
            5: "Catastrophic damage to all structures. Total evacuation required."
        }
        st.info(damage_map[s_lvl])

    with res_col2:
        st.subheader("🛡️ Safety & Precautionary Guide")
        guide_map = {
            0: "Routine monitoring only.",
            1: "Fishermen advised not to venture into sea.",
            2: "Secure loose objects. Move to sturdy buildings.",
            3: "Evacuate low-lying areas. Stockpile 3 days of food/water.",
            4: "Mandatory evacuation of coastal zones. Power shutdown likely.",
            5: "SUPER CYCLONE: Immediate inland migration. Total blackout."
        }
        st.warning(guide_map[s_lvl])

    st.progress(s_lvl / 5.0)

# --- EMERGENCY OPS ---
with tab_ops:
    st.header("🚨 Command Dispatch")
    if st.button("📢 Broadcast SOS to All Contacts", type="primary"):
        if broadcast_sos_to_contacts(f"SOS: Level {risk_lvl} {risk_name} Alert.", account_choice):
            st.success("Sent to all recipients.")
    st.divider()
    num = st.text_input("Manual Call Number", placeholder="+91...")
    if st.button("Start AI Voice Call"):
        trigger_ai_call(num, VOICE_ASSETS[selected_voice]["url"], account_choice)