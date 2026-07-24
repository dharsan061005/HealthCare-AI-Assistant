"""
Appointment Scheduling Agent — redesigned UI
"""

import logging
from datetime import date, timedelta
from typing import Dict, List

import pandas as pd
import streamlit as st

from database import database as db
from utils.helpers import (
    appointments_to_display_rows,
    date_to_str,
    format_date,
    format_time_12h,
    get_status_emoji,
)
from utils.validators import (
    validate_appointment_date,
    validate_appointment_time,
    validate_patient_name,
)
from utils.constants import SPECIALIZATIONS, TIME_SLOTS
from utils.i18n import t, get_lang

logger = logging.getLogger(__name__)


def _status_badge(status: str) -> str:
    classes = {
        "scheduled":   "badge-scheduled",
        "completed":   "badge-completed",
        "cancelled":   "badge-cancelled",
        "rescheduled": "badge-rescheduled",
    }
    cls = classes.get(status.lower(), "badge-scheduled")
    return f"<span class='badge {cls}'>{status}</span>"


# ── Book ──────────────────────────────────────────────────────────────────────
def _render_book_tab() -> None:
    lang = get_lang(st.session_state)
    st.markdown(f"""
    <div style="background:#F0F9FF; border:1px solid #BAE6FD; border-radius:12px;
                padding:1rem 1.25rem; margin-bottom:1.25rem; font-size:0.85rem; color:#0C4A6E;">
        📋 {t("tab_book", lang).replace("📋 ","")} — fields marked <b>*</b> are required.
    </div>
    """, unsafe_allow_html=True)

    # 1. Hospital Selection
    st.markdown("### 1. Select Hospital")
    hospital_options = [
        "Apollo Hospital",
        "Fortis Hospital",
        "MIOT International",
        "SIMS Hospital",
        "Sri Ramachandra Medical Centre",
        "Kauvery Hospital",
        "MGM Healthcare",
        "Gleneagles Global Hospital",
        "Other"
    ]
    selected_hosp_option = st.selectbox(
        "Select Hospital *",
        options=hospital_options,
        index=0,
        key="book_hosp_select"
    )
    
    hospital_name = ""
    if selected_hosp_option == "Other":
        hospital_name = st.text_input("Enter Hospital Name *", placeholder="e.g. City General Hospital", key="book_hosp_other").strip()
    else:
        hospital_name = selected_hosp_option

    st.markdown("### 2. Appointment Details")
    with st.form("book_appointment_form", clear_on_submit=True):
        st.markdown("#### Patient Details")
        c1, c2 = st.columns(2)
        with c1:
            patient_name     = st.text_input(t("patient_name", lang), placeholder=t("patient_name_placeholder", lang))
            age              = st.number_input("Age *", min_value=0, max_value=120, value=30, step=1)
            gender           = st.selectbox("Gender *", ["Male", "Female", "Other", "Prefer not to say"])
        with c2:
            mobile_number    = st.text_input("Mobile Number *", placeholder="e.g. +91 98765 43210")
            email            = st.text_input("Email (Optional)", placeholder="e.g. name@example.com")
            reason_for_visit = st.text_input("Reason for Visit *", placeholder="e.g. Annual checkup, consultation")

        st.markdown("#### Provider Preferences")
        c3, c4 = st.columns(2)
        with c3:
            specialization   = st.selectbox(t("specialization", lang), SPECIALIZATIONS)
            appointment_date = st.date_input(
                t("appointment_date", lang),
                value=date.today() + timedelta(days=1),
                min_value=date.today(),
                max_value=date.today() + timedelta(days=365),
            )
        with c4:
            all_doctors  = db.get_all_doctors()
            spec_doctors = [d["doctor_name"] for d in all_doctors if d["specialization"].lower() == specialization.lower()]
            doctor_name      = st.selectbox(t("select_doctor", lang), spec_doctors if spec_doctors else ["No doctors available"])
            appointment_time = st.selectbox(t("appointment_time", lang), TIME_SLOTS)
            
        notes = st.text_area(t("notes", lang), placeholder=t("notes_placeholder", lang))

        submitted = st.form_submit_button(t("book_appointment_btn", lang), type="primary", use_container_width=True)

    if submitted:
        errors = []
        if not hospital_name:
            errors.append("Hospital name cannot be empty.")
        
        ok, msg = validate_patient_name(patient_name)
        if not ok:
            errors.append(msg)
            
        from utils.validators import validate_phone_number, validate_email_address
        ok, msg = validate_phone_number(mobile_number)
        if not ok:
            errors.append(msg)
            
        if email.strip():
            ok, msg = validate_email_address(email)
            if not ok:
                errors.append(msg)
                
        if not reason_for_visit.strip():
            errors.append("Reason for visit is required.")

        ok, msg = validate_appointment_date(appointment_date)
        if not ok:
            errors.append(msg)
            
        ok, msg = validate_appointment_time(appointment_time)
        if not ok:
            errors.append(msg)

        if not spec_doctors or doctor_name == "No doctors available":
            errors.append("Please select a valid doctor.")

        if errors:
            for err in errors:
                st.error(err)
            return

        date_str = date_to_str(appointment_date)
        if db.check_duplicate_appointment(hospital_name, doctor_name, date_str, appointment_time):
            st.error(
                f"⚠️ **Slot Taken:** {doctor_name} already has an appointment at **{hospital_name}** on "
                f"{format_date(date_str)} at {format_time_12h(appointment_time)}. Choose a different slot."
            )
            return

        try:
            apt_id = db.create_appointment(
                hospital_name=hospital_name.strip(),
                patient_name=patient_name.strip(),
                age=int(age),
                gender=gender,
                mobile_number=mobile_number.strip(),
                email=email.strip(),
                reason_for_visit=reason_for_visit.strip(),
                doctor_name=doctor_name,
                specialization=specialization,
                appointment_date=date_str,
                appointment_time=appointment_time,
                notes=notes.strip(),
            )
            st.markdown(f"""
            <div style="background:#F0FDF4; border-left:4px solid #10B981; border-radius:10px;
                        padding:1rem 1.25rem; font-size:0.88rem; color:#065F46;">
                <div style="font-weight:700; font-size:1rem; margin-bottom:0.5rem;">✅ Appointment Booked! (ID: #{apt_id})</div>
                <div><b>Hospital:</b> {hospital_name}</div>
                <div><b>Patient:</b> {patient_name} (Age: {age}, Gender: {gender})</div>
                <div><b>Reason for Visit:</b> {reason_for_visit}</div>
                <div><b>Doctor:</b> {doctor_name} · {specialization}</div>
                <div><b>Date &amp; Time:</b> {format_date(date_str)} at {format_time_12h(appointment_time)}</div>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Failed to book appointment: {e}")


# ── View ──────────────────────────────────────────────────────────────────────
def _render_view_tab() -> None:
    lang = get_lang(st.session_state)
    try:
        all_apts = db.get_appointments()
    except Exception:
        all_apts = []

    total       = len(all_apts)
    scheduled   = sum(1 for a in all_apts if a.get("status") == "scheduled")
    completed   = sum(1 for a in all_apts if a.get("status") == "completed")
    cancelled   = sum(1 for a in all_apts if a.get("status") == "cancelled")
    rescheduled = sum(1 for a in all_apts if a.get("status") == "rescheduled")

    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("Total",        total)
    s2.metric("Scheduled",    scheduled)
    s3.metric("Completed",    completed)
    s4.metric("Cancelled",    cancelled)
    s5.metric("Rescheduled",  rescheduled)

    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        patient_filter = st.text_input(t("search_patient", lang), placeholder=t("leave_blank_all", lang))
    with c2:
        status_filter  = st.selectbox(t("filter_by_status", lang), ["All", "scheduled", "completed", "cancelled", "rescheduled"])

    status  = None if status_filter == "All" else status_filter
    patient = patient_filter.strip() or None

    try:
        appointments = db.get_appointments(patient_name=patient, status=status)
    except Exception as e:
        st.error(f"Failed to load appointments: {e}")
        return

    if not appointments:
        st.markdown(f"""
        <div style="text-align:center; padding:2.5rem; color:#6B7280; font-size:0.9rem;">
            {t("no_appointments", lang)}
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown(f"<div class='section-label'>{len(appointments)} appointment(s) found</div>", unsafe_allow_html=True)
    rows = appointments_to_display_rows(appointments)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ── Cancel ────────────────────────────────────────────────────────────────────
def _render_cancel_tab() -> None:
    lang = get_lang(st.session_state)
    st.markdown(f"""
    <div style="background:#FEF2F2; border:1px solid #FECACA; border-radius:10px;
                padding:0.85rem 1.1rem; margin-bottom:1rem; font-size:0.85rem; color:#7F1D1D;">
        ❌ {t("tab_cancel", lang).replace("❌ ","")} — enter Appointment ID below.
    </div>
    """, unsafe_allow_html=True)

    apt_id = st.number_input("Appointment ID", min_value=1, step=1, label_visibility="collapsed")
    if st.button(t("look_up", lang) + " Appointment", use_container_width=False):
        apt = db.get_appointment_by_id(int(apt_id))
        if not apt:
            st.error(f"No appointment found with ID {apt_id}.")
        else:
            st.session_state["cancel_apt"] = apt

    if "cancel_apt" in st.session_state:
        apt = st.session_state["cancel_apt"]
        if apt.get("status") == "cancelled":
            st.warning("This appointment is already cancelled.")
            del st.session_state["cancel_apt"]
            return

        st.markdown(f"""
        <div style="background:#111827; border:1px solid #E2E8F0; border-radius:12px;
                    padding:1rem 1.25rem; font-size:0.88rem; line-height:1.9;">
            <div style="font-weight:700; margin-bottom:0.5rem; color:#F9FAFB;">Appointment Details</div>
            <div><b>ID:</b> #{apt['id']}</div>
            <div><b>Hospital:</b> {apt.get('hospital_name', 'General Hospital')}</div>
            <div><b>{t("patient_name", lang)}:</b> {apt['patient_name']}</div>
            <div><b>{t("doctor_name", lang)}:</b> {apt['doctor_name']} · {apt['specialization']}</div>
            <div><b>Date &amp; Time:</b> {format_date(apt['appointment_date'])} at {format_time_12h(apt['appointment_time'])}</div>
            <div><b>Status:</b> {get_status_emoji(apt['status'])} {apt['status'].capitalize()}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button(t("confirm_cancel_btn", lang), type="primary"):
                try:
                    if db.update_appointment_status(apt["id"], "cancelled"):
                        st.success(f"✅ Appointment #{apt['id']} cancelled.")
                        del st.session_state["cancel_apt"]
                    else:
                        st.error("Cancellation failed.")
                except Exception as e:
                    st.error(f"Error: {e}")
        with col2:
            if st.button(t("go_back", lang)):
                del st.session_state["cancel_apt"]


# ── Reschedule ────────────────────────────────────────────────────────────────
def _render_reschedule_tab() -> None:
    lang = get_lang(st.session_state)
    st.markdown(f"""
    <div style="background:#F0F9FF; border:1px solid #BAE6FD; border-radius:10px;
                padding:0.85rem 1.1rem; margin-bottom:1rem; font-size:0.85rem; color:#0C4A6E;">
        🔄 {t("tab_reschedule", lang).replace("🔄 ","")} — enter Appointment ID.
    </div>
    """, unsafe_allow_html=True)

    apt_id = st.number_input("Appointment ID", min_value=1, step=1, key="reschedule_id", label_visibility="collapsed")
    if st.button(t("look_up", lang) + " Appointment", key="lookup_reschedule"):
        apt = db.get_appointment_by_id(int(apt_id))
        if not apt:
            st.error(f"No appointment found with ID {apt_id}.")
        elif apt.get("status") == "cancelled":
            st.error("Cannot reschedule a cancelled appointment.")
        else:
            st.session_state["reschedule_apt"] = apt

    if "reschedule_apt" in st.session_state:
        apt = st.session_state["reschedule_apt"]
        st.markdown(f"""
        <div style="background:#111827; border:1px solid #E2E8F0; border-radius:12px;
                    padding:1rem 1.25rem; font-size:0.88rem; line-height:1.9; margin-bottom:1rem;">
            <div style="font-weight:700; color:#F9FAFB; margin-bottom:0.4rem;">Current Appointment</div>
            <div><b>{t("patient_name", lang)}:</b> {apt['patient_name']}</div>
            <div><b>{t("doctor_name", lang)}:</b> {apt['doctor_name']} · {apt['specialization']}</div>
            <div><b>Current:</b> {format_date(apt['appointment_date'])} at {format_time_12h(apt['appointment_time'])}</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("reschedule_form"):
            new_date = st.date_input(
                t("new_date", lang),
                value=date.today() + timedelta(days=1),
                min_value=date.today(),
                max_value=date.today() + timedelta(days=365),
            )
            new_time  = st.selectbox(t("new_time", lang), TIME_SLOTS)
            submitted = st.form_submit_button(t("confirm_reschedule_btn", lang), type="primary")

        if submitted:
            ok, msg = validate_appointment_date(new_date)
            if not ok:
                st.error(msg)
                return
            new_date_str = date_to_str(new_date)
            if db.check_duplicate_appointment(apt.get("hospital_name", "General Hospital"), apt["doctor_name"], new_date_str, new_time):
                st.error(f"⚠️ Slot already taken at **{apt.get('hospital_name', 'General Hospital')}** for {format_date(new_date_str)} {format_time_12h(new_time)}.")
                return
            try:
                if db.reschedule_appointment(apt["id"], new_date_str, new_time):
                    st.success(f"✅ Rescheduled to {format_date(new_date_str)} at {format_time_12h(new_time)}.")
                    del st.session_state["reschedule_apt"]
                else:
                    st.error("Reschedule failed. Please try again.")
            except Exception as e:
                st.error(f"Error: {e}")


# ── Mark as Completed ─────────────────────────────────────────────────────────
def _render_complete_tab() -> None:
    lang = get_lang(st.session_state)
    st.markdown(f"""
    <div style="background:#F0FDF4; border:1px solid #BBF7D0; border-radius:10px;
                padding:0.85rem 1.1rem; margin-bottom:1rem; font-size:0.85rem; color:#065F46;">
        ✅ {t("tab_complete", lang).replace("✅ ","")} — enter Appointment ID.
    </div>
    """, unsafe_allow_html=True)

    apt_id = st.number_input("Appointment ID", min_value=1, step=1, key="complete_apt_id", label_visibility="collapsed")
    if st.button(t("look_up", lang) + " Appointment", key="lookup_complete"):
        apt = db.get_appointment_by_id(int(apt_id))
        if not apt:
            st.error(f"No appointment found with ID {apt_id}.")
        elif apt.get("status") == "completed":
            st.warning("This appointment is already marked as completed.")
        elif apt.get("status") == "cancelled":
            st.error("Cannot complete a cancelled appointment.")
        else:
            st.session_state["complete_apt"] = apt

    if "complete_apt" in st.session_state:
        apt = st.session_state["complete_apt"]
        st.markdown(f"""
        <div style="background:#111827; border:1px solid #E2E8F0; border-radius:12px;
                    padding:1rem 1.25rem; font-size:0.88rem; line-height:1.9;">
            <div style="font-weight:700; margin-bottom:0.5rem; color:#F9FAFB;">Appointment Details</div>
            <div><b>ID:</b> #{apt['id']}</div>
            <div><b>Hospital:</b> {apt.get('hospital_name', 'General Hospital')}</div>
            <div><b>{t("patient_name", lang)}:</b> {apt['patient_name']}</div>
            <div><b>{t("doctor_name", lang)}:</b> {apt['doctor_name']} &middot; {apt['specialization']}</div>
            <div><b>Date &amp; Time:</b> {format_date(apt['appointment_date'])} at {format_time_12h(apt['appointment_time'])}</div>
            <div><b>Status:</b> {get_status_emoji(apt['status'])} {apt['status'].capitalize()}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button(t("mark_completed_btn", lang), type="primary", key="confirm_complete"):
                try:
                    if db.update_appointment_status(apt["id"], "completed"):
                        st.success(f"✅ Appointment #{apt['id']} marked as completed.")
                        del st.session_state["complete_apt"]
                    else:
                        st.error("Update failed. Please try again.")
                except Exception as e:
                    st.error(f"Error: {e}")
        with col2:
            if st.button(t("go_back", lang), key="back_complete"):
                del st.session_state["complete_apt"]



def _render_doctor_availability_tab() -> None:
    lang = get_lang(st.session_state)
    c1, c2 = st.columns(2)
    with c1:
        all_doctors  = db.get_all_doctors()
        doctor_names = [d["doctor_name"] for d in all_doctors]
        selected_doc = st.selectbox(t("select_doctor", lang), doctor_names)
    with c2:
        check_date = st.date_input("Check Date", value=date.today() + timedelta(days=1), min_value=date.today())

    if st.button(t("check_availability", lang), type="primary"):
        doctor_slots = db.get_doctor_slots(selected_doc)
        if not doctor_slots:
            st.warning("No slot information found for this doctor.")
            return
        date_str = date_to_str(check_date)
        existing = db.get_appointments(status="scheduled")
        booked   = {
            apt["appointment_time"]
            for apt in existing
            if apt["doctor_name"].lower() == selected_doc.lower()
            and apt["appointment_date"] == date_str
        }
        st.markdown(f"""
        <div style="font-weight:700; color:#F9FAFB; font-size:0.95rem; margin:0.75rem 0 0.5rem;">
            {selected_doc}  ·  {format_date(date_str)}
        </div>
        """, unsafe_allow_html=True)
        cols = st.columns(5)
        for i, slot in enumerate(doctor_slots):
            col = cols[i % 5]
            if slot in booked:
                col.markdown(f"""
                <div style="background:#FEE2E2;border:1px solid #FECACA;border-radius:8px;
                            padding:0.6rem;text-align:center;font-size:0.8rem;">
                    🔴 <b>{format_time_12h(slot)}</b><br>
                    <span style="color:#7F1D1D;font-size:0.72rem;">{t("booked", lang)}</span>
                </div>""", unsafe_allow_html=True)
            else:
                col.markdown(f"""
                <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;
                            padding:0.6rem;text-align:center;font-size:0.8rem;">
                    🟢 <b>{format_time_12h(slot)}</b><br>
                    <span style="color:#15803D;font-size:0.72rem;">{t("available", lang)}</span>
                </div>""", unsafe_allow_html=True)


# ── Main render ───────────────────────────────────────────────────────────────
def render() -> None:
    lang = get_lang(st.session_state)
    st.markdown(f"""
    <div class="page-header">
        <div style="display:flex; align-items:center; gap:1rem;">
            <span style="font-size:2.2rem;">📅</span>
            <div>
                <h1 style="margin:0;">{t("appointment_title", lang)}</h1>
                <p style="margin:0;">{t("appointment_subtitle", lang)}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs([
        t("tab_book", lang), t("tab_view_appointments", lang), t("tab_complete", lang),
        t("tab_cancel", lang), t("tab_reschedule", lang), t("tab_availability", lang),
    ])
    with tabs[0]: _render_book_tab()
    with tabs[1]: _render_view_tab()
    with tabs[2]: _render_complete_tab()
    with tabs[3]: _render_cancel_tab()
    with tabs[4]: _render_reschedule_tab()
    with tabs[5]: _render_doctor_availability_tab()
