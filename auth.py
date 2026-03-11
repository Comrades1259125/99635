"""
auth.py - User Authentication & Registration System
Supports: Email/Password, Google OAuth, Facebook OAuth.
"""

import json
import os
import hashlib
from datetime import datetime, timezone
import streamlit as st
import urllib.request
import urllib.parse

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")


def _load_users() -> dict:
    """Load users from JSON file."""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_users(users: dict):
    """Save users to JSON file."""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def _hash_password(password: str) -> str:
    """Hash password with SHA-256 + salt."""
    salt = "SAT_TELEMETRY_SALT_"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def is_admin(email: str) -> bool:
    """Check if the given email is an admin."""
    try:
        admin_emails = st.secrets.get("admin", {}).get("emails", "")
        return email.lower().strip() in [e.strip().lower() for e in admin_emails.split(",")]
    except Exception:
        return False


def register_user(email: str, password: str, display_name: str, method: str = "email") -> tuple:
    """Register a new user.  Returns (success, message)."""
    users = _load_users()
    email_lower = email.lower().strip()

    if email_lower in users:
        return False, "Email already registered"

    if len(password) < 4:
        return False, "Password must be at least 4 characters"

    users[email_lower] = {
        "display_name": display_name,
        "password_hash": _hash_password(password),
        "method": method,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_login": None,
    }
    _save_users(users)
    return True, "Registration successful!"


def login_user(email: str, password: str) -> tuple:
    """Login with email/password.  Returns (success, display_name, message)."""
    users = _load_users()
    email_lower = email.lower().strip()

    if email_lower not in users:
        return False, "", "Email not found. Please register first."

    user = users[email_lower]
    if user["password_hash"] != _hash_password(password):
        return False, "", "Incorrect password."

    user["last_login"] = datetime.now(timezone.utc).isoformat()
    _save_users(users)
    return True, user["display_name"], "Login successful!"


def social_login(email: str, display_name: str, method: str) -> tuple:
    """Social login — auto-register if new.  Returns (success, display_name)."""
    users = _load_users()
    email_lower = email.lower().strip()

    if email_lower not in users:
        users[email_lower] = {
            "display_name": display_name,
            "password_hash": "",
            "method": method,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_login": datetime.now(timezone.utc).isoformat(),
        }
    else:
        users[email_lower]["last_login"] = datetime.now(timezone.utc).isoformat()

    _save_users(users)
    return True, users[email_lower]["display_name"]


# ═══════════════════════════════════════════════════════════════════════
#  GOOGLE OAUTH 2.0  (Authorization Code flow)
# ═══════════════════════════════════════════════════════════════════════

def _google_credentials():
    """Return (client_id, client_secret, redirect_uri) or None."""
    try:
        g = st.secrets.get("google_oauth", {})
        cid = g.get("client_id", "")
        csec = g.get("client_secret", "")
        ruri = g.get("redirect_uri", "http://localhost:8501")
        if cid and csec:
            return cid, csec, ruri
    except Exception:
        pass
    return None


def google_auth_url() -> str | None:
    """Build the Google OAuth authorization URL."""
    creds = _google_credentials()
    if creds is None:
        return None
    client_id, _, redirect_uri = creds
    params = urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    })
    return f"https://accounts.google.com/o/oauth2/v2/auth?{params}"


def google_handle_callback(code: str) -> dict | None:
    """Exchange authorization code for user info. Returns dict(email, name) or None."""
    creds = _google_credentials()
    if creds is None:
        return None
    client_id, client_secret, redirect_uri = creds
    try:
        # Exchange code for tokens
        token_data = urllib.parse.urlencode({
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }).encode()
        req = urllib.request.Request(
            "https://oauth2.googleapis.com/token",
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            tokens = json.loads(resp.read())

        access_token = tokens.get("access_token")
        if not access_token:
            return None

        # Fetch user info
        info_req = urllib.request.Request(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        with urllib.request.urlopen(info_req, timeout=10) as resp:
            user_info = json.loads(resp.read())

        return {
            "email": user_info.get("email", ""),
            "name": user_info.get("name", user_info.get("email", "").split("@")[0]),
        }
    except Exception as e:
        st.error(f"Google OAuth error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════
#  FACEBOOK OAUTH 2.0  (Authorization Code flow)
# ═══════════════════════════════════════════════════════════════════════

def _facebook_credentials():
    """Return (app_id, app_secret, redirect_uri) or None."""
    try:
        fb = st.secrets.get("facebook_oauth", {})
        aid = fb.get("app_id", "")
        asec = fb.get("app_secret", "")
        ruri = fb.get("redirect_uri", "http://localhost:8501")
        if aid and asec:
            return aid, asec, ruri
    except Exception:
        pass
    return None


def facebook_auth_url() -> str | None:
    """Build the Facebook OAuth authorization URL."""
    creds = _facebook_credentials()
    if creds is None:
        return None
    app_id, _, redirect_uri = creds
    params = urllib.parse.urlencode({
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "scope": "email,public_profile",
        "response_type": "code",
    })
    return f"https://www.facebook.com/v18.0/dialog/oauth?{params}"


def facebook_handle_callback(code: str) -> dict | None:
    """Exchange authorization code for user info. Returns dict(email, name) or None."""
    creds = _facebook_credentials()
    if creds is None:
        return None
    app_id, app_secret, redirect_uri = creds
    try:
        # Exchange code for access token
        params = urllib.parse.urlencode({
            "client_id": app_id,
            "client_secret": app_secret,
            "redirect_uri": redirect_uri,
            "code": code,
        })
        url = f"https://graph.facebook.com/v18.0/oauth/access_token?{params}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            tokens = json.loads(resp.read())

        access_token = tokens.get("access_token")
        if not access_token:
            return None

        # Fetch user info
        info_url = f"https://graph.facebook.com/me?fields=id,name,email&access_token={access_token}"
        with urllib.request.urlopen(info_url, timeout=10) as resp:
            user_info = json.loads(resp.read())

        return {
            "email": user_info.get("email", f"{user_info['id']}@facebook.com"),
            "name": user_info.get("name", "Facebook User"),
        }
    except Exception as e:
        st.error(f"Facebook OAuth error: {e}")
        return None
