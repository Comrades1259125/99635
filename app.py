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
from gateway import show_public_page
from auth import register_user, login_user, social_login
from i18n import t, lang_selector
from satellite_data import (
    SATELLITE_CATALOG, fetch_tle, compute_position,
    build_telemetry_40ch, compute_ground_track,
)

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Satellite Telemetry System",
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
    "user_email": "",
    "lang": "en",
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
    /* Hide Streamlit UI Elements */
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
# PRE-LOGIN PUBLIC PAGE — NARIT-inspired design (Moved to gateway.py)
# ─────────────────────────────────────────────────────────────────────────────


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
        req = urllib.request.Request(url, headers={"User-Agent": "SatTelemetry/1.0"})
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
@st.dialog(t("mission_archive"), width="large")
def mission_archive_control():
    dialog_sat = st.selectbox(
        t("select_satellite"),
        options=list(SATELLITE_CATALOG.keys()),
        index=list(SATELLITE_CATALOG.keys()).index(st.session_state.selected_satellite),
        key="dialog_satellite",
    )
    st.markdown(f"### {t('analyze_mission')} **{dialog_sat}**")

    # ── Cache toggle ──
    st.session_state.remember_archive = st.toggle(
        t("remember_cache"),
        value=st.session_state.get("remember_archive", False),
        key="remember_toggle",
    )

    if not st.session_state.download_ready:
        tab1, tab2 = st.tabs([t("realtime_report"), t("predictive_report")])

        with tab1:
            st.info(t("realtime_info"))
            if st.button(t("generate_realtime"), use_container_width=True, type="primary"):
                now = datetime.now()
                seq = random.randint(100, 999)
                ref_id = f"REF-{seq}-{now.strftime('%Y%m%d')}"
                passkey = f"{random.randint(100000, 999999)}"

                with st.spinner(t("generating_pdf")):
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
                        st.error(f"{t('error_occurred')} {e}")

        with tab2:
            st.write(t("predictive_info"))
            col1, col2 = st.columns(2)
            pred_date = col1.date_input(
                t("pred_date"), value=datetime.now(),
                key="pred_date_input",
            )
            pred_time = col2.time_input(
                t("pred_time"), value=datetime.now().time(),
                key="pred_time_input",
            )

            if st.button(t("calculate_predictive"), use_container_width=True):
                dt = datetime.combine(pred_date, pred_time).replace(tzinfo=timezone.utc)
                now = datetime.now()
                seq = random.randint(100, 999)
                ref_id = f"REF-{seq}-{now.strftime('%Y%m%d')}"
                passkey = f"{random.randint(100000, 999999)}"

                with st.spinner(t("calculating_pdf")):
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
                        st.error(f"{t('error_occurred')} {e}")

    else:
        # ── Download Ready — show Archive ID, Password, file info ──
        st.markdown(f"""
        <div style="background: white; padding: 30px; border-radius: 12px; text-align: center;
                    border: 1px solid #ccc; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <h3 style="color: #666; margin: 0; font-size: 0.8rem; letter-spacing: 3px;">SECURE ARCHIVE ACCESS</h3>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #888; font-size: 0.7rem; letter-spacing: 2px; margin-bottom: 5px;">{t('archive_id')}</p>
            <h1 style="color: #FF0000; font-family: 'Courier New', monospace; font-weight: 900;
                       margin: 0 0 20px 0;">{st.session_state.ref_id}</h1>
            <p style="color: #888; font-size: 0.7rem; letter-spacing: 2px; margin-bottom: 5px;">PASSWORD</p>
            <h2 style="color: #000; font-family: 'Courier New', monospace; font-weight: 700;
                       margin: 0 0 20px 0;">{st.session_state.passkey}</h2>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 10px 0;">
            <p style="color: #28a745; font-size: 0.9rem; font-weight: 700; margin: 0;">
                {t('pdf_ready')}</p>
            <p style="color: #666; font-size: 0.75rem; margin: 8px 0 0 0;">
                📂 {st.session_state.get('saved_pdf_filename', '')}</p>
        </div>
        """, unsafe_allow_html=True)

        st.write("")

        # Download Button replaces the local folder explorer
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            st.download_button(
                label=t("download_pdf"),
                data=st.session_state.get('cached_pdf', b''),
                file_name=st.session_state.get('saved_pdf_filename', 'report.pdf'),
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )

        with btn_col2:
            if st.button(t("new_report"), use_container_width=True):
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
            st.markdown(f"#### {t('send_email')}")
            recipient = st.text_input(
                t("recipient_email"),
                placeholder="recipient@example.com",
                key="email_recipient",
            )
            if st.button(t("send_email"), use_container_width=True, type="primary"):
                if not recipient:
                    st.warning(t("enter_recipient"))
                elif st.session_state.get("cached_pdf") is None:
                    st.error(t("no_pdf_found"))
                else:
                    with st.spinner(t("sending_email")):
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
            st.info(t("setup_gmail"))


# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
if not st.session_state.logged_in:
    st.markdown("""<style>section[data-testid="stSidebar"]{display:none}</style>""",
                unsafe_allow_html=True)
    show_public_page()
    st.stop()

with st.sidebar:
    lang_selector(location="sidebar")
    st.markdown(f"### {t('satellite_selection')}")
    st.session_state.selected_satellite = st.selectbox(
        t("select_target"),
        options=list(SATELLITE_CATALOG.keys()),
        index=0,
    )

    if st.session_state.selected_satellite != st.session_state.last_sat_name:
        with st.spinner(f"{t('fetching_tle')} {st.session_state.selected_satellite}..."):
            norad_id = SATELLITE_CATALOG[st.session_state.selected_satellite]
            st.session_state.satellite_obj = fetch_tle(
                st.session_state.selected_satellite, norad_id
            )
            st.session_state.last_sat_name = st.session_state.selected_satellite

    st.markdown("---")
    st.markdown(f"### {t('station_info')}")
    locked = st.session_state.station_locked

    st.session_state.sub_district = st.text_input(
        t("sub_district"), value=st.session_state.sub_district, disabled=locked
    )
    st.session_state.district = st.text_input(
        t("district"), value=st.session_state.district, disabled=locked
    )
    st.session_state.province = st.text_input(
        t("province"), value=st.session_state.province, disabled=locked
    )
    st.session_state.zip_code = st.text_input(
        t("zip_code"), value=st.session_state.zip_code, disabled=locked
    )
    st.session_state.country = st.text_input(
        t("country"), value=st.session_state.country, disabled=locked
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
        if st.button(t("search_coords"), use_container_width=True):
            full_addr = " ".join(filter(None, [
                st.session_state.sub_district,
                st.session_state.district,
                st.session_state.province,
                st.session_state.zip_code,
                st.session_state.country,
            ]))
            with st.spinner(t("searching_coords")):
                lat, lon = _geocode_address(full_addr)
            if lat is not None:
                st.session_state.station_lat = lat
                st.session_state.station_lon = lon
                st.success(f"{t('coords_found')} {lat:.6f}, {lon:.6f}")
                st.rerun()
            else:
                st.error(t("coords_not_found"))

    if not locked:
        if st.button(t("lock_station"), use_container_width=True):
            st.session_state.station_locked = True
            st.rerun()
    else:
        st.success(t("station_locked"))
        if st.button(t("unlock"), use_container_width=True):
            st.session_state.station_locked = False
            st.rerun()

    # ── Zoom Controls ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"### {t('map_zoom')}")
    st.session_state.zoom_tactical = st.slider(
        t("tactical_map"), 1, 18, st.session_state.zoom_tactical
    )
    st.session_state.zoom_global = st.slider(
        t("global_map"), 1, 18, st.session_state.zoom_global
    )
    st.session_state.zoom_station = st.slider(
        t("station_map"), 1, 18, st.session_state.zoom_station
    )
    st.session_state.zoom_globe = st.slider(
        t("globe_3d"), 1, 8, st.session_state.zoom_globe
    )

    st.markdown("---")
    if st.button(t("mission_archive"), use_container_width=True, type="primary"):
        mission_archive_control()

    # ── Email Settings ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"### {t('email_settings')}")
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
        st.success(t("email_configured"))
    else:
        st.info("Gmail + App Password")

    # ── Theme Toggle ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"### {t('theme')}")
    dark = st.toggle(t("dark_mode"), value=st.session_state.dark_mode, key="theme_toggle")
    st.session_state.dark_mode = dark

    # ── Alert System ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"### {t('alert_system')}")
    st.session_state.alerts_enabled = st.toggle(
        t("enable_alerts"), value=st.session_state.alerts_enabled,
        key="alert_toggle",
    )
    if st.session_state.alerts_enabled:
        st.session_state.alert_distance_km = st.slider(
            t("alert_distance"), 100, 5000,
            st.session_state.alert_distance_km, step=100,
        )
        if st.session_state.alert_log:
            with st.expander(t("alert_log"), expanded=False):
                for msg in reversed(st.session_state.alert_log[-10:]):
                    st.caption(msg)

    # ── Multi-Satellite Tracking ──────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"### {t('multi_satellite')}")
    tracked = st.multiselect(
        t("track_max5"),
        options=list(SATELLITE_CATALOG.keys()),
        default=st.session_state.tracked_satellites,
        max_selections=5,
        key="multi_sat_select",
    )
    st.session_state.tracked_satellites = tracked

    # ── Satellite Pass Prediction ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"### {t('pass_prediction')}")
    if st.button(t("calc_next_passes"), use_container_width=True):
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
                st.caption(t("no_passes"))
        else:
            st.caption(t("load_sat_first"))

    # ── User Status ──
    st.markdown("---")
    st.success(f"{t('logged_in_as')}{st.session_state.username}")
    if st.button(t("logout"), use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.user_email = ""
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
            st.markdown(f'<p class="telemetry-header">{t("multi_sat_tracking")}</p>', unsafe_allow_html=True)
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
            f'<p class="telemetry-header">{t("telemetry_40ch")}</p>',
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
                label=t("csv_export"),
                data=csv_data,
                file_name=f"telemetry_{sat_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with exp_col2:
            excel_buf = _io.BytesIO()
            telemetry_df.to_excel(excel_buf, index=False, engine="openpyxl")
            st.download_button(
                label=t("excel_export"),
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
            st.markdown(f'<p class="telemetry-header">{t("telemetry_history")}</p>', unsafe_allow_html=True)
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
                st.warning(f"{t('proximity_alert')}: {sat_name} — {dist_km:.0f} km!")

    else:
        st.warning(t("waiting_tle"))


live_dashboard()
