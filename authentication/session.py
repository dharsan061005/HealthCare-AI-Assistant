"""
Session Management — Healthcare AI Assistant
All authentication state lives in st.session_state under a single 'auth' dict.
This module provides clean helpers so the rest of the app never touches
session keys directly.
"""

import streamlit as st
from typing import Dict, Optional


# ─── Session key constants ────────────────────────────────────────────────────

_AUTH_KEY        = "auth"          # dict holding full auth state
_USER_KEY        = "user"          # logged-in user dict
_LOGGED_IN_KEY   = "logged_in"     # bool
_IS_GUEST_KEY    = "is_guest"      # bool
_AUTH_PAGE_KEY   = "auth_page"     # 'login' | 'register' | 'forgot'
_REMEMBER_KEY    = "remember_me"   # bool


def _auth() -> Dict:
    """Return (creating if needed) the top-level auth state dict."""
    if _AUTH_KEY not in st.session_state:
        st.session_state[_AUTH_KEY] = {
            _LOGGED_IN_KEY: False,
            _IS_GUEST_KEY:  False,
            _USER_KEY:      None,
            _AUTH_PAGE_KEY: "login",
            _REMEMBER_KEY:  False,
        }
    return st.session_state[_AUTH_KEY]


# ─── Read helpers ─────────────────────────────────────────────────────────────

def is_logged_in() -> bool:
    """Return True if a user (or guest) is currently authenticated."""
    a = _auth()
    return bool(a.get(_LOGGED_IN_KEY, False))


def is_guest() -> bool:
    """Return True if the session is a guest (no account) session."""
    return bool(_auth().get(_IS_GUEST_KEY, False))


def get_current_user() -> Optional[Dict]:
    """Return the logged-in user dict, or None for guests / not logged in."""
    return _auth().get(_USER_KEY)


def get_auth_page() -> str:
    """Return the currently active auth sub-page: 'login'|'register'|'forgot'."""
    return _auth().get(_AUTH_PAGE_KEY, "login")


# ─── Write helpers ────────────────────────────────────────────────────────────

def set_auth_page(page: str) -> None:
    """Switch the displayed auth sub-page."""
    _auth()[_AUTH_PAGE_KEY] = page
    st.rerun()


def login_user(user: Dict, remember: bool = False) -> None:
    """Persist a successful login into session state."""
    a = _auth()
    a[_LOGGED_IN_KEY] = True
    a[_IS_GUEST_KEY]  = False
    a[_USER_KEY]      = dict(user)
    a[_REMEMBER_KEY]  = remember
    # Clear any OTP state left over from forgot-password flow
    for key in ["otp_email", "otp_sent", "otp_verified"]:
        st.session_state.pop(key, None)


def login_as_guest() -> None:
    """Create a lightweight guest session (no user dict)."""
    a = _auth()
    a[_LOGGED_IN_KEY] = True
    a[_IS_GUEST_KEY]  = True
    a[_USER_KEY]      = {
        "id":         None,
        "full_name":  "Guest",
        "email":      "",
        "phone":      "",
        "age":        None,
        "gender":     "",
        "blood_group": "",
    }


def logout() -> None:
    """Clear all authentication state and return to login page."""
    # Wipe the entire auth dict and any leftover OTP keys
    keys_to_clear = [_AUTH_KEY, "otp_email", "otp_sent", "otp_verified",
                     "db_initialized", "selected_page"]
    for k in keys_to_clear:
        st.session_state.pop(k, None)
    st.rerun()


def refresh_user(user: Dict) -> None:
    """Replace the in-session user dict (e.g., after a profile update)."""
    _auth()[_USER_KEY] = dict(user)


def get_display_name() -> str:
    """Return the first name of the logged-in user, or 'Guest'."""
    user = get_current_user()
    if not user:
        return "Guest"
    full = user.get("full_name", "Guest") or "Guest"
    return full.split()[0]


def get_avatar_initials() -> str:
    """Return up to 2 initials for the avatar placeholder."""
    user = get_current_user()
    if not user:
        return "G"
    parts = (user.get("full_name", "") or "").split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    if parts:
        return parts[0][:2].upper()
    return "G"
