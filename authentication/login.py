"""
Login Page — Healthcare AI Assistant
No st.form used — avoids white-card override from styles.css.
State-based submission via session_state + st.button.
"""

import streamlit as st
from components.auth_ui import (
    inject_auth_css, auth_card_open, auth_card_close,
    auth_error, auth_success, divider_or,
)
from authentication.auth import attempt_login
from authentication.session import login_user, login_as_guest, set_auth_page


def render() -> None:
    """Render the full login page."""
    inject_auth_css()
    auth_card_open()

    # ── show/hide toggle ──────────────────────────────────────────────────
    if "show_pw" not in st.session_state:
        st.session_state.show_pw = False

    # ── Feedback ──────────────────────────────────────────────────────────
    if st.session_state.get("_login_error"):
        auth_error(st.session_state.pop("_login_error"))
    if st.session_state.get("_login_success"):
        auth_success(st.session_state.pop("_login_success"))
    if st.session_state.get("_register_ok"):
        auth_success(st.session_state.pop("_register_ok"))
    if st.session_state.get("_reset_ok"):
        auth_success(st.session_state.pop("_reset_ok"))

    # ── Email field ───────────────────────────────────────────────────────
    st.markdown(
        '<p class="field-label">EMAIL ADDRESS</p>',
        unsafe_allow_html=True,
    )
    email = st.text_input(
        "Email",
        placeholder="you@example.com",
        label_visibility="collapsed",
        key="login_email",
    )

    # ── Password field ────────────────────────────────────────────────────
    st.markdown(
        '<p class="field-label" style="margin-top:0.5rem;">PASSWORD</p>',
        unsafe_allow_html=True,
    )
    pw_type = "default" if st.session_state.show_pw else "password"
    password = st.text_input(
        "Password",
        type=pw_type,
        placeholder="Enter your password",
        label_visibility="collapsed",
        key="login_password",
    )

    # ── Remember Me + Show/Hide row ───────────────────────────────────────
    col_rem, col_show = st.columns([3, 2])
    with col_rem:
        remember = st.checkbox("Remember Me", key="remember_me_chk")
    with col_show:
        toggle_lbl = "🙈 Hide" if st.session_state.show_pw else "👁️ Show"
        if st.button(toggle_lbl, key="btn_toggle_pw"):
            st.session_state.show_pw = not st.session_state.show_pw
            st.rerun()

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── Login button ──────────────────────────────────────────────────────
    if st.button("🔐  Login", key="btn_login", use_container_width=True, type="primary"):
        if not email or not password:
            st.session_state["_login_error"] = "Please enter your email and password."
            st.rerun()
        else:
            with st.spinner("Verifying credentials…"):
                ok, msg, user = attempt_login(email.strip(), password)
            if ok:
                login_user(user, remember=st.session_state.get("remember_me_chk", False))
                st.session_state["_login_success"] = f"Welcome back, {user['full_name'].split()[0]}!"
                st.rerun()
            else:
                st.session_state["_login_error"] = msg
                st.rerun()

    # ── Forgot Password ───────────────────────────────────────────────────
    st.markdown('<div class="auth-link-btn" style="text-align:right;margin-top:0.4rem;">', unsafe_allow_html=True)
    if st.button("Forgot Password?", key="btn_forgot"):
        set_auth_page("forgot")
    st.markdown("</div>", unsafe_allow_html=True)

    # ── OR + Guest ────────────────────────────────────────────────────────
    divider_or()

    if st.button("👤  Continue as Guest", key="btn_guest", use_container_width=True):
        login_as_guest()
        st.rerun()

    # ── Create Account link ───────────────────────────────────────────────
    st.markdown(
        '<div class="auth-bottom-text">Don\'t have an account?</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="auth-link-btn" style="text-align:center;">', unsafe_allow_html=True)
    if st.button("✨  Create Account", key="btn_to_register"):
        set_auth_page("register")
    st.markdown("</div>", unsafe_allow_html=True)

    auth_card_close()
