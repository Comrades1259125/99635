"""
i18n.py - Internationalization (Thai / English) for the entire system.
Usage:
    from i18n import t, lang_selector
    lang_selector()        # renders a TH/EN toggle
    label = t("login")     # returns the translated string
"""

import streamlit as st

# ─── Master Translation Dictionary ──────────────────────────────────────────
TRANSLATIONS = {
    # ── Gateway / Public Page ─────────────────────────────────────────────
    "the_gateway": {"en": "THE GATEWAY", "th": "THE GATEWAY"},
    "gateway_subtitle": {
        "en": "VIRTUAL ASTRONOMY EXHIBITION & SYSTEM ACCESS",
        "th": "นิทรรศการดาราศาสตร์เสมือนจริง & เข้าสู่ระบบ",
    },
    "active_event": {"en": "ACTIVE EVENT", "th": "ปรากฏการณ์ที่กำลังเกิดขึ้น"},
    "current_status": {"en": "CURRENT STATUS", "th": "สถานะปัจจุบัน"},
    "optimal_viewing": {"en": "🟢 OPTIMAL VIEWING", "th": "🟢 สภาพการสังเกตที่ดี"},
    "calendar_title": {"en": "ASTRONOMICAL CALENDAR 2026", "th": "ปฏิทินดาราศาสตร์ 2026"},
    "date": {"en": "Date", "th": "วันที่"},
    "event_name": {"en": "Event Name", "th": "ชื่อปรากฎการณ์"},
    "category": {"en": "Category", "th": "ประเภท"},
    "visibility_detail": {"en": "Visibility / Detail", "th": "การมองเห็น / รายละเอียด"},
    "astronomy_101": {"en": "ASTRONOMY 101", "th": "ดาราศาสตร์ 101"},
    "orbit_types": {"en": "ORBIT TYPES", "th": "ประเภทวงโคจร"},
    "satellite_anatomy": {"en": "SATELLITE ANATOMY", "th": "กายวิภาคดาวเทียม"},
    "keplers_laws": {"en": "KEPLER'S LAWS", "th": "กฎของเคปเลอร์"},
    "news_feed": {"en": "NEWS FEED", "th": "ข่าวสาร"},
    "the_portal": {"en": "THE PORTAL", "th": "THE PORTAL"},
    "portal_subtitle": {
        "en": "Secure entry point to the satellite telemetry dashboard.",
        "th": "จุดเข้าสู่ระบบแดชบอร์ดดาวเทียม",
    },
    "enter_system": {"en": "ENTER TO SYSTEM", "th": "เข้าสู่ระบบ"},

    # ── Auth ──────────────────────────────────────────────────────────────
    "login": {"en": "Login", "th": "เข้าสู่ระบบ"},
    "register": {"en": "Register", "th": "สมัครสมาชิก"},
    "email": {"en": "Email", "th": "อีเมล"},
    "password": {"en": "Password", "th": "รหัสผ่าน"},
    "confirm_password": {"en": "Confirm Password", "th": "ยืนยันรหัสผ่าน"},
    "display_name": {"en": "Display Name", "th": "ชื่อที่แสดง"},
    "authenticate": {"en": "AUTHENTICATE", "th": "ยืนยันตัวตน"},
    "create_account": {"en": "CREATE ACCOUNT", "th": "สร้างบัญชี"},
    "commander_access": {"en": "Mission Commander Access", "th": "เข้าสู่ระบบผู้บัญชาการ"},
    "quick_access": {"en": "Quick Access", "th": "เข้าสู่ระบบเร็ว"},
    "continue_google": {"en": "🔵 Continue with Google", "th": "🔵 เข้าสู่ระบบด้วย Google"},
    "continue_facebook": {"en": "🔵 Continue with Facebook", "th": "🔵 เข้าสู่ระบบด้วย Facebook"},
    "signup_via": {"en": "Sign up via", "th": "สมัครผ่าน"},
    "fill_all_fields": {"en": "Please fill in all fields.", "th": "กรุณากรอกข้อมูลให้ครบ"},
    "password_mismatch": {"en": "Passwords do not match.", "th": "รหัสผ่านไม่ตรงกัน"},
    "enter_credentials": {"en": "Please enter credentials.", "th": "กรุณากรอกข้อมูลเข้าสู่ระบบ"},
    "login_success": {"en": "Login successful!", "th": "เข้าสู่ระบบสำเร็จ!"},
    "register_success": {"en": "Registration successful! You can log in now.", "th": "สมัครสมาชิกสำเร็จ! สามารถเข้าสู่ระบบได้แล้ว"},

    # ── Dashboard / Sidebar ──────────────────────────────────────────────
    "satellite_selection": {"en": "🛰️ Satellite Selection", "th": "🛰️ เลือกดาวเทียม"},
    "select_target": {"en": "Select Target Satellite", "th": "เลือกดาวเทียมเป้าหมาย"},
    "station_info": {"en": "📡 Station Information", "th": "📡 ข้อมูลสถานี"},
    "sub_district": {"en": "Sub-district", "th": "ตำบล"},
    "district": {"en": "District", "th": "อำเภอ"},
    "province": {"en": "Province", "th": "จังหวัด"},
    "zip_code": {"en": "Zip Code", "th": "รหัสไปรษณีย์"},
    "country": {"en": "Country", "th": "ประเทศ"},
    "search_coords": {"en": "📍 Search Coordinates from Address", "th": "📍 ค้นหาพิกัดจากที่อยู่"},
    "lock_station": {"en": "✅ LOCK STATION", "th": "✅ ล็อกสถานี"},
    "unlock": {"en": "🔓 Unlock", "th": "🔓 ปลดล็อก"},
    "station_locked": {"en": "🔒 Station Locked", "th": "🔒 สถานีถูกล็อก"},
    "map_zoom": {"en": "🔍 Map Zoom Controls", "th": "🔍 ปรับระดับซูมแผนที่"},
    "tactical_map": {"en": "🗺️ Tactical Map", "th": "🗺️ แผนที่ยุทธวิธี"},
    "global_map": {"en": "🌍 Global Map", "th": "🌍 แผนที่โลก"},
    "station_map": {"en": "📡 Station Map", "th": "📡 แผนที่สถานี"},
    "globe_3d": {"en": "🌐 3D Globe Scale", "th": "🌐 มาตราส่วนลูกโลก 3D"},
    "mission_archive": {"en": "📦 MISSION ARCHIVE CONTROL", "th": "📦 ควบคุมคลังภารกิจ"},
    "email_settings": {"en": "📧 Email Settings (Gmail)", "th": "📧 ตั้งค่าอีเมล (Gmail)"},
    "theme": {"en": "Theme", "th": "ธีม"},
    "dark_mode": {"en": "Dark Mode", "th": "โหมดมืด"},
    "alert_system": {"en": "Alert System", "th": "ระบบแจ้งเตือน"},
    "enable_alerts": {"en": "Enable Proximity Alerts", "th": "เปิดการแจ้งเตือนระยะใกล้"},
    "alert_distance": {"en": "Alert Distance (km)", "th": "ระยะแจ้งเตือน (กม.)"},
    "alert_log": {"en": "Alert Log", "th": "บันทึกการแจ้งเตือน"},
    "multi_satellite": {"en": "Multi-Satellite", "th": "ติดตามหลายดวง"},
    "track_max5": {"en": "Track (max 5)", "th": "ติดตาม (สูงสุด 5)"},
    "pass_prediction": {"en": "Pass Prediction", "th": "ทำนายการผ่าน"},
    "calc_next_passes": {"en": "Calculate Next Passes", "th": "คำนวณการผ่านถัดไป"},
    "logged_in_as": {"en": "Logged in: ", "th": "เข้าสู่ระบบ: "},
    "logout": {"en": "LOGOUT", "th": "ออกจากระบบ"},
    "language": {"en": "Language", "th": "ภาษา"},

    # ── Telemetry ─────────────────────────────────────────────────────────
    "telemetry_40ch": {"en": "TELEMETRY DATA - 40 CHANNELS", "th": "ข้อมูลเทเลเมทรี - 40 ช่อง"},
    "telemetry_history": {"en": "TELEMETRY HISTORY", "th": "ประวัติเทเลเมทรี"},
    "multi_sat_tracking": {"en": "MULTI-SATELLITE TRACKING", "th": "ติดตามดาวเทียมหลายดวง"},
    "csv_export": {"en": "CSV Export", "th": "ส่งออก CSV"},
    "excel_export": {"en": "Excel Export", "th": "ส่งออก Excel"},
    "waiting_tle": {"en": "Waiting for TLE data...", "th": "กำลังรอข้อมูล TLE..."},
    "proximity_alert": {"en": "PROXIMITY ALERT", "th": "แจ้งเตือนระยะใกล้"},
    "no_passes": {"en": "No passes in next 24h", "th": "ไม่มีการผ่านใน 24 ชั่วโมงถัดไป"},
    "load_sat_first": {"en": "Load satellite first", "th": "โหลดดาวเทียมก่อน"},

    # ── Mission Archive Dialog ────────────────────────────────────────────
    "select_satellite": {"en": "🛰️ Select Satellite", "th": "🛰️ เลือกดาวเทียม"},
    "analyze_mission": {"en": "📦 Analyze mission for:", "th": "📦 วิเคราะห์ภารกิจสำหรับ:"},
    "remember_cache": {"en": "💾 Remember cached report", "th": "💾 จดจำไฟล์ที่คำนวณไว้"},
    "realtime_report": {"en": "🔄 Real-time Report", "th": "🔄 รายงานปัจจุบัน"},
    "predictive_report": {"en": "📅 Predictive Report", "th": "📅 รายงานล่วงหน้า"},
    "generate_realtime": {"en": "🚀 GENERATE REAL-TIME PDF", "th": "🚀 สร้าง PDF ปัจจุบัน"},
    "calculate_predictive": {"en": "📅 CALCULATE & DOWNLOAD PREDICTIVE PDF", "th": "📅 คำนวณและดาวน์โหลด PDF ล่วงหน้า"},
    "download_pdf": {"en": "📥 Download PDF", "th": "📥 ดาวน์โหลด PDF"},
    "new_report": {"en": "🔙 New Report", "th": "🔙 สร้างรายงานใหม่"},
    "send_email": {"en": "📧 SEND EMAIL", "th": "📧 ส่งอีเมล"},
    "recipient_email": {"en": "Recipient Email", "th": "อีเมลผู้รับ"},
    "generating_pdf": {"en": "Generating PDF with QR Code...", "th": "กำลังสร้างรายงาน PDF พร้อม QR Code..."},
    "calculating_pdf": {"en": "Calculating predictive position and generating PDF...", "th": "กำลังคำนวณตำแหน่งล่วงหน้าและสร้าง PDF..."},
    "email_configured": {"en": "Email configured", "th": "ตั้งค่าอีเมลแล้ว"},
    "setup_gmail": {"en": "📧 Setup Gmail + App Password in Sidebar to send Email", "th": "📧 ตั้งค่า Gmail + App Password ใน Sidebar เพื่อส่ง Email"},

    # ── Admin / Content Management ────────────────────────────────────────
    "admin_panel": {"en": "⚙️ Admin: Edit Gateway Content", "th": "⚙️ แอดมิน: แก้ไขเนื้อหา Gateway"},
    "add_event": {"en": "Add Calendar Event", "th": "เพิ่มปรากฏการณ์"},
    "add_news": {"en": "Add News Item", "th": "เพิ่มข่าว"},
    "add_article": {"en": "Add Article", "th": "เพิ่มบทความ"},
    "save": {"en": "💾 Save", "th": "💾 บันทึก"},
    "delete": {"en": "🗑️ Delete", "th": "🗑️ ลบ"},
    "title": {"en": "Title", "th": "หัวข้อ"},
    "body": {"en": "Body", "th": "เนื้อหา"},
    "image_url": {"en": "Image URL", "th": "URL รูปภาพ"},
    "content_saved": {"en": "Content saved!", "th": "บันทึกเนื้อหาแล้ว!"},
    "realtime_info": {"en": "System will generate report from current position (Real-time)", "th": "ระบบจะสร้างรายงานจากตำแหน่งปัจจุบัน (Real-time)"},
    "predictive_info": {"en": "Specify date/time for predictive position analysis", "th": "ระบุวันเวลาที่ต้องการวิเคราะห์ตำแหน่งล่วงหน้า"},
    "pred_date": {"en": "Date", "th": "วันที่"},
    "pred_time": {"en": "Time", "th": "เวลา"},
    "error_occurred": {"en": "❌ Error:", "th": "❌ เกิดข้อผิดพลาด:"},
    "pdf_ready": {"en": "✅ PDF ready for download (with QR verification)", "th": "✅ ไฟล์ PDF พร้อมสำหรับดาวน์โหลด (พร้อม QR Code ตรวจสอบ)"},
    "archive_id": {"en": "ARCHIVE ID", "th": "รหัสเอกสาร"},
    "sending_email": {"en": "Sending email...", "th": "กำลังส่งอีเมล..."},
    "enter_recipient": {"en": "Please enter recipient email", "th": "กรุณาใส่ Email ผู้รับ"},
    "no_pdf_found": {"en": "No PDF file found", "th": "ไม่พบไฟล์ PDF"},
    "fetching_tle": {"en": "Fetching TLE for", "th": "กำลังดึงข้อมูล TLE สำหรับ"},
    "searching_coords": {"en": "Searching coordinates...", "th": "กำลังค้นหาพิกัด..."},
    "coords_found": {"en": "Coordinates found:", "th": "พบพิกัด:"},
    "coords_not_found": {"en": "Coordinates not found from the given address", "th": "ไม่พบพิกัดจากที่อยู่ที่กรอก"},

    # ── Knowledge Hub content ─────────────────────────────────────────────
    "orbit_leo": {
        "en": "<b>LEO (Low Earth Orbit):</b> 160-2,000 km altitude. Ideal for imaging and ISS.",
        "th": "<b>LEO (วงโคจรต่ำ):</b> ความสูง 160-2,000 กม. เหมาะสำหรับการถ่ายภาพและ ISS",
    },
    "orbit_meo": {
        "en": "<b>MEO (Medium Earth Orbit):</b> 2,000-35,786 km. Used by GPS/GNSS satellites.",
        "th": "<b>MEO (วงโคจรกลาง):</b> 2,000-35,786 กม. ใช้โดยดาวเทียม GPS/GNSS",
    },
    "orbit_geo": {
        "en": "<b>GEO (Geostationary Orbit):</b> ~35,786 km. Satellites match Earth's rotation, appearing fixed.",
        "th": "<b>GEO (วงโคจรค้างฟ้า):</b> ~35,786 กม. ดาวเทียมหมุนตามโลก ดูเหมือนอยู่กับที่",
    },
    "sat_payload": {
        "en": "<b>Payload:</b> Scientific instruments or communication antennas.",
        "th": "<b>Payload:</b> เครื่องมือวิทยาศาสตร์หรือเสาอากาศสื่อสาร",
    },
    "sat_bus": {
        "en": "<b>Bus:</b> The main body housing power, propulsion, and avionics.",
        "th": "<b>Bus:</b> ตัวถังหลักที่บรรจุระบบพลังงาน ขับเคลื่อน และอิเล็กทรอนิกส์",
    },
    "sat_solar": {
        "en": "<b>Solar Arrays:</b> Panels converting sunlight into electrical power.",
        "th": "<b>Solar Arrays:</b> แผงรับแสงอาทิตย์แปลงเป็นพลังงานไฟฟ้า",
    },
    "sat_attitude": {
        "en": "<b>Attitude Control:</b> Sensors and thrusters mapping orientation.",
        "th": "<b>Attitude Control:</b> เซ็นเซอร์และตัวขับเคลื่อนควบคุมทิศทาง",
    },
    "kepler_1": {
        "en": "<b>Law of Ellipses:</b> The path of the planets about the sun is elliptical in shape.",
        "th": "<b>กฎวงรี:</b> เส้นทางของดาวเคราะห์รอบดวงอาทิตย์เป็นรูปวงรี",
    },
    "kepler_2": {
        "en": "<b>Law of Equal Areas:</b> A line from the sun to a planet sweeps out equal areas in equal times.",
        "th": "<b>กฎพื้นที่เท่ากัน:</b> เส้นตรงจากดวงอาทิตย์ถึงดาวเคราะห์กวาดพื้นที่เท่ากันในเวลาเท่ากัน",
    },
    "kepler_3": {
        "en": "<b>Law of Harmonies:</b> The square of the period is proportional to the cube of the semi-major axis.",
        "th": "<b>กฎความสัมพันธ์:</b> กำลังสองของคาบเป็นสัดส่วนกับกำลังสามของกึ่งแกนเอก",
    },
}


def _get_lang() -> str:
    """Get current language from session state."""
    return st.session_state.get("lang", "en")


def t(key: str) -> str:
    """Translate a key into the current language."""
    lang = _get_lang()
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key  # fallback: return the key itself
    return entry.get(lang, entry.get("en", key))


def lang_selector(location: str = "sidebar"):
    """Render a TH/EN language toggle."""
    if "lang" not in st.session_state:
        st.session_state.lang = "en"

    options = {"en": "🇬🇧 English", "th": "🇹🇭 ภาษาไทย"}
    current = st.session_state.lang

    if location == "sidebar":
        choice = st.sidebar.radio(
            t("language"),
            list(options.keys()),
            format_func=lambda x: options[x],
            index=list(options.keys()).index(current),
            key="lang_radio_sidebar",
            horizontal=True,
        )
    else:
        choice = st.radio(
            t("language"),
            list(options.keys()),
            format_func=lambda x: options[x],
            index=list(options.keys()).index(current),
            key="lang_radio_main",
            horizontal=True,
        )

    if choice != current:
        st.session_state.lang = choice
        st.rerun()
