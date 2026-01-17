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

EMERGENCY_CONTACTS = ["+91XXXXXXXXXX", "+91YYYYYYYYYY"]

VOICE_URLS = {
    "📢 Regional Broadcast (English)": "https://drive.google.com/uc?export=download&id=1CWswvjAoIAO7h6C6Jh-uCsrOWFM7dnS_",
    "🇮🇳 Emergency Alert (Telugu)": "https://drive.google.com/uc?export=download&id=15xz_g_TvMAF2Icjesi3FyMV6MMS-RZHt"
}

st.set_page_config(page_title=CONFIG["APP_TITLE"], page_icon="🌪️", layout="wide")

# ==============================================================================
# MODULE 2: BACKEND ENGINES
# ==============================================================================
def silent_backend_sos(message_body):
    try:
        acc = TWILIO_ACCOUNTS["Primary"]
        client = Client(acc["SID"], acc["AUTH"])
        for number in EMERGENCY_CONTACTS:
            client.messages.create(body=message_body, from_=acc["PHONE"], to=number)
        return True
    except:
        return False

def make_ai_voice_call(to_number, audio_url):
    try:
        acc = TWILIO_ACCOUNTS["Primary"]
        client = Client(acc["SID"], acc["AUTH"])
        twiml = f'<Response><Play>{audio_url}</Play></Response>'
        client.calls.create(twiml=twiml, to=to_number, from_=acc["PHONE"])
        return True
    except:
        return False

# ==============================================================================
# MODULE 3: UPDATED 5-LEVEL RISK ENGINE
# ==============================================================================
class PhysicsFallbackModel:
    def predict(self, X):
        pressure = X[0][2]
        if pressure < 920: return np.array([5]) # Super Cyclone
        if pressure < 940: return np.array([4]) # Extremely Severe
        if pressure < 960: return np.array([3]) # Very Severe
        if pressure < 980: return np.array([2]) # Severe Cyclone
        if pressure < 1000: return np.array([1]) # Cyclonic Storm
        return np.array([0]) # Normal

@st.cache_resource
def load_cyclone_engine():
    if not os.path.exists(CONFIG["MODEL_PATH"]):
        return PhysicsFallbackModel(), True
    try:
        model = joblib.load(CONFIG["MODEL_PATH"])
        return model, False
    except:
        return PhysicsFallbackModel(), True

model_engine, is_fallback = load_cyclone_engine()

def get_weather(city):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={CONFIG['API_KEY']}"
        r = requests.get(url, timeout=5).json()
        return r['coord']['lat'], r['coord']['lon'], r['main']['pressure'], r['name']
    except:
        return *CONFIG["DEFAULT_COORDS"], 1012, "Default (Simulated)"

# Logic Calculations
lat, lon, pres, loc_name = get_weather(CONFIG["TARGET_CITY"])
risk_level = int(model_engine.predict([[lat, lon, pres]])[0])

# SILENT SOS TRIGGER (Levels 3, 4, and 5)
if risk_level >= 3:
    if 'auto_sos_sent' not in st.session_state:
        alert_body = f"CRITICAL: Level {risk_level} Cyclone Risk in {loc_name}. Pressure: {pres} hPa."
        silent_backend_sos(alert_body)
        st.session_state.auto_sos_sent = True

# ==============================================================================
# MODULE 4: UI LAYOUT
# ==============================================================================
st.title(f"🌪️ {CONFIG['APP_TITLE']}")

with st.sidebar:
    st.header("⚙️ Dispatch Settings")
    selected_voice = st.selectbox("Select AI Voice Language", list(VOICE_URLS.keys()))
    
    st.divider()
    st.subheader("📊 Severity Guide")
    st.write("**L1:** Storm | **L2:** Severe")
    st.write("**L3:** Very Severe | **L4:** Extreme")
    st.error("**L5: Super Cyclone**")

tab_live, tab_sim, tab_ops = st.tabs(["📡 Live Data Monitor", "🧪 Storm Simulation", "🚨 Emergency Ops"])

# --- LIVE MONITOR ---
with tab_live:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Live Pressure", f"{pres} hPa")
        st.metric("Risk Level", f"Level {risk_level}")
        
        # UI Alerts based on Level 5 scale
        if risk_level == 5:
            st.warning("🚨 SUPER CYCLONE DETECTED (Level 5)")
        elif risk_level >= 3:
            st.error(f"⚠️ MAJOR RISK: LEVEL {risk_level}")

    with col2:
        m = folium.Map(location=[lat, lon], zoom_start=11)
        folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri', name='Satellite').add_to(m)
        
        # Color code markers by risk
        marker_color = 'darkred' if risk_level >= 4 else 'red' if risk_level >= 2 else 'blue'
        folium.Marker([lat, lon], icon=folium.Icon(color=marker_color, icon='warning', prefix='fa')).add_to(m)
        
        st_folium(m, height=500, use_container_width=True)

# --- EMERGENCY OPS ---
with tab_ops:
    st.header("🚨 AI Voice Dispatch")
    recipient = st.text_input("Target Number", placeholder="+91XXXXXXXXXX")
    if st.button("📞 Start AI Voice Call", type="primary"):
        make_ai_voice_call(recipient, VOICE_URLS[selected_voice])

# --- SIMULATION (5-Level Testing) ---
with tab_sim:
    s_pres = st.slider("Simulate Extreme Pressure (hPa)", 880, 1030, 950)
    s_risk = int(model_engine.predict([[lat, lon, s_pres]])[0])
    
    st.subheader(f"Simulated Status: Level {s_risk}")
    st.progress(min(s_risk/5, 1.0)) # Scaled to Level 5