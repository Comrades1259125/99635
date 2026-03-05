"""
auth.py - User Authentication & Registration System
Simple JSON-file-based user storage for the Satellite Telemetry System.
"""

import json
import os
import hashlib
import secrets
from datetime import datetime, timezone

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


def register_user(email: str, password: str, display_name: str, method: str = "email") -> tuple:
    """
    Register a new user.
    Returns (success: bool, message: str)
    """
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
    """
    Login with email and password.
    Returns (success: bool, display_name: str, message: str)
    """
    users = _load_users()
    email_lower = email.lower().strip()

    if email_lower not in users:
        return False, "", "Email not found. Please register first."

    user = users[email_lower]
    if user["password_hash"] != _hash_password(password):
        return False, "", "Incorrect password."

    # Update last login
    user["last_login"] = datetime.now(timezone.utc).isoformat()
    _save_users(users)

    return True, user["display_name"], "Login successful!"


def social_login(email: str, display_name: str, method: str) -> tuple:
    """
    Social login (Google/Facebook) - auto-register if new.
    Returns (success: bool, display_name: str)
    """
    users = _load_users()
    email_lower = email.lower().strip()

    if email_lower not in users:
        # Auto-register for social login
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
