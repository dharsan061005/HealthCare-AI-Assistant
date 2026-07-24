"""
Registration Page — Healthcare AI Assistant
No st.form — avoids white-card background override from styles.css.
"""

import streamlit as st
from components.auth_ui import (
    inject_auth_css, auth_card_open, auth_card_close,
    auth_error, auth_success, render_strength_bar,
)
from authentication.auth import attempt_register
from authentication.session import set_auth_page

_BLOOD_GROUPS = ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"]
_GENDERS      = ["", "Male", "Female", "Non-binary", "Prefer not to say"]


def render() -> None:
    """Render the registration page."""
    inject_auth_css()

    st.markdown(
        "<style>.auth-card { max-width: 520px !important; }</style>",
        unsafe_allow_html=True,
    )

    auth_card_open()

    st.markdown(
        '<p style="text-align:center;color:#94A3B8;font-size:0.83rem;margin:-0.75rem 0 1rem;">Create your patient account</p>',
        unsafe_allow_html=True,
    )

    # ── Feedback ──────────────────────────────────────────────────────────
    if st.session_state.get("_reg_error"):
        auth_error(st.session_state.pop("_reg_error"))

    # ── show/hide toggle ──────────────────────────────────────────────────
    if "show_reg_pw" not in st.session_state:
        st.session_state.show_reg_pw = False

    # ── Full Name ─────────────────────────────────────────────────────────
    st.markdown('<p class="field-label">FULL NAME *</p>', unsafe_allow_html=True)
    full_name = st.text_input("Full Name", placeholder="e.g. Dharsan Kumar",
                               label_visibility="collapsed", key="reg_fullname")

    # ── Email ─────────────────────────────────────────────────────────────
    st.markdown('<p class="field-label" style="margin-top:0.4rem;">EMAIL ADDRESS *</p>', unsafe_allow_html=True)
    email = st.text_input("Email", placeholder="you@example.com",
                           label_visibility="collapsed", key="reg_email")

    # ── Phone + Age ───────────────────────────────────────────────────────
    col_phone, col_age = st.columns([3, 2])
    with col_phone:
        st.markdown('<p class="field-label" style="margin-top:0.4rem;">PHONE NUMBER</p>', unsafe_allow_html=True)
        phone = st.text_input("Phone", placeholder="+91 9876543210",
                               label_visibility="collapsed", key="reg_phone")
    with col_age:
        st.markdown('<p class="field-label" style="margin-top:0.4rem;">AGE</p>', unsafe_allow_html=True)
        age_val = st.number_input("Age", min_value=1, max_value=120, value=None,
                                   placeholder="25", label_visibility="collapsed",
                                   key="reg_age", step=1)

    # ── Gender + Blood Group ──────────────────────────────────────────────
    col_gen, col_bg = st.columns(2)
    with col_gen:
        st.markdown('<p class="field-label" style="margin-top:0.4rem;">GENDER</p>', unsafe_allow_html=True)
        gender = st.selectbox("Gender", options=_GENDERS,
                               label_visibility="collapsed", key="reg_gender")
    with col_bg:
        st.markdown('<p class="field-label" style="margin-top:0.4rem;">BLOOD GROUP</p>', unsafe_allow_html=True)
        blood_group = st.selectbox("Blood Group", options=_BLOOD_GROUPS,
                                    label_visibility="collapsed", key="reg_blood")

    # ── Password ──────────────────────────────────────────────────────────
    pw_type = "default" if st.session_state.show_reg_pw else "password"
    st.markdown('<p class="field-label" style="margin-top:0.4rem;">PASSWORD *</p>', unsafe_allow_html=True)
    password = st.text_input("Password", type=pw_type,
                              placeholder="Min 8 chars, upper, lower, number, symbol",
                              label_visibility="collapsed", key="reg_password")

    # ── Confirm Password ──────────────────────────────────────────────────
    st.markdown('<p class="field-label" style="margin-top:0.4rem;">CONFIRM PASSWORD *</p>', unsafe_allow_html=True)
    confirm_pw = st.text_input("Confirm Password", type=pw_type,
                                placeholder="Re-enter your password",
                                label_visibility="collapsed", key="reg_confirm")

    # Strength bar (live, outside any form)
    render_strength_bar(st.session_state.get("reg_password", ""))

    # ── Show/Hide + T&C row ───────────────────────────────────────────────
    col_toggle, col_tc = st.columns([2, 3])
    with col_toggle:
        toggle_lbl = "🙈 Hide" if st.session_state.show_reg_pw else "👁️ Show"
        if st.button(toggle_lbl, key="btn_reg_toggle"):
            st.session_state.show_reg_pw = not st.session_state.show_reg_pw
            st.rerun()
    with col_tc:
        terms = st.checkbox("I agree to the Terms & Conditions", key="reg_terms")

    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

    # ── Create Account button ─────────────────────────────────────────────
    if st.button("🚀  Create Account", key="btn_register",
                  use_container_width=True, type="primary"):
        if not terms:
            st.session_state["_reg_error"] = "Please accept the Terms & Conditions to continue."
            st.rerun()
        else:
            with st.spinner("Creating your account…"):
                ok, msg = attempt_register(
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    age=int(age_val) if age_val else None,
                    gender=gender,
                    blood_group=blood_group,
                    password=password,
                    confirm_password=confirm_pw,
                )
            if ok:
                st.session_state["_register_ok"] = msg
                set_auth_page("login")
            else:
                st.session_state["_reg_error"] = msg
                st.rerun()

    # ── Already have account ──────────────────────────────────────────────
    st.markdown('<div class="auth-bottom-text">Already have an account?</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-link-btn" style="text-align:center;">', unsafe_allow_html=True)
    if st.button("🔐  Login", key="btn_to_login"):
        set_auth_page("login")
    st.markdown("</div>", unsafe_allow_html=True)

    auth_card_close()
