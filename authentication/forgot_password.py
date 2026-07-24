"""
Forgot Password Page — Healthcare AI Assistant
Three-step flow (no st.form — avoids white-card override):
  Step 1 — Enter email → sends OTP
  Step 2 — Verify OTP
  Step 3 — Set new password
"""

import streamlit as st
from components.auth_ui import (
    inject_auth_css, auth_card_open, auth_card_close,
    auth_error, auth_success, auth_info,
    render_strength_bar, render_step_indicator,
)
from authentication.auth import send_otp, reset_password_with_otp
from authentication.session import set_auth_page


def render() -> None:
    inject_auth_css()
    auth_card_open()

    st.markdown(
        '<p style="text-align:center;color:#94A3B8;font-size:0.83rem;margin:-0.75rem 0 1rem;">Reset your password</p>',
        unsafe_allow_html=True,
    )

    # ── State init ────────────────────────────────────────────────────────
    if "otp_step"      not in st.session_state: st.session_state.otp_step      = 1
    if "otp_email"     not in st.session_state: st.session_state.otp_email     = ""
    if "otp_demo_code" not in st.session_state: st.session_state.otp_demo_code = ""

    step = st.session_state.otp_step
    render_step_indicator(step, total=3)

    # ── Feedback ──────────────────────────────────────────────────────────
    if st.session_state.get("_fp_error"):   auth_error(st.session_state.pop("_fp_error"))
    if st.session_state.get("_fp_success"): auth_success(st.session_state.pop("_fp_success"))
    if st.session_state.get("_fp_info"):    auth_info(st.session_state.pop("_fp_info"))

    # ── STEP 1: Email ─────────────────────────────────────────────────────
    if step == 1:
        st.markdown(
            '<p style="color:#CBD5E1;font-size:0.85rem;text-align:center;margin-bottom:1rem;">'
            "Enter your registered email and we'll send you a verification code.</p>",
            unsafe_allow_html=True,
        )
        st.markdown('<p class="field-label">EMAIL ADDRESS</p>', unsafe_allow_html=True)
        email_input = st.text_input("Email", placeholder="you@example.com",
                                     label_visibility="collapsed", key="fp_email_input")

        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
        if st.button("📨  Send OTP", key="btn_send_otp", use_container_width=True, type="primary"):
            if not email_input.strip():
                st.session_state["_fp_error"] = "Please enter your email address."
                st.rerun()
            else:
                with st.spinner("Sending OTP…"):
                    ok, otp_code = send_otp(email_input.strip())
                if ok:
                    st.session_state.otp_email      = email_input.strip().lower()
                    st.session_state.otp_demo_code  = otp_code
                    st.session_state.otp_step       = 2
                    st.session_state["_fp_info"] = f"OTP sent! (Demo mode — code: {otp_code})"
                    st.rerun()
                else:
                    st.session_state["_fp_error"] = "No account found with that email."
                    st.rerun()

    # ── STEP 2: Verify OTP ────────────────────────────────────────────────
    elif step == 2:
        email = st.session_state.otp_email
        st.markdown(
            f'<p class="otp-hint">OTP sent to <strong style="color:#38BDF8">{email}</strong></p>',
            unsafe_allow_html=True,
        )
        if st.session_state.otp_demo_code:
            auth_info(f"Demo OTP: {st.session_state.otp_demo_code}  (valid 10 min)")

        st.markdown('<p class="field-label">ENTER 6-DIGIT OTP</p>', unsafe_allow_html=True)
        otp_input = st.text_input("OTP", placeholder="_ _ _ _ _ _", max_chars=6,
                                   label_visibility="collapsed", key="fp_otp_input")

        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
        if st.button("✅  Verify OTP", key="btn_verify_otp", use_container_width=True, type="primary"):
            if len(otp_input.strip()) != 6 or not otp_input.strip().isdigit():
                st.session_state["_fp_error"] = "Please enter the 6-digit OTP."
                st.rerun()
            else:
                from authentication.auth_db import verify_otp
                if verify_otp(email, otp_input.strip()):
                    st.session_state.otp_verified_code = otp_input.strip()
                    st.session_state.otp_step = 3
                    st.session_state["_fp_success"] = "OTP verified! Set your new password."
                    st.rerun()
                else:
                    st.session_state["_fp_error"] = "Invalid or expired OTP. Please try again."
                    st.rerun()

        st.markdown('<div class="auth-link-btn" style="text-align:center;margin-top:0.5rem;">', unsafe_allow_html=True)
        if st.button("🔄 Resend OTP", key="btn_resend_otp"):
            with st.spinner("Resending…"):
                ok, otp_code = send_otp(email)
            if ok:
                st.session_state.otp_demo_code = otp_code
                st.session_state["_fp_info"] = f"New OTP sent! (Demo: {otp_code})"
            else:
                st.session_state["_fp_error"] = "Failed to resend OTP."
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ── STEP 3: New Password ──────────────────────────────────────────────
    elif step == 3:
        st.markdown(
            '<p style="color:#CBD5E1;font-size:0.85rem;text-align:center;margin-bottom:1rem;">'
            "Create a strong new password for your account.</p>",
            unsafe_allow_html=True,
        )

        if "show_fp_pw" not in st.session_state:
            st.session_state.show_fp_pw = False
        pw_type = "default" if st.session_state.show_fp_pw else "password"

        st.markdown('<p class="field-label">NEW PASSWORD</p>', unsafe_allow_html=True)
        new_pw = st.text_input("New Password", type=pw_type,
                                placeholder="Min 8 chars, upper, lower, number, symbol",
                                label_visibility="collapsed", key="fp_new_pw")

        st.markdown('<p class="field-label" style="margin-top:0.4rem;">CONFIRM NEW PASSWORD</p>', unsafe_allow_html=True)
        confirm_pw = st.text_input("Confirm Password", type=pw_type,
                                    placeholder="Re-enter new password",
                                    label_visibility="collapsed", key="fp_confirm_pw")

        render_strength_bar(st.session_state.get("fp_new_pw", ""))

        col_toggle, _ = st.columns([2, 3])
        with col_toggle:
            lbl = "🙈 Hide" if st.session_state.show_fp_pw else "👁️ Show"
            if st.button(lbl, key="btn_fp_toggle"):
                st.session_state.show_fp_pw = not st.session_state.show_fp_pw
                st.rerun()

        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
        if st.button("🔒  Reset Password", key="btn_reset_pw",
                      use_container_width=True, type="primary"):
            email = st.session_state.otp_email
            otp   = st.session_state.get("otp_verified_code", "")
            # Re-store for 1-min consumption by reset_password_with_otp
            from authentication.auth_db import store_otp
            store_otp(email, otp, ttl_minutes=1)
            with st.spinner("Resetting password…"):
                ok, msg = reset_password_with_otp(email, otp, new_pw, confirm_pw)
            if ok:
                for k in ["otp_step", "otp_email", "otp_demo_code", "otp_verified_code"]:
                    st.session_state.pop(k, None)
                st.session_state["_reset_ok"] = msg
                set_auth_page("login")
            else:
                st.session_state["_fp_error"] = msg
                st.rerun()

    # ── Back to Login ─────────────────────────────────────────────────────
    st.markdown('<div class="auth-link-btn" style="text-align:center;margin-top:0.75rem;">', unsafe_allow_html=True)
    if st.button("← Back to Login", key="btn_back_login"):
        for k in ["otp_step", "otp_email", "otp_demo_code", "otp_verified_code"]:
            st.session_state.pop(k, None)
        set_auth_page("login")
    st.markdown("</div>", unsafe_allow_html=True)

    auth_card_close()
