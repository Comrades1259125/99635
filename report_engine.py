"""
report_engine.py — Mission Archive Report Generation
Matches Figure 3 layout with 40-channel telemetry and dual map images.
Real-time satellite data from CelesTrak / Skyfield.
"""

import io
import os
import random
import tempfile
import hashlib
from datetime import datetime, timezone
import streamlit as st
from fpdf import FPDF
from pypdf import PdfReader, PdfWriter
import plotly.graph_objects as go
import pandas as pd
import qrcode
from PIL import Image


class _MissionPDF(FPDF):
    """Custom FPDF subclass for Mission Archive Analysis."""

    def __init__(self, sat_name, archive_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sat_name = sat_name
        self.archive_id = archive_id
        # Register Unicode font — try multiple platforms
        self._has_unicode_font = False
        import sys
        font_candidates = []
        if sys.platform == "win32":
            font_candidates = [
                (r"C:\Windows\Fonts\tahoma.ttf", r"C:\Windows\Fonts\tahomabd.ttf"),
                (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf"),
            ]
        elif sys.platform == "darwin":
            font_candidates = [
                ("/Library/Fonts/Arial Unicode.ttf", "/Library/Fonts/Arial Unicode.ttf"),
                ("/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/Helvetica.ttc"),
            ]
        else:  # Linux
            font_candidates = [
                ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
                ("/usr/share/fonts/truetype/freefont/FreeSans.ttf", "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"),
            ]
        for regular, bold in font_candidates:
            try:
                self.add_font("UniFont", "", regular)
                self.add_font("UniFont", "B", bold)
                self.add_font("UniFont", "I", regular)  # fallback italic
                self._has_unicode_font = True
                break
            except Exception:
                continue

    def _font(self, style="", size=8):
        """Set font - always uses Unicode font when available."""
        if self._has_unicode_font:
            self.set_font("UniFont", style, size)
        else:
            self.set_font("Helvetica", style, size)

    def header(self):
        self._font("B", 16)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, f"MISSION DATA ANALYSIS REPORT: {self.sat_name.upper()}", align="C", ln=True)

        self._font("", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, f"Calculation Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC", align="C", ln=True)

        self.ln(1)

        self._font("B", 10)
        self.set_text_color(80, 80, 80)
        self.cell(0, 6, f"Archive ID: {self.archive_id}", align="C", ln=True)

        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self._font("I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} | ระบบติดตามดาวเทียม | ID: {self.archive_id}", align="C")


def _generate_map_image(lat, lon, sat_name="SAT", style="tactical") -> bytes:
    """Generate a map PNG for embedding in PDF using real satellite position."""
    import urllib.request

    if style == "tactical":
        # Download static satellite image from Esri REST API
        try:
            delta = 8  # degrees around the point
            xmin, ymin = lon - delta, lat - delta
            xmax, ymax = lon + delta, lat + delta
            esri_url = (
                "https://server.arcgisonline.com/ArcGIS/rest/services/"
                "World_Imagery/MapServer/export?"
                f"bbox={xmin},{ymin},{xmax},{ymax}"
                "&bboxSR=4326&imageSR=4326"
                "&size=600,400&format=png&f=image"
            )
            req = urllib.request.Request(esri_url, headers={"User-Agent": "SatelliteTelemetry/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                bg_bytes = resp.read()

            # Composite a marker dot on top using PIL
            from PIL import Image, ImageDraw, ImageFont
            bg_img = Image.open(io.BytesIO(bg_bytes)).convert("RGBA")
            draw = ImageDraw.Draw(bg_img)

            # Convert lat/lon to pixel coordinates
            px = int((lon - xmin) / (xmax - xmin) * 600)
            py = int((ymax - lat) / (ymax - ymin) * 400)

            # Draw marker (red circle with white border)
            r = 12
            draw.ellipse([px-r-2, py-r-2, px+r+2, py+r+2], fill="white")
            draw.ellipse([px-r, py-r, px+r, py+r], fill="#ff4444")

            # Draw satellite name label
            try:
                font = ImageFont.truetype("arial.ttf", 14)
            except Exception:
                font = ImageFont.load_default()
            draw.text((px + 15, py - 10), sat_name, fill="white", font=font,
                       stroke_width=2, stroke_fill="black")

            out = io.BytesIO()
            bg_img.save(out, format="PNG")
            return out.getvalue()
        except Exception:
            # Fallback to Plotly dark map if Esri fails
            pass

    # Global map or fallback: use Plotly with built-in style
    fig = go.Figure()
    marker_color = "#ff4444" if style == "tactical" else "#58a6ff"
    fig.add_trace(go.Scattermap(
        lat=[lat], lon=[lon],
        mode="markers+text",
        marker=dict(size=18, color=marker_color, symbol="rocket"),
        text=[sat_name],
        textposition="top center",
        textfont=dict(size=14, color="white"),
    ))

    map_style = "carto-darkmatter" if style == "tactical" else "open-street-map"
    zoom = 3 if style == "tactical" else 1
    fig.update_layout(
        map=dict(
            style=map_style,
            center=dict(lat=lat, lon=lon),
            zoom=zoom,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        width=600,
        height=400,
    )
    return fig.to_image(format="png")


def generate_pdf(
    telemetry_df,
    station_info,
    archive_id,
    passkey,
    sat_name,
    is_predictive=False,
    sat_position=None,
    norad_id=None,
    pred_dt=None,
):
    """Generate the Mission Archive PDF matching Figure 3.
    
    Args:
        telemetry_df: 40-channel telemetry DataFrame
        station_info: dict with ground station fields
        archive_id: unique REF-xxx-YYYYMMDD string
        passkey: 6-digit encryption password
        sat_name: selected satellite name
        is_predictive: True if predictive mode
        sat_position: dict with lat/lon/alt_km from compute_position()
        norad_id: NORAD catalog ID
        pred_dt: predictive datetime (None for real-time)
    """
    pdf = _MissionPDF(sat_name, archive_id)
    pdf.alias_nb_pages()
    pdf.add_page()

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    mode_str = "Predictive Analysis" if is_predictive else "Real-time Current"

    # ── Export Mode & Date ────────────────────────────────────────────────────
    pdf._font("B", 9)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 6, f"Export Mode: {mode_str}", align="C", ln=True)
    pdf.ln(2)

    if is_predictive and pred_dt:
        pdf._font("", 9)
        pdf.cell(0, 5, f"Predicted Time: {pred_dt.strftime('%Y-%m-%d %H:%M:%S')} UTC", align="C", ln=True)
        pdf.ln(2)

    # ── GROUND STATION IDENTIFICATION ────────────────────────────────────────
    pdf.set_fill_color(230, 230, 230)
    pdf._font("B", 9)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, "GROUND STATION IDENTIFICATION", ln=True, fill=True)
    pdf.ln(2)

    pdf._font("", 8)
    pdf.set_text_color(40, 40, 40)
    station_fields = [
        ("Building/ID", "Royal Command Center"),
        ("District", station_info.get("district", "")),
        ("Province", station_info.get("province", "")),
        ("Country", station_info.get("country", "")),
    ]
    for label, value in station_fields:
        pdf._font("B", 8)
        pdf.cell(35, 5, f"{label}:", border=0)
        pdf._font("", 8)
        pdf.cell(0, 5, value, border=0, ln=True)
    pdf.ln(4)

    # ── SATELLITE INFORMATION ────────────────────────────────────────────────
    pdf.set_fill_color(230, 230, 230)
    pdf._font("B", 9)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, "SATELLITE INFORMATION", ln=True, fill=True)
    pdf.ln(2)

    pdf._font("", 8)
    pdf.set_text_color(40, 40, 40)
    sat_fields = [
        ("Satellite", sat_name),
        ("NORAD ID", str(norad_id) if norad_id else "N/A"),
        ("Data Source", "CelesTrak / NORAD TLE (Real-time)"),
        ("Map Data", "Real-time satellite position on all maps (except Station Map)"),
    ]
    if sat_position:
        sat_fields.insert(2, ("Position", f"Lat {sat_position['lat']:.4f} deg, Lon {sat_position['lon']:.4f} deg, Alt {sat_position['alt_km']:.2f} km"))
    for label, value in sat_fields:
        pdf._font("B", 8)
        pdf.cell(35, 5, f"{label}:", border=0)
        pdf._font("", 8)
        pdf.cell(0, 5, value, border=0, ln=True)
    pdf.ln(4)

    # ── TELEMETRY MATRIX (4 columns) ─────────────────────────────────────────
    pdf.set_fill_color(240, 240, 240)
    pdf._font("B", 8)
    pdf.cell(0, 6, "TECHNICAL TELEMETRY MATRIX (40 UNIQUE CHANNELS)", ln=True, align="C", fill=True)
    pdf.ln(2)

    pdf._font("", 7)
    params = telemetry_df.to_dict("records")
    for i in range(0, len(params), 4):
        chunk = params[i : i + 4]
        for item in chunk:
            label = f"{item['Parameter'][:12]}:"
            val = f"{item['Value']} {item['Unit']}"
            pdf._font("B", 7)
            pdf.cell(20, 5, label, border=0)
            pdf._font("", 7)
            pdf.cell(27, 5, val, border=0)
        pdf.ln(5)

    pdf.ln(6)

    # ── MAP IMAGES (Two maps: Tactical + Global) ────────────────────────────
    # Get lat/lon from satellite position or telemetry
    if sat_position:
        lat, lon = sat_position["lat"], sat_position["lon"]
    else:
        lat_row = telemetry_df[telemetry_df["Parameter"] == "LATITUDE"]["Value"].values[0]
        lon_row = telemetry_df[telemetry_df["Parameter"] == "LONGITUDE"]["Value"].values[0]
        lat, lon = float(lat_row), float(lon_row)

    # Map 1: Tactical Map (dark, zoomed)
    pdf._font("B", 8)
    pdf.set_text_color(0, 0, 0)
    map_y = pdf.get_y()

    # Check if we need a new page for maps
    if map_y + 55 > pdf.h - 20:
        pdf.add_page()
        map_y = pdf.get_y()

    pdf.cell(90, 5, "TACTICAL VIEW - Satellite Imagery (Real-time)", border=0, align="C")
    pdf.cell(10, 5, "", border=0)  # spacer
    pdf.cell(90, 5, "GLOBAL VIEW (Real-time)", border=0, align="C", ln=True)
    map_y = pdf.get_y()

    try:
        tac_bytes = _generate_map_image(lat, lon, sat_name, "tactical")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tac_tmp:
            tac_tmp.write(tac_bytes)
            tac_path = tac_tmp.name
        pdf.image(tac_path, x=10, y=map_y, w=90)
        os.unlink(tac_path)
    except Exception:
        pdf.set_xy(10, map_y)
        pdf.cell(90, 40, "[Tactical Map - Real-time Data]", border=1, align="C")

    try:
        glob_bytes = _generate_map_image(lat, lon, sat_name, "global")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as glob_tmp:
            glob_tmp.write(glob_bytes)
            glob_path = glob_tmp.name
        pdf.image(glob_path, x=110, y=map_y, w=90)
        os.unlink(glob_path)
    except Exception:
        pdf.set_xy(110, map_y)
        pdf.cell(90, 40, "[Global Map - Real-time Data]", border=1, align="C")

    pdf.ln(50)

    # ── DATA SOURCE NOTE ─────────────────────────────────────────────────────
    pdf._font("I", 7)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(
        0,
        4,
        "NOTE: All map views display real-time satellite position data calculated from NORAD TLE elements "
        "(CelesTrak). The Station Map on the live dashboard shows the fixed ground station location and does "
        "not reflect satellite position. Data refreshes every 1 second on the live system.",
    )
    pdf.ln(3)

    # ── QR CODE — Document Verification ──────────────────────────────────────
    qr_y = pdf.get_y()
    if qr_y + 50 > pdf.h - 20:
        pdf.add_page()
        qr_y = pdf.get_y()

    # Generate verification hash
    verify_ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    raw_str = f"{archive_id}|{passkey}|{sat_name}|{verify_ts}"
    verify_hash = hashlib.sha256(raw_str.encode()).hexdigest()[:16]
    qr_payload = f"SAT-VERIFY|ID:{archive_id}|HASH:{verify_hash}|SAT:{sat_name}|TS:{verify_ts}"

    qr_img = qrcode.make(qr_payload, box_size=6, border=2)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as qr_tmp:
        qr_img.save(qr_tmp, format="PNG")
        qr_path = qr_tmp.name

    pdf._font("B", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 5, "DOCUMENT VERIFICATION", ln=True, align="C")
    pdf.ln(2)

    qr_x = (pdf.w - 35) / 2  # center the QR code
    pdf.image(qr_path, x=qr_x, y=pdf.get_y(), w=35)
    os.unlink(qr_path)
    pdf.ln(38)

    pdf._font("I", 7)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 4, "Scan QR code to verify document authenticity", align="C", ln=True)
    pdf._font("", 6)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 4, f"Verification Hash: {verify_hash}", align="C", ln=True)
    pdf.ln(4)

    # ── SECURITY NOTICE ──────────────────────────────────────────────────────
    pdf._font("I", 7)
    pdf.set_text_color(200, 0, 0)
    pdf.multi_cell(
        0,
        4,
        "NOTICE: This document is encrypted and contains sensitive mission-critical telemetry. "
        "Unauthorized distribution is prohibited.",
    )

    # ── FINAL OUTPUT & ENCRYPTION ────────────────────────────────────────────
    raw_buf = io.BytesIO()
    pdf.output(raw_buf)
    raw_buf.seek(0)

    reader = PdfReader(raw_buf)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    # Encrypt with 6-digit passkey
    writer.encrypt(user_password=passkey, owner_password=passkey, use_128bit=True)

    enc_buf = io.BytesIO()
    writer.write(enc_buf)
    enc_buf.seek(0)
    return enc_buf.getvalue()
