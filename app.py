import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timezone, timedelta
import random
import urllib.request
import urllib.parse
import json
import os
import sys
import platform
import io as _io

from report_engine import generate_pdf
from email_sender import send_pdf_email
from auth import register_user, login_user, social_login
from satellite_data import (
    SATELLITE_CATALOG, fetch_tle, compute_position,
    build_telemetry_40ch, compute_ground_track,
)

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Satellite Telemetry System — V5950",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Session State Defaults ─────────────────────────────────────────────────────
for key, default in {
    "station_locked": False,
    "sub_district": "ห้วยขวาง",
    "district": "ห้วยขวาง",
    "province": "กรุงเทพฯ",
    "zip_code": "10310",
    "country": "ประเทศไทย",
    "selected_satellite": "ISS (ZARYA)",
    "satellite_obj": None,
    "last_sat_name": None,
    "ref_id": "",
    "passkey": "",
    "download_ready": False,
    "station_lat": 13.75,
    "station_lon": 100.5,
    "zoom_tactical": 5,
    "zoom_global": 2,
    "zoom_station": 10,
    "zoom_globe": 2,
    "gmail_address": "",
    "gmail_app_password": "",
    "dark_mode": True,
    "telemetry_history": [],
    "tracked_satellites": [],
    "alerts_enabled": False,
    "alert_distance_km": 1000,
    "alert_log": [],
    "logged_in": False,
    "username": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─── Custom CSS + Responsive Design ─────────────────────────────────────────────
st.markdown(
    """
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
    .stApp { background-color: #0e1117; }
    .digital-clock {
        text-align: center; font-family: 'Courier New', monospace;
        font-size: 2.6rem; font-weight: 900; color: #ffffff;
        background: linear-gradient(145deg, #1a1d23, #22262e);
        border: 2px solid rgba(255,255,255,0.15); border-radius: 18px;
        padding: 14px 32px; margin: 0 auto 18px auto; max-width: 520px;
        letter-spacing: 4px; box-shadow: 0 0 25px rgba(0,200,255,0.08);
    }
    .digital-clock .label {
        font-size: 0.65rem; letter-spacing: 6px;
        color: rgba(255,255,255,0.45); display: block; margin-bottom: 2px;
    }
    .map-card {
        background: #161b22; border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px; padding: 8px; margin-bottom: 8px;
    }
    .map-card-title {
        color: #58a6ff; font-size: 0.85rem; font-weight: 700;
        padding: 4px 8px; letter-spacing: 1px;
    }
    section[data-testid="stSidebar"] { background: #161b22; }
    section[data-testid="stSidebar"] .stTextInput label,
    section[data-testid="stSidebar"] .stMarkdown { color: #c9d1d9 !important; }
    .telemetry-header {
        color: #58a6ff; font-size: 1rem; font-weight: 700;
        letter-spacing: 2px; margin-top: 20px; margin-bottom: 6px;
    }


    @media (max-width: 1024px) {
        .digital-clock {
            font-size: 2rem; padding: 10px 20px;
            max-width: 400px; letter-spacing: 2px;
        }
        .digital-clock .label { font-size: 0.55rem; letter-spacing: 4px; }
        .map-card { padding: 4px; margin-bottom: 4px; border-radius: 8px; }
        .map-card-title { font-size: 0.75rem; padding: 2px 6px; }
        .telemetry-header { font-size: 0.85rem; letter-spacing: 1px; }
    }


    @media (max-width: 768px) {
        .digital-clock {
            font-size: 1.4rem; padding: 8px 12px;
            max-width: 300px; letter-spacing: 1px;
            border-radius: 12px;
        }
        .digital-clock .label { font-size: 0.5rem; letter-spacing: 3px; }
        .map-card { padding: 2px; margin-bottom: 2px; border-radius: 6px; }
        .map-card-title { font-size: 0.65rem; padding: 2px 4px; letter-spacing: 0; }
        .telemetry-header { font-size: 0.75rem; letter-spacing: 0; margin-top: 10px; }
        .stDataFrame { overflow-x: auto; }
    }


    @media (max-width: 480px) {
        .digital-clock {
            font-size: 1.1rem; padding: 6px 8px;
            max-width: 260px; letter-spacing: 0;
        }
        .digital-clock .label { font-size: 0.45rem; letter-spacing: 2px; }
    }
    # Hide Streamlit UI Elements
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Light Mode override
if not st.session_state.dark_mode:
    st.markdown(
        """
        <style>
        .stApp { background-color: #f5f5f5 !important; color: #333 !important; }
        .digital-clock {
            background: linear-gradient(145deg, #e8e8e8, #ffffff) !important;
            border: 2px solid rgba(0,0,0,0.1) !important;
            color: #222 !important;
            box-shadow: 0 0 25px rgba(0,0,0,0.05) !important;
        }
        .digital-clock .label { color: rgba(0,0,0,0.45) !important; }
        .map-card {
            background: #ffffff !important;
            border: 1px solid rgba(0,0,0,0.1) !important;
        }
        .map-card-title { color: #1a73e8 !important; }
        .telemetry-header { color: #1a73e8 !important; }
        section[data-testid="stSidebar"] { background: #ffffff !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# PRE-LOGIN PUBLIC PAGE — NARIT-inspired design
# ─────────────────────────────────────────────────────────────────────────────
def show_public_page():
    """NARIT-inspired premium pre-login dashboard."""

    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600&display=swap');

/* Hide Streamlit header and fix layout */
header[data-testid="stHeader"] { display: none !important; }
.stApp {
    background-color: #0e1117;
    color: #c9d1d9;
    font-family: 'Inter', sans-serif;
}
.block-container { padding-top: 0 !important; padding-left: 0 !important; padding-right: 0 !important; max-width: 100% !important; }

/* Navbar */
.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 5%;
    background-color: rgba(14, 17, 23, 0.8);
    backdrop-filter: blur(10px);
    position: sticky;
    top: 0;
    z-index: 1000;
    border-bottom: 1px solid rgba(88, 166, 255, 0.1);
}
.navbar-logo {
    font-family: 'Orbitron', monospace;
    font-size: 1.5rem;
    font-weight: 900;
    color: #58a6ff;
    text-decoration: none;
    display: flex;
    align-items: center;
}
.navbar-logo img {
    height: 30px;
    margin-right: 10px;
}
.navbar-links a {
    color: #c9d1d9;
    text-decoration: none;
    margin-left: 30px;
    font-weight: 400;
    transition: color 0.3s;
}
.navbar-links a:hover {
    color: #58a6ff;
}
.navbar-auth button {
    margin-left: 15px;
}

/* Hero Carousel */
.hero-carousel {
    position: relative;
    width: 100%;
    height: 600px; /* Adjust height as needed */
    overflow: hidden;
    margin-bottom: 40px;
}
.carousel-item {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-size: cover;
    background-position: center;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 1s ease-in-out;
}
.carousel-item.active {
    opacity: 1;
}
.carousel-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.6);
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    justify-content: center;
    padding: 0;
}
.carousel-title {
    font-family: 'Orbitron', monospace;
    font-size: 4rem;
    font-weight: 900;
    color: #ffffff;
    margin-bottom: 20px;
    letter-spacing: 3px;
    text-shadow: 0 0 15px rgba(88, 166, 255, 0.5);
}
.carousel-subtitle {
    font-family: 'Inter', sans-serif;
    font-size: 1.5rem;
    color: #a5d8ff;
    max-width: 800px;
    line-height: 1.6;
}

/* Services Card Grid */
.services-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 30px;
    padding: 50px 5%;
    background-color: #0e1117;
}
.service-card {
    background: linear-gradient(145deg, #1a1d23, #22262e);
    border: 1px solid rgba(88, 166, 255, 0.15);
    border-radius: 12px;
    padding: 30px;
    text-align: center;
    transition: transform 0.3s, box-shadow 0.3s;
}
.service-card:hover {
    transform: translateY(-10px);
    box-shadow: 0 15px 30px rgba(88, 166, 255, 0.2);
}
.service-icon {
    font-size: 3rem;
    color: #58a6ff;
    margin-bottom: 20px;
}
.service-title {
    font-family: 'Orbitron', monospace;
    font-size: 1.2rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 15px;
}
.service-description {
    font-size: 0.95rem;
    color: #8b949e;
    line-height: 1.6;
}

/* Capabilities Section */
.capabilities-section {
    background-color: #0a1628; /* Dark navy */
    padding: 60px 5%;
    text-align: center;
    border-top: 1px solid rgba(88, 166, 255, 0.1);
    border-bottom: 1px solid rgba(88, 166, 255, 0.1);
}
.capabilities-title {
    font-family: 'Orbitron', monospace;
    font-size: 2.5rem;
    font-weight: 900;
    color: #58a6ff;
    margin-bottom: 40px;
    text-shadow: 0 0 10px rgba(88, 166, 255, 0.3);
}
.capabilities-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 25px;
    max-width: 1200px;
    margin: 0 auto;
}
.capability-item {
    background: rgba(88, 166, 255, 0.05);
    border: 1px solid rgba(88, 166, 255, 0.2);
    border-radius: 10px;
    padding: 25px;
    text-align: left;
    transition: background-color 0.3s, border-color 0.3s;
}
.capability-item:hover {
    background-color: rgba(88, 166, 255, 0.1);
    border-color: rgba(88, 166, 255, 0.5);
}
.capability-icon {
    font-size: 2rem;
    color: #a5d8ff;
    margin-bottom: 15px;
}
.capability-title-small {
    font-family: 'Orbitron', monospace;
    font-size: 1rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 10px;
}
.capability-description {
    font-size: 0.85rem;
    color: #8b949e;
    line-height: 1.5;
}

/* Login/Register Section */
.auth-section {
    padding: 60px 5%;
    background-color: #0e1117;
    text-align: center;
}
.auth-section-title {
    font-family: 'Orbitron', monospace;
    font-size: 2.2rem;
    font-weight: 900;
    color: #58a6ff;
    margin-bottom: 40px;
}
.auth-container {
    max-width: 700px;
    margin: 0 auto;
    background: linear-gradient(135deg, #1a1d23, #22262e);
    border: 1px solid rgba(88, 166, 255, 0.2);
    border-radius: 15px;
    padding: 40px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
}
.stTabs [data-baseweb="tab-list"] button {
    font-family: 'Orbitron', monospace;
    font-size: 1rem;
    font-weight: 700;
    color: #c9d1d9;
    background-color: transparent;
    border-bottom: 2px solid transparent;
    transition: all 0.3s;
}
.stTabs [data-baseweb="tab-list"] button:hover {
    color: #58a6ff;
}
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
    color: #58a6ff;
    border-bottom: 2px solid #58a6ff;
}
.stTextInput label, .stRadio label {
    color: #c9d1d9 !important;
}
.stButton button {
    font-family: 'Orbitron', monospace;
    letter-spacing: 1px;
}

@media (max-width: 768px) {
    .navbar { padding: 10px 3%; }
    .navbar-logo { font-size: 1.2rem; }
    .navbar-links a { margin-left: 15px; font-size: 0.9rem; }
    .hero-carousel { height: 400px; }
    .carousel-title { font-size: 2.5rem; }
    .carousel-subtitle { font-size: 1.1rem; }
    .services-grid, .capabilities-grid { grid-template-columns: 1fr; }
    .capabilities-title { font-size: 2rem; }
    .auth-section-title { font-size: 1.8rem; }
    .auth-container { padding: 25px; }
}
</style>
""", unsafe_allow_html=True)

    now = datetime.now()

    # Navbar
    st.markdown(f"""
    <div class="navbar">
        <div class="navbar-logo">
            <span style="font-size:1.8rem;">🛰️</span>
            <span style="margin-left:10px;">V5950</span>
        </div>
        <div class="navbar-links">
            <a href="#services">Services</a>
            <a href="#capabilities">Capabilities</a>
            <a href="#access-system">Access System</a>
        </div>
        <div style="margin-left:auto;display:flex;align-items:center;gap:12px;">
            <span style="font-family:'Inter',sans-serif;font-size:0.85rem;color:#8b949e;">{now.strftime('%H:%M:%S')} UTC+7</span>
            <span style="background:#58a6ff;color:#0e1117;font-size:0.7rem;font-weight:700;padding:4px 10px;border-radius:20px;letter-spacing:1px;">SECURE PROTOCOL</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Hero Carousel — CSS gradient backgrounds (no external images needed)
    st.markdown(f"""
    <div class="hero-carousel">
        <!-- Slide 1 -->
        <div class="carousel-item active" style="background: radial-gradient(ellipse at 60% 40%, #0d2137 0%, #010305 70%), linear-gradient(135deg,#030812,#0a1f3a);">
            <div style="position:absolute;inset:0;overflow:hidden;">
                <div style="position:absolute;width:300px;height:300px;border-radius:50%;background:radial-gradient(circle,rgba(88,166,255,0.12),transparent 70%);top:10%;left:60%;"></div>
                <div style="position:absolute;width:180px;height:180px;border-radius:50%;background:radial-gradient(circle,rgba(88,166,255,0.08),transparent 70%);bottom:15%;right:20%;"></div>
                <div style="position:absolute;top:20%;left:10%;width:2px;height:2px;background:white;border-radius:50%;opacity:0.7;"></div>
                <div style="position:absolute;top:40%;left:25%;width:1px;height:1px;background:white;border-radius:50%;opacity:0.5;"></div>
                <div style="position:absolute;top:15%;left:75%;width:3px;height:3px;background:white;border-radius:50%;opacity:0.6;"></div>
                <div style="position:absolute;top:65%;left:85%;width:2px;height:2px;background:white;border-radius:50%;opacity:0.4;"></div>
                <div style="position:absolute;top:30%;left:50%;width:1px;height:1px;background:white;border-radius:50%;opacity:0.8;"></div>
                <div style="position:absolute;top:80%;left:40%;width:2px;height:2px;background:white;border-radius:50%;opacity:0.5;"></div>
            </div>
            <div class="carousel-overlay" style="background:linear-gradient(to right,rgba(0,0,0,0.75) 50%,rgba(0,0,0,0.1));"
                 >
                <div style="text-align:left;max-width:700px;padding:0 60px;">
                    <div style="font-size:0.8rem;letter-spacing:4px;color:#58a6ff;font-family:'Inter',sans-serif;font-weight:600;margin-bottom:16px;text-transform:uppercase;">— Secure Protocol V5950</div>
                    <div class="carousel-title" style="text-align:left;">Track the universe<br>in real-time.</div>
                    <div class="carousel-subtitle" style="text-align:left;">Advanced satellite telemetry and mission control for professional ground station operators.</div>
                    <div style="margin-top:20px;display:flex;gap:10px;">
                        <div class="hero-dot-nav active" data-i="0"></div>
                        <div class="hero-dot-nav" data-i="1"></div>
                        <div class="hero-dot-nav" data-i="2"></div>
                    </div>
                </div>
            </div>
        </div>
        <!-- Slide 2 -->
        <div class="carousel-item" style="background: radial-gradient(ellipse at 30% 60%, #0f2a1a 0%, #010305 70%), linear-gradient(135deg,#020a04,#0a2a12);">
            <div style="position:absolute;inset:0;overflow:hidden;">
                <div style="position:absolute;width:400px;height:400px;border-radius:50%;background:radial-gradient(circle,rgba(25,200,100,0.08),transparent 70%);top:-10%;right:10%;"></div>
                <div style="position:absolute;top:55%;left:65%;width:2px;height:2px;background:white;border-radius:50%;opacity:0.6;"></div>
                <div style="position:absolute;top:20%;left:80%;width:1px;height:1px;background:white;border-radius:50%;opacity:0.7;"></div>
                <div style="position:absolute;top:70%;left:15%;width:3px;height:3px;background:white;border-radius:50%;opacity:0.4;"></div>
            </div>
            <div class="carousel-overlay" style="background:linear-gradient(to right,rgba(0,0,0,0.78) 50%,rgba(0,0,0,0.1));">
                <div style="text-align:left;max-width:700px;padding:0 60px;">
                    <div style="font-size:0.8rem;letter-spacing:4px;color:#19c864;font-family:'Inter',sans-serif;font-weight:600;margin-bottom:16px;text-transform:uppercase;">— Orbital Mechanics</div>
                    <div class="carousel-title" style="text-align:left;">Predict satellite<br>passes precisely.</div>
                    <div class="carousel-subtitle" style="text-align:left;">Predictive modeling and AOS/LOS schedule for mission-critical flyover planning.</div>
                    <div style="margin-top:20px;display:flex;gap:10px;">
                        <div class="hero-dot-nav" data-i="0"></div>
                        <div class="hero-dot-nav active" data-i="1"></div>
                        <div class="hero-dot-nav" data-i="2"></div>
                    </div>
                </div>
            </div>
        </div>
        <!-- Slide 3 -->
        <div class="carousel-item" style="background: radial-gradient(ellipse at 70% 30%, #1f0d2a 0%, #010305 70%), linear-gradient(135deg,#06020a,#1a0a2a);">
            <div style="position:absolute;inset:0;overflow:hidden;">
                <div style="position:absolute;width:350px;height:350px;border-radius:50%;background:radial-gradient(circle,rgba(180,88,255,0.1),transparent 70%);top:-5%;right:5%;"></div>
                <div style="position:absolute;top:35%;left:70%;width:2px;height:2px;background:white;border-radius:50%;opacity:0.7;"></div>
                <div style="position:absolute;top:60%;left:85%;width:1px;height:1px;background:white;border-radius:50%;opacity:0.5;"></div>
            </div>
            <div class="carousel-overlay" style="background:linear-gradient(to right,rgba(0,0,0,0.78) 50%,rgba(0,0,0,0.1));">
                <div style="text-align:left;max-width:700px;padding:0 60px;">
                    <div style="font-size:0.8rem;letter-spacing:4px;color:#b458ff;font-family:'Inter',sans-serif;font-weight:600;margin-bottom:16px;text-transform:uppercase;">— Mission Reports</div>
                    <div class="carousel-title" style="text-align:left;">Encrypted mission<br>archive control.</div>
                    <div class="carousel-subtitle" style="text-align:left;">Generate PDF mission reports with QR verification, password protection, and secure archiving.</div>
                    <div style="margin-top:20px;display:flex;gap:10px;">
                        <div class="hero-dot-nav" data-i="0"></div>
                        <div class="hero-dot-nav" data-i="1"></div>
                        <div class="hero-dot-nav active" data-i="2"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <style>
    .hero-dot-nav {{
        width:8px;height:8px;border-radius:50%;
        background:rgba(255,255,255,0.35);cursor:pointer;
        transition:all 0.3s;
    }}
    .hero-dot-nav.active {{
        background:#58a6ff;width:24px;border-radius:4px;
    }}
    </style>
    <script>
        (function(){{
            let current = 0;
            const slides = document.querySelectorAll('.carousel-item');
            const n = slides.length;
            function show(i) {{
                slides.forEach((s,j) => s.classList.toggle('active', j===i));
                current = i;
            }}
            setInterval(() => show((current+1)%n), 5000);
        }})();
    </script>
    """, unsafe_allow_html=True)

    # Services Section
    st.markdown('<div id="services" style="padding-top: 80px; margin-top: -80px;"></div>', unsafe_allow_html=True) # Anchor for navigation
    st.markdown('<h2 style="font-family:\'Orbitron\', monospace; text-align:center; color:#58a6ff; font-size:2.5rem; margin-bottom:50px;">OUR SERVICES</h2>', unsafe_allow_html=True)
    st.markdown("""
    <div class="services-grid">
        <div class="service-card">
            <div class="service-icon">📡</div>
            <div class="service-title">REAL-TIME TRACKING</div>
            <div class="service-description">Monitor satellite positions, velocities, and altitudes in real-time with high precision.</div>
        </div>
        <div class="service-card">
            <div class="service-icon">📈</div>
            <div class="service-title">TELEMETRY ANALYSIS</div>
            <div class="service-description">Access and analyze 40-channel telemetry data for comprehensive satellite health and performance.</div>
        </div>
        <div class="service-card">
            <div class="service-icon">🗺️</div>
            <div class="service-title">GLOBAL MAP VIEWS</div>
            <div class="service-description">Visualize satellite orbits and ground tracks on interactive 2D and 3D maps.</div>
        </div>
        <div class="service-card">
            <div class="service-icon">🔔</div>
            <div class="service-title">CUSTOM ALERTS</div>
            <div class="service-description">Set up proximity alerts for satellites passing near your ground station or points of interest.</div>
        </div>
        <div class="service-card">
            <div class="service-icon">📧</div>
            <div class="service-title">AUTOMATED REPORTING</div>
            <div class="service-description">Generate and email detailed PDF reports of satellite passes and telemetry data.</div>
        </div>
        <div class="service-card">
            <div class="service-icon">🔒</div>
            <div class="service-title">SECURE ACCESS</div>
            <div class="service-description">Robust user authentication and data encryption ensure your mission data is always protected.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Capabilities Section
    st.markdown('<div id="capabilities" style="padding-top: 80px; margin-top: -80px;"></div>', unsafe_allow_html=True) # Anchor for navigation
    st.markdown("""
    <div class="capabilities-section">
        <div class="capabilities-title">SYSTEM CAPABILITIES</div>
        <div class="capabilities-grid">
            <div class="capability-item">
                <div class="capability-icon">🛰️</div>
                <div class="capability-title-small">MULTI-SATELLITE SUPPORT</div>
                <div class="capability-description">Track multiple satellites simultaneously from a comprehensive catalog.</div>
            </div>
            <div class="capability-item">
                <div class="capability-icon">📊</div>
                <div class="capability-title-small">DATA EXPORT</div>
                <div class="capability-description">Export telemetry data to CSV and PDF formats for offline analysis and archiving.</div>
            </div>
            <div class="capability-item">
                <div class="capability-icon">⏰</div>
                <div class="capability-title-small">PASS PREDICTION</div>
                <div class="capability-description">Accurate prediction of satellite flyover times and trajectories for any ground station.</div>
            </div>
            <div class="capability-item">
                <div class="capability-icon">🌐</div>
                <div class="capability-title-small">GLOBAL STATION NETWORK</div>
                <div class="capability-description">Simulate ground station operations from any location on Earth.</div>
            </div>
            <div class="capability-item">
                <div class="capability-icon">⚙️</div>
                <div class="capability-title-small">CUSTOMIZABLE INTERFACE</div>
                <div class="capability-description">Personalize your dashboard with dark/light modes and map styles.</div>
            </div>
            <div class="capability-item">
                <div class="capability-icon">🚀</div>
                <div class="capability-title-small">FUTURE EXPANSION</div>
                <div class="capability-description">Designed for scalability, ready for integration with new data sources and features.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Login / Register
    st.markdown('<div id="access-system" style="padding-top: 80px; margin-top: -80px;"></div>', unsafe_allow_html=True) # Anchor for navigation
    st.markdown('<h2 class="auth-section-title">ACCESS SYSTEM</h2>', unsafe_allow_html=True)

    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    login_tab, reg_tab = st.tabs(["Login", "Register"])

    with login_tab:
        lc, _, rc = st.columns([2, 0.3, 1])
        with lc:
            le = st.text_input("Email", key="pub_login_email", placeholder="mission.commander@email.com")
            lp = st.text_input("Password", type="password", key="pub_login_pass", placeholder="Enter password")
            if st.button("AUTHENTICATE", use_container_width=True, type="primary", key="btn_login"):
                if le and lp:
                    ok, name, msg = login_user(le, lp)
                    if ok:
                        st.session_state.logged_in = True
                        st.session_state.username = name
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Please enter email and password")
        with rc:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Continue with Google", use_container_width=True, key="btn_google"):
                st.session_state["_social"] = "google"
            if st.button("Continue with Facebook", use_container_width=True, key="btn_fb"):
                st.session_state["_social"] = "facebook"
            mode = st.session_state.get("_social", "")
            if mode in ("google", "facebook"):
                se = st.text_input(f"{mode.title()} Email", key=f"_se_{mode}")
                if st.button(f"Confirm", key=f"_sc_{mode}"):
                    if se:
                        ok, name = social_login(se, se.split("@")[0], mode)
                        st.session_state.logged_in = True
                        st.session_state.username = name
                        st.session_state["_social"] = ""
                        st.rerun()

    with reg_tab:
        r1, r2 = st.columns(2)
        rn = r1.text_input("Display Name", key="reg_name", placeholder="Commander Name")
        re_email = r2.text_input("Email", key="reg_email", placeholder="your@email.com")
        rp = r1.text_input("Password", type="password", key="reg_pass")
        rp2 = r2.text_input("Confirm Password", type="password", key="reg_pass2")
        rm = st.radio("Sign up via", ["Email", "Google", "Facebook"], horizontal=True, key="reg_method")
        if st.button("CREATE ACCOUNT", use_container_width=True, type="primary", key="btn_register"):
            if not rn or not re_email:
                st.warning("Please fill in all fields")
            elif rp != rp2:
                st.error("Passwords do not match")
            else:
                ok, msg = register_user(re_email, rp, rn, rm.lower())
                if ok:
                    st.success(f"{msg} You can now log in.")
                else:
                    st.error(msg)
    st.markdown('</div>', unsafe_allow_html=True)


# =============================================================================
#  SATELLITE IMAGERY STYLE (Esri World Imagery - free tiles)
# ═══════════════════════════════════════════════════════════════════════════════
SATELLITE_STYLE = {
    "version": 8,
    "sources": {
        "esri": {
            "type": "raster",
            "tiles": [
                "https://server.arcgisonline.com/ArcGIS/rest/services/"
                "World_Imagery/MapServer/tile/{z}/{y}/{x}"
            ],
            "tileSize": 256,
            "attribution": "Esri",
        }
    },
    "layers": [{"id": "esri-sat", "type": "raster", "source": "esri"}],
}


def _geocode_address(address: str):
    """Look up lat/lon from an address string using Nominatim (OSM)."""
    try:
        url = (
            "https://nominatim.openstreetmap.org/search?"
            + urllib.parse.urlencode({"q": address, "format": "json", "limit": "1"})
        )
        req = urllib.request.Request(url, headers={"User-Agent": "SatTelemetryV5950/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return None, None


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPER: simulate dashed line by inserting None gaps
# ═══════════════════════════════════════════════════════════════════════════════
def _make_dashed(lats, lons, dash=3, gap=2):
    out_lat, out_lon = []  , []
    state, count = "dash", 0
    for la, lo in zip(lats, lons):
        if la is None:
            out_lat.append(None); out_lon.append(None)
            count, state = 0, "dash"
            continue
        if state == "dash":
            out_lat.append(la); out_lon.append(lo)
            count += 1
            if count >= dash:
                out_lat.append(None); out_lon.append(None)
                count, state = 0, "gap"
        else:
            count += 1
            if count >= gap:
                count, state = 0, "dash"
    return out_lat, out_lon


# ═══════════════════════════════════════════════════════════════════════════════
#  MAP PLOTTING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _make_sat_map(sat_pos, track, sat_name, zoom, style="tactical"):
    """Create 2D map with satellite imagery, orbit track, and satellite marker."""
    fig = go.Figure()

    # Past track — outline (thick, transparent)
    fig.add_trace(go.Scattermap(
        lat=track["past_lats"], lon=track["past_lons"],
        mode="lines", line=dict(width=6, color="rgba(88,166,255,0.25)"),
        showlegend=False, hoverinfo="skip",
    ))
    # Past track — main line
    fig.add_trace(go.Scattermap(
        lat=track["past_lats"], lon=track["past_lons"],
        mode="lines", line=dict(width=2, color="#58a6ff"),
        showlegend=False, hoverinfo="skip",
    ))
    # Future track — dashed
    d_lats, d_lons = _make_dashed(track["future_lats"], track["future_lons"])
    fig.add_trace(go.Scattermap(
        lat=d_lats, lon=d_lons,
        mode="lines", line=dict(width=2, color="rgba(88,166,255,0.55)"),
        showlegend=False, hoverinfo="skip",
    ))
    # Satellite marker
    fig.add_trace(go.Scattermap(
        lat=[sat_pos["lat"]], lon=[sat_pos["lon"]],
        mode="markers+text",
        marker=dict(size=14, color="#58a6ff", symbol="rocket"),
        text=[sat_name], textposition="top center", showlegend=False,
    ))

    fig.update_layout(
        map=dict(style=SATELLITE_STYLE,
                 center=dict(lat=sat_pos["lat"], lon=sat_pos["lon"]),
                 zoom=zoom),
        margin=dict(l=0, r=0, t=0, b=0), height=320,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _make_3d_globe(sat_pos, track, sat_name, scale):
    """Create 3D orthographic globe with orbit track."""
    fig = go.Figure()

    # Past track — outline
    fig.add_trace(go.Scattergeo(
        lat=track["past_lats"], lon=track["past_lons"],
        mode="lines", line=dict(width=5, color="rgba(88,166,255,0.25)"),
        showlegend=False, hoverinfo="skip",
    ))
    # Past track — main
    fig.add_trace(go.Scattergeo(
        lat=track["past_lats"], lon=track["past_lons"],
        mode="lines", line=dict(width=2, color="#58a6ff"),
        showlegend=False, hoverinfo="skip",
    ))
    # Future track — dashed (Scattergeo supports native dash)
    fig.add_trace(go.Scattergeo(
        lat=track["future_lats"], lon=track["future_lons"],
        mode="lines", line=dict(width=2, color="rgba(88,166,255,0.55)", dash="dash"),
        showlegend=False, hoverinfo="skip",
    ))
    # Satellite marker
    fig.add_trace(go.Scattergeo(
        lat=[sat_pos["lat"]], lon=[sat_pos["lon"]],
        mode="markers", marker=dict(size=10, color="#58a6ff", symbol="star"),
        text=[sat_name], showlegend=False,
    ))

    fig.update_geos(
        projection_type="orthographic",
        projection_scale=max(0.5, scale * 0.5),
        projection_rotation=dict(lat=sat_pos["lat"], lon=sat_pos["lon"]),
        showland=True, landcolor="#1a3a1a",
        showocean=True, oceancolor="#0a1628",
        showcountries=True, countrycolor="#333",
        showlakes=False, bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0), height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        geo=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def _make_station_map(lat, lon, station_label, zoom):
    """Station map — ground station from sidebar info, regular street tiles."""
    fig = go.Figure()
    fig.add_trace(go.Scattermap(
        lat=[lat], lon=[lon], mode="markers+text",
        marker=dict(size=15, color="#ff4444"),
        text=[station_label], textposition="top center", showlegend=False,
    ))
    fig.update_layout(
        map=dict(style="open-street-map",
                 center=dict(lat=lat, lon=lon), zoom=zoom),
        margin=dict(l=0, r=0, t=0, b=0), height=320,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPER: Generate PDF, save to Downloads, return path
# ═══════════════════════════════════════════════════════════════════════════════
def _build_and_save_pdf(archive_sat, ref_id, passkey, pred_dt=None):
    """Generate PDF, save to Downloads, return (pdf_bytes, file_path)."""
    norad_id = SATELLITE_CATALOG[archive_sat]
    sat_obj = fetch_tle(archive_sat, norad_id)
    dt = pred_dt
    is_predictive = dt is not None
    telemetry_df = build_telemetry_40ch(archive_sat, sat_obj, dt)
    sat_pos = compute_position(sat_obj, dt)

    pdf_bytes = generate_pdf(
        telemetry_df=telemetry_df,
        station_info={
            "sub_district": st.session_state.sub_district,
            "district": st.session_state.district,
            "province": st.session_state.province,
            "zip_code": st.session_state.zip_code,
            "country": st.session_state.country,
        },
        archive_id=ref_id,
        passkey=passkey,
        sat_name=archive_sat,
        is_predictive=is_predictive,
        sat_position=sat_pos,
        norad_id=norad_id,
        pred_dt=dt,
    )

    # Save to Downloads folder
    downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    os.makedirs(downloads_dir, exist_ok=True)
    pdf_filename = f"{ref_id}.pdf"
    pdf_path = os.path.join(downloads_dir, pdf_filename)
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    return pdf_bytes, pdf_path, pdf_filename


# ═══════════════════════════════════════════════════════════════════════════════
#  DIALOG — Mission Archive Control
# ═══════════════════════════════════════════════════════════════════════════════
@st.dialog("MISSION ARCHIVE CONTROL", width="large")
def mission_archive_control():
    dialog_sat = st.selectbox(
        "🛰️ เลือกดาวเทียม (Select Satellite)",
        options=list(SATELLITE_CATALOG.keys()),
        index=list(SATELLITE_CATALOG.keys()).index(st.session_state.selected_satellite),
        key="dialog_satellite",
    )
    st.markdown(f"### 📦 วิเคราะห์ภารกิจสำหรับ: **{dialog_sat}**")

    # ── Cache toggle ──
    st.session_state.remember_archive = st.toggle(
        "💾 จดจำไฟล์ที่คำนวณไว้ (Remember cached report)",
        value=st.session_state.get("remember_archive", False),
        key="remember_toggle",
    )

    if not st.session_state.download_ready:
        tab1, tab2 = st.tabs(["🔄 รายงานปัจจุบัน", "📅 รายงานล่วงหน้า"])

        with tab1:
            st.info("ระบบจะสร้างรายงานจากการคำนวณตำแหน่ง ณ เวลาปัจจุบัน (Real-time)")
            if st.button("🚀 GENERATE REAL-TIME PDF", use_container_width=True, type="primary"):
                now = datetime.now()
                seq = random.randint(100, 999)
                ref_id = f"REF-{seq}-{now.strftime('%Y%m%d')}"
                passkey = f"{random.randint(100000, 999999)}"

                with st.spinner("กำลังสร้างรายงาน PDF พร้อม QR Code..."):
                    try:
                        pdf_bytes, pdf_path, pdf_filename = _build_and_save_pdf(
                            dialog_sat, ref_id, passkey,
                        )
                        st.session_state.ref_id = ref_id
                        st.session_state.passkey = passkey
                        st.session_state.archive_sat = dialog_sat
                        st.session_state.cached_pdf = pdf_bytes
                        st.session_state.saved_pdf_path = pdf_path
                        st.session_state.saved_pdf_filename = pdf_filename
                        st.session_state.download_ready = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ เกิดข้อผิดพลาด: {e}")

        with tab2:
            st.write("ระบุวันเวลาที่ต้องการวิเคราะห์ตำแหน่งล่วงหน้า")
            col1, col2 = st.columns(2)
            pred_date = col1.date_input(
                "วันที่", value=datetime.now(),
                key="pred_date_input",
            )
            pred_time = col2.time_input(
                "เวลา", value=datetime.now().time(),
                key="pred_time_input",
            )

            if st.button("📅 CALCULATE & DOWNLOAD PREDICTIVE PDF", use_container_width=True):
                dt = datetime.combine(pred_date, pred_time).replace(tzinfo=timezone.utc)
                now = datetime.now()
                seq = random.randint(100, 999)
                ref_id = f"REF-{seq}-{now.strftime('%Y%m%d')}"
                passkey = f"{random.randint(100000, 999999)}"

                with st.spinner("กำลังคำนวณตำแหน่งล่วงหน้าและสร้าง PDF..."):
                    try:
                        pdf_bytes, pdf_path, pdf_filename = _build_and_save_pdf(
                            dialog_sat, ref_id, passkey, pred_dt=dt,
                        )
                        st.session_state.ref_id = ref_id
                        st.session_state.passkey = passkey
                        st.session_state.pred_dt = dt
                        st.session_state.archive_sat = dialog_sat
                        st.session_state.cached_pdf = pdf_bytes
                        st.session_state.saved_pdf_path = pdf_path
                        st.session_state.saved_pdf_filename = pdf_filename
                        st.session_state.download_ready = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ เกิดข้อผิดพลาด: {e}")

    else:
        # ── Download Ready — show Archive ID, Password, file info ──
        st.markdown(f"""
        <div style="background: white; padding: 30px; border-radius: 12px; text-align: center;
                    border: 1px solid #ccc; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <h3 style="color: #666; margin: 0; font-size: 0.8rem; letter-spacing: 3px;">SECURE ARCHIVE ACCESS</h3>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #888; font-size: 0.7rem; letter-spacing: 2px; margin-bottom: 5px;">ARCHIVE ID</p>
            <h1 style="color: #FF0000; font-family: 'Courier New', monospace; font-weight: 900;
                       margin: 0 0 20px 0;">{st.session_state.ref_id}</h1>
            <p style="color: #888; font-size: 0.7rem; letter-spacing: 2px; margin-bottom: 5px;">PASSWORD</p>
            <h2 style="color: #000; font-family: 'Courier New', monospace; font-weight: 700;
                       margin: 0 0 20px 0;">{st.session_state.passkey}</h2>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 10px 0;">
            <p style="color: #28a745; font-size: 0.9rem; font-weight: 700; margin: 0;">
                ✅ ไฟล์ PDF บันทึกแล้ว (พร้อม QR Code ตรวจสอบ)</p>
            <p style="color: #666; font-size: 0.75rem; margin: 8px 0 0 0;">
                📂 {st.session_state.get('saved_pdf_path', '')}</p>
        </div>
        """, unsafe_allow_html=True)

        st.write("")

        # Open Downloads folder button
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("📂 เปิดโฟลเดอร์ Downloads", use_container_width=True, type="primary"):
                import subprocess
                downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
                if sys.platform == "win32":
                    subprocess.Popen(f'explorer "{downloads_dir}"')
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", downloads_dir])
                else:
                    subprocess.Popen(["xdg-open", downloads_dir])

        with btn_col2:
            if st.button("🔙 สร้างรายงานใหม่", use_container_width=True):
                if st.session_state.get("remember_archive", False):
                    st.session_state.download_ready = True
                else:
                    st.session_state.download_ready = False
                    st.session_state.pop("pred_dt", None)
                    st.session_state.pop("archive_sat", None)
                    st.session_state.pop("cached_pdf", None)
                    st.session_state.pop("saved_pdf_path", None)
                    st.session_state.pop("saved_pdf_filename", None)
                st.rerun()

        # ── Email Section ──
        st.markdown("---")
        if st.session_state.gmail_address and st.session_state.gmail_app_password:
            st.markdown("#### 📧 ส่งรายงานทาง Email")
            recipient = st.text_input(
                "Email ผู้รับ",
                placeholder="recipient@example.com",
                key="email_recipient",
            )
            if st.button("📧 SEND EMAIL", use_container_width=True, type="primary"):
                if not recipient:
                    st.warning("กรุณาใส่ Email ผู้รับ")
                elif st.session_state.get("cached_pdf") is None:
                    st.error("ไม่พบไฟล์ PDF")
                else:
                    with st.spinner("กำลังส่ง Email..."):
                        success, message = send_pdf_email(
                            sender_email=st.session_state.gmail_address,
                            app_password=st.session_state.gmail_app_password,
                            recipient_email=recipient,
                            pdf_bytes=st.session_state.cached_pdf,
                            pdf_filename=st.session_state.get("saved_pdf_filename", f"{st.session_state.ref_id}.pdf"),
                            archive_id=st.session_state.ref_id,
                            passkey=st.session_state.passkey,
                            sat_name=st.session_state.get("archive_sat", ""),
                        )
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
        else:
            st.info("📧 ตั้งค่า Gmail + App Password ใน Sidebar เพื่อส่ง Email")


# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
if not st.session_state.logged_in:
    st.markdown("""<style>section[data-testid="stSidebar"]{display:none}</style>""",
                unsafe_allow_html=True)
    show_public_page()
    st.stop()

with st.sidebar:
    st.markdown("### 🛰️ Satellite Selection")
    st.session_state.selected_satellite = st.selectbox(
        "Select Target Satellite",
        options=list(SATELLITE_CATALOG.keys()),
        index=0,
    )

    if st.session_state.selected_satellite != st.session_state.last_sat_name:
        with st.spinner(f"Fetching TLE for {st.session_state.selected_satellite}..."):
            norad_id = SATELLITE_CATALOG[st.session_state.selected_satellite]
            st.session_state.satellite_obj = fetch_tle(
                st.session_state.selected_satellite, norad_id
            )
            st.session_state.last_sat_name = st.session_state.selected_satellite

    st.markdown("---")
    st.markdown("### 📡 Station Information")
    locked = st.session_state.station_locked

    st.session_state.sub_district = st.text_input(
        "ตำบล (Sub-district)", value=st.session_state.sub_district, disabled=locked
    )
    st.session_state.district = st.text_input(
        "อำเภอ (District)", value=st.session_state.district, disabled=locked
    )
    st.session_state.province = st.text_input(
        "จังหวัด (Province)", value=st.session_state.province, disabled=locked
    )
    st.session_state.zip_code = st.text_input(
        "รหัสไปรษณีย์ (Zip Code)", value=st.session_state.zip_code, disabled=locked
    )
    st.session_state.country = st.text_input(
        "ประเทศ (Country)", value=st.session_state.country, disabled=locked
    )
    lat_col, lon_col = st.columns(2)
    st.session_state.station_lat = lat_col.number_input(
        "Latitude", value=st.session_state.station_lat,
        format="%.6f", disabled=locked,
    )
    st.session_state.station_lon = lon_col.number_input(
        "Longitude", value=st.session_state.station_lon,
        format="%.6f", disabled=locked,
    )

    if not locked:
        if st.button("📍 ค้นหาพิกัดจากที่อยู่", use_container_width=True):
            full_addr = " ".join(filter(None, [
                st.session_state.sub_district,
                st.session_state.district,
                st.session_state.province,
                st.session_state.zip_code,
                st.session_state.country,
            ]))
            with st.spinner("กำลังค้นหาพิกัด..."):
                lat, lon = _geocode_address(full_addr)
            if lat is not None:
                st.session_state.station_lat = lat
                st.session_state.station_lon = lon
                st.success(f"พบพิกัด: {lat:.6f}, {lon:.6f}")
                st.rerun()
            else:
                st.error("ไม่พบพิกัดจากที่อยู่ที่กรอก")

    if not locked:
        if st.button("✅ LOCK STATION", use_container_width=True):
            st.session_state.station_locked = True
            st.rerun()
    else:
        st.success("🔒 Station Locked")
        if st.button("🔓 Unlock", use_container_width=True):
            st.session_state.station_locked = False
            st.rerun()

    # ── Zoom Controls ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🔍 Map Zoom Controls")
    st.session_state.zoom_tactical = st.slider(
        "🗺️ Tactical Map", 1, 18, st.session_state.zoom_tactical
    )
    st.session_state.zoom_global = st.slider(
        "🌍 Global Map", 1, 18, st.session_state.zoom_global
    )
    st.session_state.zoom_station = st.slider(
        "📡 Station Map", 1, 18, st.session_state.zoom_station
    )
    st.session_state.zoom_globe = st.slider(
        "🌐 3D Globe Scale", 1, 8, st.session_state.zoom_globe
    )

    st.markdown("---")
    if st.button("📦 MISSION ARCHIVE CONTROL", use_container_width=True, type="primary"):
        mission_archive_control()

    # ── Email Settings ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📧 Email Settings (Gmail)")
    st.session_state.gmail_address = st.text_input(
        "Gmail Address", value=st.session_state.gmail_address,
        placeholder="your.email@gmail.com",
    )
    st.session_state.gmail_app_password = st.text_input(
        "App Password", value=st.session_state.gmail_app_password,
        type="password", placeholder="xxxx xxxx xxxx xxxx",
        help="Go to Google Account > Security > App Passwords to generate one",
    )
    if st.session_state.gmail_address and st.session_state.gmail_app_password:
        st.success("Email configured")
    else:
        st.info("Gmail + App Password")

    # ── Theme Toggle ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Theme")
    dark = st.toggle("Dark Mode", value=st.session_state.dark_mode, key="theme_toggle")
    st.session_state.dark_mode = dark

    # ── Alert System ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Alert System")
    st.session_state.alerts_enabled = st.toggle(
        "Enable Proximity Alerts", value=st.session_state.alerts_enabled,
        key="alert_toggle",
    )
    if st.session_state.alerts_enabled:
        st.session_state.alert_distance_km = st.slider(
            "Alert Distance (km)", 100, 5000,
            st.session_state.alert_distance_km, step=100,
        )
        if st.session_state.alert_log:
            with st.expander("Alert Log", expanded=False):
                for msg in reversed(st.session_state.alert_log[-10:]):
                    st.caption(msg)

    # ── Multi-Satellite Tracking ──────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Multi-Satellite")
    tracked = st.multiselect(
        "Track (max 5)",
        options=list(SATELLITE_CATALOG.keys()),
        default=st.session_state.tracked_satellites,
        max_selections=5,
        key="multi_sat_select",
    )
    st.session_state.tracked_satellites = tracked

    # ── Satellite Pass Prediction ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Pass Prediction")
    if st.button("Calculate Next Passes", use_container_width=True):
        if st.session_state.satellite_obj:
            from skyfield.api import load, Topos
            ts = load.timescale()
            station = Topos(
                latitude_degrees=st.session_state.station_lat,
                longitude_degrees=st.session_state.station_lon,
            )
            sat = st.session_state.satellite_obj
            t0 = ts.now()
            t1 = ts.tt_jd(t0.tt + 1)  # next 24 hours

            passes = []
            try:
                events = sat.find_events(station, t0, t1, altitude_degrees=10.0)
                if events and len(events) == 3:
                    times, event_types = events[0], events[1]
                    i = 0
                    while i < len(event_types):
                        if event_types[i] == 0:  # rise
                            rise_t = times[i].utc_strftime("%H:%M:%S")
                            max_t = times[i+1].utc_strftime("%H:%M:%S") if i+1 < len(event_types) else "?"
                            set_t = times[i+2].utc_strftime("%H:%M:%S") if i+2 < len(event_types) else "?"
                            passes.append(f"Rise {rise_t} | Max {max_t} | Set {set_t}")
                            i += 3
                        else:
                            i += 1
            except Exception:
                pass

            if passes:
                for p in passes[:5]:
                    st.caption(p)
            else:
                st.caption("No passes in next 24h")
        else:
            st.caption("Load satellite first")

    # ── User Status ──
    st.markdown("---")
    st.success(f"Logged in: {st.session_state.username}")
    if st.button("LOGOUT", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#  LIVE DASHBOARD — uses @st.fragment for 1-second updates without full rerun
#  (prevents the dialog from closing on refresh)
# ═══════════════════════════════════════════════════════════════════════════════

@st.fragment(run_every=timedelta(seconds=1))
def live_dashboard():
    # ── Digital Clock ────────────────────────────────────────────────────────
    now = datetime.now()
    clock_str = now.strftime("%H : %M : %S")
    date_str = now.strftime("%d %b %Y")

    st.markdown(
        f"""
        <div class="digital-clock">
            <span class="label">SATELLITE TELEMETRY SYSTEM</span>
            {clock_str}
            <span class="label">{date_str}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Maps & Telemetry ─────────────────────────────────────────────────────
    if st.session_state.satellite_obj:
        sat_name = st.session_state.selected_satellite
        current_pos = compute_position(st.session_state.satellite_obj)
        track = compute_ground_track(st.session_state.satellite_obj)

        row1_col1, row1_col2 = st.columns(2)
        row2_col1, row2_col2 = st.columns(2)

        with row1_col1:
            st.markdown(
                '<div class="map-card"><span class="map-card-title">🗺️ TACTICAL MAP</span></div>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                _make_sat_map(current_pos, track, sat_name,
                              st.session_state.zoom_tactical, "tactical"),
                key="map_tactical", use_container_width=True,
            )

        with row1_col2:
            st.markdown(
                '<div class="map-card"><span class="map-card-title">🌍 GLOBAL MAP</span></div>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                _make_sat_map(current_pos, track, sat_name,
                              st.session_state.zoom_global, "global"),
                key="map_global", use_container_width=True,
            )

        with row2_col1:
            st.markdown(
                '<div class="map-card"><span class="map-card-title">📡 STATION MAP</span></div>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                _make_station_map(
                    st.session_state.station_lat,
                    st.session_state.station_lon,
                    f"GS-{st.session_state.sub_district}",
                    st.session_state.zoom_station,
                ),
                key="map_station", use_container_width=True,
            )

        with row2_col2:
            st.markdown(
                '<div class="map-card"><span class="map-card-title">🌐 3D GLOBE</span></div>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                _make_3d_globe(current_pos, track, sat_name,
                               st.session_state.zoom_globe),
                key="map_globe", use_container_width=True,
            )

        # Multi-Satellite Tracking Map
        if st.session_state.tracked_satellites:
            st.markdown('<p class="telemetry-header">MULTI-SATELLITE TRACKING</p>', unsafe_allow_html=True)
            multi_fig = go.Figure()
            colors = ["#ff4444", "#44ff44", "#ffaa00", "#aa44ff", "#44ffff"]
            for idx, ms_name in enumerate(st.session_state.tracked_satellites):
                ms_norad = SATELLITE_CATALOG.get(ms_name)
                if ms_norad:
                    try:
                        ms_sat = fetch_tle(ms_name, ms_norad)
                        if ms_sat:
                            ms_pos = compute_position(ms_sat)
                            multi_fig.add_trace(go.Scattermap(
                                lat=[ms_pos["lat"]], lon=[ms_pos["lon"]],
                                mode="markers+text",
                                marker=dict(size=12, color=colors[idx % 5]),
                                text=[ms_name],
                                textposition="top center",
                                name=ms_name,
                            ))
                    except Exception:
                        pass
            multi_fig.update_layout(
                map=dict(style="carto-darkmatter" if st.session_state.dark_mode else "open-street-map",
                         center=dict(lat=0, lon=0), zoom=1),
                margin=dict(l=0, r=0, t=0, b=0), height=400,
                showlegend=True, legend=dict(font=dict(color="white")),
            )
            st.plotly_chart(multi_fig, use_container_width=True, key="map_multi")

        st.markdown(
            '<p class="telemetry-header">TELEMETRY DATA - 40 CHANNELS</p>',
            unsafe_allow_html=True,
        )
        telemetry_df = build_telemetry_40ch(sat_name, st.session_state.satellite_obj)
        st.dataframe(
            telemetry_df, width=None, height=600,
            use_container_width=True, hide_index=True,
        )

        # CSV/Excel Export
        exp_col1, exp_col2 = st.columns(2)
        with exp_col1:
            csv_data = telemetry_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="CSV Export",
                data=csv_data,
                file_name=f"telemetry_{sat_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with exp_col2:
            excel_buf = _io.BytesIO()
            telemetry_df.to_excel(excel_buf, index=False, engine="openpyxl")
            st.download_button(
                label="Excel Export",
                data=excel_buf.getvalue(),
                file_name=f"telemetry_{sat_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        # Track telemetry history (keep last 60 points)
        history = st.session_state.telemetry_history
        history.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "alt": current_pos["alt_km"],
            "lat": current_pos["lat"],
            "lon": current_pos["lon"],
            "vel": sum(v**2 for v in current_pos["velocity_km_s"])**0.5,
        })
        if len(history) > 60:
            st.session_state.telemetry_history = history[-60:]

        # Telemetry History Charts
        if len(history) > 2:
            import pandas as pd
            hist_df = pd.DataFrame(history)
            st.markdown('<p class="telemetry-header">TELEMETRY HISTORY</p>', unsafe_allow_html=True)
            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                fig_alt = go.Figure()
                fig_alt.add_trace(go.Scatter(
                    x=hist_df["time"], y=hist_df["alt"],
                    mode="lines", name="Altitude",
                    line=dict(color="#58a6ff", width=2),
                    fill="tozeroy", fillcolor="rgba(88,166,255,0.1)",
                ))
                fig_alt.update_layout(
                    title="Altitude (km)", height=250,
                    template="plotly_dark", margin=dict(l=40, r=10, t=40, b=30),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_alt, use_container_width=True, key="chart_alt")
            with chart_col2:
                fig_vel = go.Figure()
                fig_vel.add_trace(go.Scatter(
                    x=hist_df["time"], y=hist_df["vel"],
                    mode="lines", name="Velocity",
                    line=dict(color="#ff6b6b", width=2),
                    fill="tozeroy", fillcolor="rgba(255,107,107,0.1)",
                ))
                fig_vel.update_layout(
                    title="Velocity (km/s)", height=250,
                    template="plotly_dark", margin=dict(l=40, r=10, t=40, b=30),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_vel, use_container_width=True, key="chart_vel")

        # Alert System Check
        if st.session_state.alerts_enabled and current_pos:
            from math import radians, sin, cos, sqrt, atan2
            slat = radians(st.session_state.station_lat)
            slon = radians(st.session_state.station_lon)
            dlat = radians(current_pos["lat"])
            dlon = radians(current_pos["lon"])
            a = sin((dlat-slat)/2)**2 + cos(slat)*cos(dlat)*sin((dlon-slon)/2)**2
            dist_km = 6371 * 2 * atan2(sqrt(a), sqrt(1-a))
            if dist_km < st.session_state.alert_distance_km:
                alert_msg = f"[{datetime.now().strftime('%H:%M:%S')}] {sat_name} within {dist_km:.0f} km of station!"
                if not st.session_state.alert_log or st.session_state.alert_log[-1] != alert_msg:
                    st.session_state.alert_log.append(alert_msg)
                    if len(st.session_state.alert_log) > 20:
                        st.session_state.alert_log = st.session_state.alert_log[-20:]
                st.warning(f"PROXIMITY ALERT: {sat_name} is {dist_km:.0f} km from station!")

    else:
        st.warning("Waiting for TLE data...")


live_dashboard()
