"""
gateway.py - The Gateway: Immersive Pre-Dashboard
Features: Bilingual, editable content, real Google/Facebook OAuth.
"""

import streamlit as st
import json
import os
from datetime import datetime

from i18n import t, lang_selector
from auth import (
    login_user, register_user, social_login,
    google_auth_url, google_handle_callback,
    facebook_auth_url, facebook_handle_callback,
    is_admin,
)

CONTENT_FILE = os.path.join(os.path.dirname(__file__), "gateway_content.json")


# ═══════════════════════════════════════════════════════════════════════
#  Content CRUD helpers
# ═══════════════════════════════════════════════════════════════════════

def _load_content() -> dict:
    if os.path.exists(CONTENT_FILE):
        with open(CONTENT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"banner": {}, "calendar": [], "news": [], "articles": []}


def _save_content(data: dict):
    with open(CONTENT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _l(item: dict, field: str) -> str:
    """Get field_en or field_th based on current language."""
    lang = st.session_state.get("lang", "en")
    return item.get(f"{field}_{lang}", item.get(f"{field}_en", ""))


# ═══════════════════════════════════════════════════════════════════════
#  OAuth callback handler  (runs once at page load)
# ═══════════════════════════════════════════════════════════════════════

def _handle_oauth_callback():
    """Check URL query params for OAuth callback codes."""
    params = st.query_params
    code = params.get("code")
    oauth_state = st.session_state.get("_oauth_provider", "")

    if code and oauth_state == "google":
        user_info = google_handle_callback(code)
        if user_info:
            ok, name = social_login(user_info["email"], user_info["name"], "google")
            st.session_state.logged_in = True
            st.session_state.username = name
            st.session_state.user_email = user_info["email"]
            st.session_state["_oauth_provider"] = ""
            st.query_params.clear()
            st.rerun()

    elif code and oauth_state == "facebook":
        user_info = facebook_handle_callback(code)
        if user_info:
            ok, name = social_login(user_info["email"], user_info["name"], "facebook")
            st.session_state.logged_in = True
            st.session_state.username = name
            st.session_state.user_email = user_info["email"]
            st.session_state["_oauth_provider"] = ""
            st.query_params.clear()
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════
#  Section Renderers
# ═══════════════════════════════════════════════════════════════════════

def render_banner(content):
    banner = content.get("banner", {})
    icon = banner.get("icon", "☄️")
    title = _l(banner, "title") or "Active Event"
    desc = _l(banner, "desc") or ""
    status = _l(banner, "status") or "🟢"

    st.markdown(f"""
    <div style="background: linear-gradient(90deg, #111b2b, #1a2842); padding: 20px; border-radius: 12px;
                border-left: 5px solid #58a6ff; margin-bottom: 25px; display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 15px;">
            <div style="background: rgba(88,166,255,0.2); padding: 10px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                <span style="font-size: 1.5rem; color: #58a6ff;">{icon}</span>
            </div>
            <div>
                <h3 style="margin: 0; color: #fff; font-family: 'Orbitron', sans-serif; letter-spacing: 1px;">
                    {t("active_event")}: {title}</h3>
                <p style="margin: 5px 0 0 0; color: #a5d8ff; font-size: 0.9rem;">{desc}</p>
            </div>
        </div>
        <div style="text-align: right; color: rgba(255,255,255,0.5); font-size: 0.8rem;">
            <div>{t("current_status")}</div>
            <div style="color: #4CAF50; font-weight: bold;">{status}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_calendar(content):
    events = content.get("calendar", [])
    st.markdown(f"""
    <h3 style="color: #58a6ff; font-family: 'Orbitron', sans-serif; border-bottom: 1px solid rgba(88, 166, 255, 0.2);
               padding-bottom: 10px; margin-bottom: 20px;">{t("calendar_title")}</h3>
    """, unsafe_allow_html=True)

    # Build table rows
    rows = ""
    for ev in events:
        rows += f"""
        <tr>
            <td class="cal-date">{ev.get('date','')}</td>
            <td><strong>{_l(ev, 'name')}</strong></td>
            <td><span class="cal-type {ev.get('category_class','')}">{ev.get('category','')}</span></td>
            <td>{_l(ev, 'detail')}</td>
        </tr>"""

    st.markdown(f"""
    <style>
    .cal-table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; font-family: 'Inter', sans-serif; font-size: 0.9rem; }}
    .cal-table th {{ text-align: left; padding: 12px 15px; border-bottom: 2px solid rgba(88,166,255,0.3); color: #8b949e; text-transform: uppercase; letter-spacing: 1px; }}
    .cal-table td {{ padding: 15px; border-bottom: 1px solid rgba(255,255,255,0.05); color: #c9d1d9; }}
    .cal-table tr:hover td {{ background: rgba(88,166,255,0.05); }}
    .cal-date {{ font-family: 'Orbitron', monospace; color: #58a6ff; font-weight: 700; width: 120px; }}
    .cal-type {{ display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 600; }}
    .type-eclipse {{ background: rgba(255, 87, 34, 0.2); color: #FF5722; border: 1px solid rgba(255, 87, 34, 0.5); }}
    .type-equinox {{ background: rgba(76, 175, 80, 0.2); color: #4CAF50; border: 1px solid rgba(76, 175, 80, 0.5); }}
    .type-meteor {{ background: rgba(3, 169, 244, 0.2); color: #03A9F4; border: 1px solid rgba(3, 169, 244, 0.5); }}
    </style>
    <table class="cal-table">
        <tr>
            <th>{t("date")}</th>
            <th>{t("event_name")}</th>
            <th>{t("category")}</th>
            <th>{t("visibility_detail")}</th>
        </tr>
        {rows}
    </table>
    """, unsafe_allow_html=True)


def render_knowledge_hub():
    st.markdown(f'<h3 style="color: #58a6ff; font-family: \'Orbitron\', sans-serif; border-bottom: 1px solid rgba(88,166,255,0.2); padding-bottom: 10px; margin-bottom: 20px; margin-top: 40px;">{t("astronomy_101")}</h3>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    card = """
        <div style="background: rgba(22,27,34,0.6); border: 1px solid rgba(88,166,255,0.15); border-radius: 12px; padding: 25px; height: 100%; box-shadow: 0 4px 20px rgba(0,0,0,0.2);">
            <div style="font-size: 2rem; margin-bottom: 15px;">{icon}</div>
            <h4 style="color: #fff; font-family: 'Orbitron', monospace; margin-top: 0; margin-bottom: 15px; font-size: 1.1rem;">{title}</h4>
            <p style="color: #8b949e; font-size: 0.9rem; line-height: 1.6;">{body}</p>
        </div>
    """

    with col1:
        st.markdown(card.format(
            icon="🌍", title=t("orbit_types"),
            body=f"{t('orbit_leo')}<br><br>{t('orbit_meo')}<br><br>{t('orbit_geo')}",
        ), unsafe_allow_html=True)

    with col2:
        st.markdown(card.format(
            icon="🛰️", title=t("satellite_anatomy"),
            body=f"{t('sat_payload')}<br><br>{t('sat_bus')}<br><br>{t('sat_solar')}<br><br>{t('sat_attitude')}",
        ), unsafe_allow_html=True)

    with col3:
        st.markdown(card.format(
            icon="📐", title=t("keplers_laws"),
            body=f"{t('kepler_1')}<br><br>{t('kepler_2')}<br><br>{t('kepler_3')}",
        ), unsafe_allow_html=True)


def render_news_feed(content):
    news = content.get("news", [])
    st.markdown(f'<h3 style="color: #58a6ff; font-family: \'Orbitron\', sans-serif; border-bottom: 1px solid rgba(88,166,255,0.2); padding-bottom: 10px; margin-bottom: 20px; margin-top: 40px;">{t("news_feed")}</h3>', unsafe_allow_html=True)

    items_html = ""
    for n in news:
        tag = _l(n, "tag")
        items_html += f"""
        <div class="news-item">
            <div class="news-date">{n.get('date','')} | {tag}</div>
            <h4 class="news-title">{_l(n, 'title')}</h4>
            <div class="news-desc">{_l(n, 'desc')}</div>
        </div>"""

    st.markdown(f"""
    <div style="background: #161b22; border: 1px solid rgba(88,166,255,0.1); border-radius: 8px; overflow: hidden; height: 250px; position: relative;">
        <style>
        @keyframes gw-scroll {{ 0% {{ transform: translateY(0); }} 100% {{ transform: translateY(-50%); }} }}
        .news-item {{ padding: 15px 20px; border-bottom: 1px solid rgba(255,255,255,0.05); }}
        .news-date {{ color: #58a6ff; font-size: 0.75rem; font-family: monospace; margin-bottom: 5px; }}
        .news-title {{ color: #c9d1d9; font-size: 0.95rem; font-weight: 600; margin: 0; }}
        .news-desc {{ color: #8b949e; font-size: 0.85rem; margin-top: 5px; line-height: 1.4; }}
        </style>
        <div style="animation: gw-scroll 30s linear infinite; position: absolute; width: 100%; top: 0;">
            {items_html}
            {items_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════
#  Admin Content Editor (dialog)
# ═══════════════════════════════════════════════════════════════════════

@st.dialog(t("admin_panel"), width="large")
def admin_content_editor():
    content = _load_content()
    tab_cal, tab_news, tab_banner = st.tabs([t("add_event"), t("add_news"), "Banner"])

    with tab_cal:
        st.markdown("#### " + t("calendar_title"))
        for i, ev in enumerate(content.get("calendar", [])):
            with st.expander(f"{ev.get('date','')} — {ev.get('name_en','')}"):
                c1, c2 = st.columns(2)
                ev["date"] = c1.text_input("Date", ev.get("date", ""), key=f"cal_date_{i}")
                ev["category"] = c2.selectbox("Category", ["SEASONAL", "METEOR", "ECLIPSE"], index=["SEASONAL", "METEOR", "ECLIPSE"].index(ev.get("category", "METEOR")), key=f"cal_cat_{i}")
                ev["category_class"] = {"SEASONAL": "type-equinox", "METEOR": "type-meteor", "ECLIPSE": "type-eclipse"}[ev["category"]]
                ev["name_en"] = st.text_input("Name (EN)", ev.get("name_en", ""), key=f"cal_ne_{i}")
                ev["name_th"] = st.text_input("Name (TH)", ev.get("name_th", ""), key=f"cal_nt_{i}")
                ev["detail_en"] = st.text_area("Detail (EN)", ev.get("detail_en", ""), key=f"cal_de_{i}")
                ev["detail_th"] = st.text_area("Detail (TH)", ev.get("detail_th", ""), key=f"cal_dt_{i}")
                if st.button(t("delete"), key=f"cal_del_{i}"):
                    content["calendar"].pop(i)
                    _save_content(content)
                    st.rerun()

        st.markdown("---")
        st.markdown("**" + t("add_event") + "**")
        nc1, nc2 = st.columns(2)
        new_date = nc1.text_input("Date", key="new_cal_date")
        new_cat = nc2.selectbox("Category", ["SEASONAL", "METEOR", "ECLIPSE"], key="new_cal_cat")
        new_ne = st.text_input("Name (EN)", key="new_cal_ne")
        new_nt = st.text_input("Name (TH)", key="new_cal_nt")
        new_de = st.text_area("Detail (EN)", key="new_cal_de")
        new_dt = st.text_area("Detail (TH)", key="new_cal_dt")
        if st.button(t("save"), key="save_new_cal"):
            if new_date and new_ne:
                content["calendar"].append({
                    "date": new_date, "name_en": new_ne, "name_th": new_nt,
                    "category": new_cat,
                    "category_class": {"SEASONAL": "type-equinox", "METEOR": "type-meteor", "ECLIPSE": "type-eclipse"}[new_cat],
                    "detail_en": new_de, "detail_th": new_dt,
                })
                _save_content(content)
                st.success(t("content_saved"))
                st.rerun()

    with tab_news:
        st.markdown("#### " + t("news_feed"))
        for i, n in enumerate(content.get("news", [])):
            with st.expander(f"{n.get('date','')} — {n.get('title_en','')}"):
                n["date"] = st.text_input("Date", n.get("date", ""), key=f"news_d_{i}")
                n["tag_en"] = st.text_input("Tag (EN)", n.get("tag_en", ""), key=f"news_te_{i}")
                n["tag_th"] = st.text_input("Tag (TH)", n.get("tag_th", ""), key=f"news_tt_{i}")
                n["title_en"] = st.text_input("Title (EN)", n.get("title_en", ""), key=f"news_ne_{i}")
                n["title_th"] = st.text_input("Title (TH)", n.get("title_th", ""), key=f"news_nt_{i}")
                n["desc_en"] = st.text_area("Desc (EN)", n.get("desc_en", ""), key=f"news_de_{i}")
                n["desc_th"] = st.text_area("Desc (TH)", n.get("desc_th", ""), key=f"news_dt_{i}")
                if st.button(t("delete"), key=f"news_del_{i}"):
                    content["news"].pop(i)
                    _save_content(content)
                    st.rerun()

        st.markdown("---")
        st.markdown("**" + t("add_news") + "**")
        nn_date = st.text_input("Date", key="new_news_date")
        nn_te = st.text_input("Tag (EN)", key="new_news_te")
        nn_tt = st.text_input("Tag (TH)", key="new_news_tt")
        nn_ne = st.text_input("Title (EN)", key="new_news_ne")
        nn_nt = st.text_input("Title (TH)", key="new_news_nt")
        nn_de = st.text_area("Desc (EN)", key="new_news_de")
        nn_dt = st.text_area("Desc (TH)", key="new_news_dt")
        if st.button(t("save"), key="save_new_news"):
            if nn_date and nn_ne:
                content["news"].insert(0, {
                    "date": nn_date, "tag_en": nn_te, "tag_th": nn_tt,
                    "title_en": nn_ne, "title_th": nn_nt,
                    "desc_en": nn_de, "desc_th": nn_dt,
                })
                _save_content(content)
                st.success(t("content_saved"))
                st.rerun()

    with tab_banner:
        st.markdown("#### Banner Settings")
        banner = content.get("banner", {})
        banner["icon"] = st.text_input("Icon emoji", banner.get("icon", "☄️"), key="ban_icon")
        banner["title_en"] = st.text_input("Title (EN)", banner.get("title_en", ""), key="ban_te")
        banner["title_th"] = st.text_input("Title (TH)", banner.get("title_th", ""), key="ban_tt")
        banner["desc_en"] = st.text_area("Desc (EN)", banner.get("desc_en", ""), key="ban_de")
        banner["desc_th"] = st.text_area("Desc (TH)", banner.get("desc_th", ""), key="ban_dt")
        banner["status_en"] = st.text_input("Status (EN)", banner.get("status_en", "🟢 OPTIMAL"), key="ban_se")
        banner["status_th"] = st.text_input("Status (TH)", banner.get("status_th", "🟢 ดีเยี่ยม"), key="ban_st")
        content["banner"] = banner
        if st.button(t("save"), key="save_banner"):
            _save_content(content)
            st.success(t("content_saved"))
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════
#  Auth Portal Section
# ═══════════════════════════════════════════════════════════════════════

def render_portal():
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 30px;">
        <h2 style="font-family: 'Orbitron', monospace; color: #fff; letter-spacing: 3px; font-size: 2rem;">{t("the_portal")}</h2>
        <p style="color: #8b949e;">{t("portal_subtitle")}</p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander(t("enter_system"), expanded=False):
        login_tab, reg_tab = st.tabs([t("login"), t("register")])

        with login_tab:
            lc, rc = st.columns([1, 1])
            with lc:
                st.markdown(f"#### {t('commander_access')}")
                le = st.text_input(t("email"), key="portal_login_email", placeholder="commander@mission.com")
                lp = st.text_input(t("password"), type="password", key="portal_login_pass")
                if st.button(t("authenticate"), use_container_width=True, type="primary"):
                    if le and lp:
                        ok, name, msg = login_user(le, lp)
                        if ok:
                            st.session_state.logged_in = True
                            st.session_state.username = name
                            st.session_state.user_email = le.lower().strip()
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning(t("enter_credentials"))

            with rc:
                st.markdown(f"#### {t('quick_access')}")

                # ── Google OAuth ──
                g_url = google_auth_url()
                if g_url:
                    if st.button(t("continue_google"), use_container_width=True, key="btn_g_oauth"):
                        st.session_state["_oauth_provider"] = "google"
                        st.markdown(f'<meta http-equiv="refresh" content="0;url={g_url}">', unsafe_allow_html=True)
                else:
                    if st.button(t("continue_google"), use_container_width=True, key="btn_g_fallback"):
                        st.session_state["_social"] = "google"

                # ── Facebook OAuth ──
                fb_url = facebook_auth_url()
                if fb_url:
                    if st.button(t("continue_facebook"), use_container_width=True, key="btn_fb_oauth"):
                        st.session_state["_oauth_provider"] = "facebook"
                        st.markdown(f'<meta http-equiv="refresh" content="0;url={fb_url}">', unsafe_allow_html=True)
                else:
                    if st.button(t("continue_facebook"), use_container_width=True, key="btn_fb_fallback"):
                        st.session_state["_social"] = "facebook"

                # Fallback manual social login (when OAuth creds not configured)
                mode = st.session_state.get("_social", "")
                if mode in ("google", "facebook"):
                    st.info(f"OAuth credentials not configured. Manual {mode.title()} login:")
                    se = st.text_input(f"{mode.title()} Email", key=f"_se_{mode}")
                    if st.button("Confirm", key=f"_sc_{mode}"):
                        if se:
                            ok, name = social_login(se, se.split("@")[0], mode)
                            st.session_state.logged_in = True
                            st.session_state.username = name
                            st.session_state.user_email = se.lower().strip()
                            st.session_state["_social"] = ""
                            st.rerun()

        with reg_tab:
            r1, r2 = st.columns(2)
            rn = r1.text_input(t("display_name"), key="portal_reg_name")
            re_email = r2.text_input(t("email"), key="portal_reg_email")
            rp = r1.text_input(t("password"), type="password", key="portal_reg_pass")
            rp2 = r2.text_input(t("confirm_password"), type="password", key="portal_reg_pass2")
            rm = st.radio(t("signup_via"), ["Email", "Google", "Facebook"], horizontal=True)
            if st.button(t("create_account"), use_container_width=True, type="primary"):
                if not rn or not re_email:
                    st.warning(t("fill_all_fields"))
                elif rp != rp2:
                    st.error(t("password_mismatch"))
                else:
                    ok, msg = register_user(re_email, rp, rn, rm.lower())
                    if ok:
                        st.success(t("register_success"))
                    else:
                        st.error(msg)


# ═══════════════════════════════════════════════════════════════════════
#  MAIN PUBLIC PAGE
# ═══════════════════════════════════════════════════════════════════════

def show_public_page():
    """The Gateway: Immersive Pre-Dashboard with i18n + editable content + real OAuth."""

    # Handle OAuth callbacks first
    _handle_oauth_callback()

    # ── CSS (inside <style> tags — no leak) ──
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600&display=swap');
    .stApp {
        background-color: #0d1117;
        background-image: radial-gradient(circle at 10% 20%, rgba(20,35,60,0.4) 0%, transparent 40%),
                          radial-gradient(circle at 90% 80%, rgba(40,20,60,0.3) 0%, transparent 40%);
        color: #c9d1d9; font-family: 'Inter', sans-serif;
    }
    header[data-testid="stHeader"] { display: none !important; }
    .block-container { padding-top: 2rem !important; max-width: 1200px !important; }
    div[data-testid="stExpander"] {
        background: rgba(14,17,23,0.8); border: 1px solid rgba(88,166,255,0.3);
        border-radius: 12px; backdrop-filter: blur(10px);
    }
    div[data-testid="stExpander"] > summary p {
        font-family: 'Orbitron', monospace; font-weight: 700;
        font-size: 1.2rem; color: #58a6ff; letter-spacing: 2px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Language Selector (top of page)
    lang_selector(location="main")

    # Load editable content
    content = _load_content()

    # Header
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 40px; margin-top: 10px;">
        <span style="font-size: 3rem;">🛰️</span>
        <h1 style="font-family: 'Orbitron', monospace; font-weight: 900; font-size: 3.5rem; margin: 0;
                   letter-spacing: 4px; color: #fff; text-shadow: 0 0 20px rgba(88,166,255,0.4);">{t("the_gateway")}</h1>
        <p style="font-size: 1.2rem; color: #8b949e; letter-spacing: 1px; font-weight: 300;">{t("gateway_subtitle")}</p>
    </div>
    """, unsafe_allow_html=True)

    # Banner
    render_banner(content)

    # Calendar + News
    col_left, col_right = st.columns([1.5, 1])
    with col_left:
        render_calendar(content)
    with col_right:
        render_news_feed(content)

    # Knowledge Hub
    render_knowledge_hub()

    st.markdown("<br><br><hr style='border-color: rgba(255,255,255,0.1);'><br>", unsafe_allow_html=True)

    # The Portal (Auth)
    render_portal()

    # Admin edit button (only visible if user is somehow logged in, or use a secret key combo)
    # For convenience, an admin button at the bottom
    st.markdown("<br><br>", unsafe_allow_html=True)
    admin_email = st.session_state.get("user_email", "")
    if admin_email and is_admin(admin_email):
        if st.button(t("admin_panel"), use_container_width=True):
            admin_content_editor()
