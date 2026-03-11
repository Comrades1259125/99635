import streamlit as st
from datetime import datetime
import time

def render_banner():
    st.markdown("""
    <div style="background: linear-gradient(90deg, #111b2b, #1a2842); padding: 20px; border-radius: 12px; border-left: 5px solid #58a6ff; margin-bottom: 25px; display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 15px;">
            <div style="background: rgba(88,166,255,0.2); padding: 10px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                <span style="font-size: 1.5rem; color: #58a6ff;">☄️</span>
            </div>
            <div>
                <h3 style="margin: 0; color: #fff; font-family: 'Orbitron', sans-serif; letter-spacing: 1px;">ACTIVE EVENT: Lyrids Meteor Shower</h3>
                <p style="margin: 5px 0 0 0; color: #a5d8ff; font-size: 0.9rem;">Expect up to 18 meteors per hour. Peak visibility near the constellation Lyra.</p>
            </div>
        </div>
        <div style="text-align: right; color: rgba(255,255,255,0.5); font-size: 0.8rem;">
            <div>CURRENT STATUS</div>
            <div style="color: #4CAF50; font-weight: bold;">🟢 OPTIMAL VIEWING</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_astronomical_calendar():
    st.markdown("""
    <h3 style="color: #58a6ff; font-family: 'Orbitron', sans-serif; border-bottom: 1px solid rgba(88, 166, 255, 0.2); padding-bottom: 10px; margin-bottom: 20px;">ASTRONOMICAL CALENDAR 2026</h3>
    
    <style>
    .cal-table { width: 100%; border-collapse: collapse; margin-bottom: 30px; font-family: 'Inter', sans-serif; font-size: 0.9rem; }
    .cal-table th { text-align: left; padding: 12px 15px; border-bottom: 2px solid rgba(88,166,255,0.3); color: #8b949e; text-transform: uppercase; letter-spacing: 1px; }
    .cal-table td { padding: 15px; border-bottom: 1px solid rgba(255,255,255,0.05); color: #c9d1d9; }
    .cal-table tr:hover td { background: rgba(88,166,255,0.05); }
    .cal-date { font-family: 'Orbitron', monospace; color: #58a6ff; font-weight: 700; width: 120px; }
    .cal-type { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 600; }
    .type-eclipse { background: rgba(255, 87, 34, 0.2); color: #FF5722; border: 1px solid rgba(255, 87, 34, 0.5); }
    .type-equinox { background: rgba(76, 175, 80, 0.2); color: #4CAF50; border: 1px solid rgba(76, 175, 80, 0.5); }
    .type-meteor { background: rgba(3, 169, 244, 0.2); color: #03A9F4; border: 1px solid rgba(3, 169, 244, 0.5); }
    </style>
    
    <table class="cal-table">
        <tr>
            <th>Date</th>
            <th>Event Name</th>
            <th>Category</th>
            <th>Visibility / Detail</th>
        </tr>
        <tr>
            <td class="cal-date">MAR 20</td>
            <td><strong>Vernal Equinox</strong></td>
            <td><span class="cal-type type-equinox">SEASONAL</span></td>
            <td>Sun crosses the celestial equator. Equal day and night.</td>
        </tr>
        <tr>
            <td class="cal-date">APR 22-23</td>
            <td><strong>Lyrids Meteor Shower</strong></td>
            <td><span class="cal-type type-meteor">METEOR</span></td>
            <td>Average shower, dust particles from comet C/1861 G1 Thatcher.</td>
        </tr>
        <tr>
            <td class="cal-date">MAY 05</td>
            <td><strong>Penumbral Lunar Eclipse</strong></td>
            <td><span class="cal-type type-eclipse">ECLIPSE</span></td>
            <td>Visible from Asia, Australia, parts of eastern Europe.</td>
        </tr>
        <tr>
            <td class="cal-date">AUG 12-13</td>
            <td><strong>Perseids Meteor Shower</strong></td>
            <td><span class="cal-type type-meteor">METEOR</span></td>
            <td>One of the best showers to observe, producing up to 60 meteors/hr.</td>
        </tr>
    </table>
    """, unsafe_allow_html=True)

def render_knowledge_hub():
    st.markdown('<h3 style="color: #58a6ff; font-family: \'Orbitron\', sans-serif; border-bottom: 1px solid rgba(88, 166, 255, 0.2); padding-bottom: 10px; margin-bottom: 20px; margin-top: 40px;">ASTRONOMY 101</h3>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    card_style = """
        <div style="background: rgba(22, 27, 34, 0.6); border: 1px solid rgba(88,166,255,0.15); border-radius: 12px; padding: 25px; height: 100%; transition: all 0.3s; box-shadow: 0 4px 20px rgba(0,0,0,0.2);">
            <div style="font-size: 2rem; margin-bottom: 15px;">{}</div>
            <h4 style="color: #ffffff; font-family: 'Orbitron', monospace; margin-top: 0; margin-bottom: 15px; font-size: 1.1rem;">{}</h4>
            <p style="color: #8b949e; font-size: 0.9rem; line-height: 1.6;">{}</p>
        </div>
    """
    
    with col1:
        st.markdown(card_style.format(
            "🌍", 
            "ORBIT TYPES", 
            "<b>LEO (Low Earth Orbit):</b> 160-2,000 km altitude. Ideal for imaging and ISS.<br><br><b>MEO (Medium Earth Orbit):</b> 2,000-35,786 km. Used by GPS/GNSS satellites.<br><br><b>GEO (Geostationary Orbit):</b> ~35,786 km. Satellites match Earth's rotation, appearing fixed."
        ), unsafe_allow_html=True)
        
    with col2:
         st.markdown(card_style.format(
            "🛰️", 
            "SATELLITE ANATOMY", 
            "<b>Payload:</b> Scientific instruments or communication antennas.<br><br><b>Bus:</b> The main body housing power, propulsion, and avionics.<br><br><b>Solar Arrays:</b> Panels converting sunlight into electrical power.<br><br><b>Attitude Control:</b> Sensors and thrusters mapping orientation."
        ), unsafe_allow_html=True)
         
    with col3:
         st.markdown(card_style.format(
            "📐", 
            "KEPLER'S LAWS", 
            "<b>Law of Ellipses:</b> The path of the planets about the sun is elliptical in shape.<br><br><b>Law of Equal Areas:</b> An imaginary line drawn from the center of the sun to the center of the planet will sweep out equal areas in equal intervals of time.<br><br><b>Law of Harmonies:</b> The ratio of the squares of the periods of any two planets is equal to the ratio of the cubes of their average distances from the sun."
        ), unsafe_allow_html=True)

def render_news_feed():
    st.markdown('<h3 style="color: #58a6ff; font-family: \'Orbitron\', sans-serif; border-bottom: 1px solid rgba(88, 166, 255, 0.2); padding-bottom: 10px; margin-bottom: 20px; margin-top: 40px;">NARIT NEWS FEED</h3>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: #161b22; border: 1px solid rgba(88, 166, 255, 0.1); border-radius: 8px; overflow: hidden; height: 250px; position: relative;">
        <style>
        @keyframes scroll {
            0% { transform: translateY(100%); }
            100% { transform: translateY(-100%); }
        }
        .news-item { padding: 15px 20px; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .news-date { color: #58a6ff; font-size: 0.75rem; font-family: monospace; margin-bottom: 5px; }
        .news-title { color: #c9d1d9; font-size: 0.95rem; font-weight: 600; margin: 0; transition: color 0.2s; cursor: pointer; }
        .news-title:hover { color: #fff; }
        .news-desc { color: #8b949e; font-size: 0.85rem; margin-top: 5px; line-height: 1.4; }
        </style>
        
        <div style="animation: scroll 30s linear infinite; position: absolute; width: 100%; top: 0;">
            <div class="news-item">
                <div class="news-date">MAR 11, 2026 | DISCOVERY</div>
                <h4 class="news-title">JWST Detects Water Vapor on Distant Exoplanet</h4>
                <div class="news-desc">The James Webb Space Telescope has identified clear signatures of water vapor in the atmosphere of K2-18b, a exoplanet located 124 light-years away in the habitable zone.</div>
            </div>
            <div class="news-item">
                <div class="news-date">MAR 08, 2026 | MISSION UPDATE</div>
                <h4 class="news-title">Artemis III Crew Manifest Announced</h4>
                <div class="news-desc">NASA has revealed the four astronauts who will pilot the Orion spacecraft for the Artemis III lunar landing mission scheduled for 2027.</div>
            </div>
            <div class="news-item">
                <div class="news-date">MAR 02, 2026 | OBSERVATION</div>
                <h4 class="news-title">New Near-Earth Asteroid Cataloged</h4>
                <div class="news-desc">A newly discovered near-earth object, designated 2026-XQ, safely passed Earth at a distance of 1.2 million miles. Trajectory mapped and archived.</div>
            </div>
             <div class="news-item">
                <div class="news-date">FEB 28, 2026 | TECHNOLOGY</div>
                <h4 class="news-title">Next-Gen Ion Thrusters Pass Endurance Tests</h4>
                <div class="news-desc">The experimental Hall-effect thrusters designed for deep space probes have successfully operated consecutively for over 10,000 hours in vacuum chambers.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def show_public_page():
    """The Gateway: New Immersive Pre-Dashboard"""
    
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600&display=swap');
    
    /* Clean Dark Space Mode Setup */
    .stApp {
        background-color: #0d1117;
        background-image: radial-gradient(circle at 10% 20%, rgba(20, 35, 60, 0.4) 0%, transparent 40%),
                          radial-gradient(circle at 90% 80%, rgba(40, 20, 60, 0.3) 0%, transparent 40%);
        color: #c9d1d9;
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide default header */
    header[data-testid="stHeader"] { display: none !important; }
    
    /* Center constraint for content */
    .block-container {
        padding-top: 2rem !important;
        max-width: 1200px !important;
    }
    
    /* Portal/Auth Section styling overrides */
    div[data-testid="stExpander"] {
        background: rgba(14, 17, 23, 0.8);
        border: 1px solid rgba(88, 166, 255, 0.3);
        border-radius: 12px;
        backdrop-filter: blur(10px);
    }
    div[data-testid="stExpander"] > summary p {
        font-family: 'Orbitron', monospace;
        font-weight: 700;
        font-size: 1.2rem;
        color: #58a6ff;
        letter-spacing: 2px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header Area
    st.markdown("""
    <div style="text-align: center; margin-bottom: 40px; margin-top: 20px;">
        <span style="font-size: 3rem;">🛰️</span>
        <h1 style="font-family: 'Orbitron', monospace; font-weight: 900; font-size: 3.5rem; margin: 0; letter-spacing: 4px; color: #fff; text-shadow: 0 0 20px rgba(88,166,255,0.4);">THE GATEWAY</h1>
        <p style="font-size: 1.2rem; color: #8b949e; letter-spacing: 1px; font-weight: 300;">VIRTUAL ASTRONOMY EXHIBITION & SYSTEM ACCESS</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 1. Active Event Banner
    render_banner()
    
    # Top Row: Calendar (left) and News (right)
    col_left, col_right = st.columns([1.5, 1])
    
    with col_left:
        # 2. Astronomical Calendar
        render_astronomical_calendar()
        
    with col_right:
        # 3. Interactive News Feed
        render_news_feed()
    
    # 4. Astronomy 101 Knowledge Hub
    render_knowledge_hub()
    
    st.markdown("<br><br><hr style='border-color: rgba(255,255,255,0.1);'><br>", unsafe_allow_html=True)
    
    # 5. The Portal (Auth Section)
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h2 style="font-family: 'Orbitron', monospace; color: #fff; letter-spacing: 3px; font-size: 2rem;">THE PORTAL</h2>
        <p style="color: #8b949e;">Secure entry point to the satellite telemetry dashboard.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Embed the original Auth logic directly inside an expander for 'The Portal' feel
    with st.expander("ENTER TO SYSTEM", expanded=False):
        from auth import login_user, social_login, register_user
        
        login_tab, reg_tab = st.tabs(["Login", "Register"])

        with login_tab:
            lc, rc = st.columns([1, 1])
            with lc:
                st.markdown("#### Mission Commander Access")
                le = st.text_input("Email", key="portal_login_email", placeholder="commander@mission.com")
                lp = st.text_input("Password", type="password", key="portal_login_pass")
                if st.button("AUTHENTICATE", use_container_width=True, type="primary"):
                    if le and lp:
                        ok, name, msg = login_user(le, lp)
                        if ok:
                            st.session_state.logged_in = True
                            st.session_state.username = name
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Please enter credentials.")
            with rc:
                st.markdown("#### Quick Access")
                if st.button("Continue with Google", use_container_width=True):
                    st.session_state["_social"] = "google"
                if st.button("Continue with Facebook", use_container_width=True):
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
            rn = r1.text_input("Display Name", key="portal_reg_name")
            re_email = r2.text_input("Email", key="portal_reg_email")
            rp = r1.text_input("Password", type="password", key="portal_reg_pass")
            rp2 = r2.text_input("Confirm Password", type="password", key="portal_reg_pass2")
            rm = st.radio("Sign up via", ["Email", "Google", "Facebook"], horizontal=True)
            if st.button("CREATE ACCOUNT", use_container_width=True, type="primary"):
                if not rn or not re_email:
                    st.warning("Fill all fields.")
                elif rp != rp2:
                    st.error("Passwords mismatch.")
                else:
                    ok, msg = register_user(re_email, rp, rn, rm.lower())
                    if ok:
                        st.success(f"{msg} You can log in now.")
                    else:
                        st.error(msg)
