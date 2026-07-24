"""
Prescription Reminder Agent — with Caregiver Notification + Missed-Medicine Alert
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

from database import database as db
from services.caregiver_service import notify_caregivers_for_reminder
from utils.constants import FREQUENCY_OPTIONS
from utils.helpers import format_time_12h, reminders_to_display_rows
from utils.i18n import t, get_lang
from utils.validators import validate_dosage, validate_medicine_name, validate_reminder_time

logger = logging.getLogger(__name__)

FREQ_ICONS = {
    "Once daily":        "1️⃣",
    "Twice daily":       "2️⃣",
    "Three times daily": "3️⃣",
    "Four times daily":  "4️⃣",
    "Every 6 hours":     "⏰",
    "Every 8 hours":     "⏰",
    "Every 12 hours":    "⏰",
    "Weekly":            "📅",
    "As needed":         "🔔",
}

MED_COLORS = [
    ("linear-gradient(135deg,#EFF6FF,#DBEAFE)", "1px solid #BFDBFE"),
    ("linear-gradient(135deg,#F0FDF4,#DCFCE7)", "1px solid #BBF7D0"),
    ("linear-gradient(135deg,#FFF7ED,#FED7AA)", "1px solid #FDBA74"),
    ("linear-gradient(135deg,#FDF4FF,#F5D0FE)", "1px solid #E879F9"),
    ("linear-gradient(135deg,#F0F9FF,#BAE6FD)", "1px solid #7DD3FC"),
    ("linear-gradient(135deg,#FFF1F2,#FECDD3)", "1px solid #FDA4AF"),
]


def _get_next_reminder(reminders: List[Dict]) -> Optional[Dict]:
    now_str  = datetime.now().strftime("%H:%M")
    upcoming = [r for r in reminders if r.get("reminder_time", "") >= now_str]
    if upcoming:
        return min(upcoming, key=lambda r: r.get("reminder_time", ""))
    return min(reminders, key=lambda r: r.get("reminder_time", "")) if reminders else None


# ── Caregiver info helper ─────────────────────────────────────────────────────

def _render_caregiver_info(patient_name: str) -> None:
    """Show linked caregivers for a patient as an info banner."""
    if not patient_name:
        return
    try:
        caregivers = db.get_caregivers_for_patient(patient_name)
    except Exception:
        return
    if not caregivers:
        return
    names = ", ".join(
        f"{cg['caregiver_name']} ({cg['relationship']})" for cg in caregivers
    )
    st.markdown(f"""
    <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:10px;
                padding:0.75rem 1rem;font-size:0.83rem;color:#15803D;margin-top:0.5rem;">
        👨‍👩‍👧 <b>Caregivers linked:</b> {names} — they will receive this reminder automatically.
    </div>
    """, unsafe_allow_html=True)


# ── View ──────────────────────────────────────────────────────────────────────
def _render_view_tab() -> None:
    lang = get_lang(st.session_state)
    patient_filter = st.text_input(
        t("search_patient", lang),
        placeholder=t("leave_blank_all", lang),
        key="view_reminder_filter",
    )
    patient = patient_filter.strip() or None

    try:
        reminders = db.get_reminders(patient_name=patient, active_only=True)
    except Exception as e:
        st.error(f"Failed to load reminders: {e}")
        return

    if not reminders:
        lang = get_lang(st.session_state)
        st.markdown(f"""
        <div style="text-align:center; padding:3rem; color:#94A3B8; font-size:0.9rem;">
            {t("no_reminders", lang)}
        </div>
        """, unsafe_allow_html=True)
        return

    # Next reminder banner
    nxt = _get_next_reminder(reminders)
    if nxt:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0EA5E9,#0284C7); border-radius:12px;
                    padding:1rem 1.5rem; margin-bottom:1.25rem; display:flex;
                    align-items:center; gap:1rem;">
            <span style="font-size:2rem;">⏰</span>
            <div>
                <div style="font-size:0.7rem; font-weight:700; text-transform:uppercase;
                             letter-spacing:0.1em; color:rgba(255,255,255,0.7);">Next Reminder</div>
                <div style="font-size:1.05rem; font-weight:700; color:#FFFFFF; margin-top:0.15rem;">
                    {nxt['medicine_name']}  ·  {format_time_12h(nxt['reminder_time'])}
                </div>
                <div style="font-size:0.8rem; color:rgba(255,255,255,0.75);">{nxt['frequency']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"<div class='section-label'>{len(reminders)} active reminder(s)</div>", unsafe_allow_html=True)

    cols_per_row = 3
    for i in range(0, len(reminders), cols_per_row):
        row_reminders = reminders[i:i+cols_per_row]
        cols = st.columns(cols_per_row)
        for col, reminder in zip(cols, row_reminders):
            bg, border = MED_COLORS[reminder["id"] % len(MED_COLORS)]
            freq_icon  = FREQ_ICONS.get(reminder["frequency"], "💊")
            # Build optional rows OUTSIDE the f-string to avoid </div> leaking as literal text
            patient_row = (
                '<div>👤 <b>' + reminder["patient_name"] + '</b></div>'
                if reminder.get("patient_name") else ""
            )
            notes_row = (
                '<div style="color:#64748B; font-size:0.78rem; margin-top:0.25rem;">'
                + reminder["notes"] + '</div>'
                if reminder.get("notes") else ""
            )
            with col:
                st.markdown(f"""
                <div style="background:{bg}; border:{border}; border-radius:14px;
                            padding:1.1rem 1.25rem; margin-bottom:0.5rem;">
                    <div style="display:flex; justify-content:space-between;
                                align-items:flex-start; margin-bottom:0.75rem;">
                        <div style="font-size:1rem; font-weight:700; color:#0F172A; line-height:1.3;">
                            💊 {reminder['medicine_name']}
                        </div>
                        <span style="font-size:0.68rem; background:rgba(255,255,255,0.85);
                                     border-radius:99px; padding:2px 8px;
                                     color:#475569; font-weight:600;">
                            #{reminder['id']}
                        </span>
                    </div>
                    <div style="font-size:0.83rem; color:#475569; line-height:1.8;">
                        <div>📏 <b>{reminder['dosage']}</b></div>
                        <div>⌛ <b>{format_time_12h(reminder['reminder_time'])}</b></div>
                        <div>{freq_icon} {reminder['frequency']}</div>
                        {patient_row}
                        {notes_row}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # ── Per-card action buttons (real Streamlit widgets) ─────────────────────────
                b1, b2, b3 = st.columns(3)
                with b1:
                    if st.button(
                        "✅ Taken",
                        key=f"taken_{reminder['id']}",
                        use_container_width=True,
                        help="Mark this dose as taken",
                    ):
                        try:
                            db.delete_reminder(reminder["id"])
                            st.success(f"✅ #{reminder['id']} marked as taken!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                with b2:
                    if st.button(
                        "✏️ Edit",
                        key=f"edit_{reminder['id']}",
                        use_container_width=True,
                        help="Edit this reminder",
                    ):
                        st.session_state["editing_reminder"] = reminder
                        st.info(f"Go to ✏️ Edit tab — #{reminder['id']} pre-loaded.")
                with b3:
                    if st.button(
                        "🗑️ Del",
                        key=f"del_{reminder['id']}",
                        use_container_width=True,
                        help="Delete this reminder",
                    ):
                        st.session_state["deleting_reminder"] = reminder
                        st.info(f"Go to 🗑️ Delete tab — #{reminder['id']} pre-loaded.")
                st.markdown("<div style='margin-bottom:0.35rem;'></div>", unsafe_allow_html=True)
    with st.expander("📊 View as Table", expanded=False):
        rows = reminders_to_display_rows(reminders)
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ── Add ───────────────────────────────────────────────────────────────────────
def _render_add_tab() -> None:
    lang = get_lang(st.session_state)
    st.markdown(f"""
    <div style="background:#F0F9FF; border:1px solid #BAE6FD; border-radius:10px;
                padding:0.85rem 1.1rem; margin-bottom:1.25rem; font-size:0.85rem; color:#0C4A6E;">
        ➕ {t("tab_add_reminder", lang).replace("➕ ", "")} — {t("notify_caregiver_check", lang)}
    </div>
    """, unsafe_allow_html=True)

    with st.form("add_reminder_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            medicine_name = st.text_input(t("medicine_name", lang), placeholder=t("medicine_placeholder", lang))
            dosage        = st.text_input(t("dosage", lang),         placeholder=t("dosage_placeholder", lang))
            patient_name  = st.text_input(t("patient_name_optional", lang), placeholder=t("patient_name_placeholder", lang))
        with c2:
            reminder_time = st.time_input(t("reminder_time", lang), value=datetime.strptime("08:00", "%H:%M").time())
            frequency     = st.selectbox(t("frequency", lang), FREQUENCY_OPTIONS)
            notes         = st.text_area(t("notes", lang), placeholder=t("notes_placeholder", lang))

        st.markdown("<hr style='margin:0.75rem 0;border-color:#E2E8F0;'>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='font-weight:700;font-size:0.88rem;color:#0F172A;margin-bottom:0.5rem;'>"
            f"{t('doctor_info_section', lang)}</div>",
            unsafe_allow_html=True,
        )
        c3, c4 = st.columns(2)
        with c3:
            doctor_name = st.text_input(t("doctor_name", lang), placeholder=t("doctor_name_placeholder", lang))
        with c4:
            notify_caregiver = st.checkbox(t("notify_caregiver_check", lang), value=True)

        submitted = st.form_submit_button(t("add_reminder_btn", lang), type="primary", use_container_width=True)

    if submitted:
        errors = []
        for fn, val in [(validate_medicine_name, medicine_name), (validate_dosage, dosage)]:
            ok, msg = fn(val)
            if not ok:
                errors.append(msg)

        time_str = reminder_time.strftime("%H:%M")
        ok, msg  = validate_reminder_time(time_str)
        if not ok:
            errors.append(msg)

        if errors:
            for err in errors:
                st.error(err)
            return

        try:
            rid = db.create_reminder(
                medicine_name=medicine_name.strip(),
                dosage=dosage.strip(),
                reminder_time=time_str,
                frequency=frequency,
                patient_name=patient_name.strip(),
                notes=notes.strip(),
            )
            st.markdown(f"""
            <div style="background:#F0FDF4; border-left:4px solid #10B981; border-radius:10px;
                        padding:1rem 1.25rem; font-size:0.88rem; color:#065F46;">
                <div style="font-weight:700; font-size:1rem; margin-bottom:0.5rem;">✅ Reminder Added! (ID: #{rid})</div>
                <div><b>Medicine:</b> {medicine_name}</div>
                <div><b>Dosage:</b> {dosage}</div>
                <div><b>Time:</b> {format_time_12h(time_str)}</div>
                <div><b>Frequency:</b> {frequency}</div>
            </div>
            """, unsafe_allow_html=True)

            # Caregiver notification
            if notify_caregiver and patient_name.strip():
                with st.spinner("📤 Notifying caregivers…"):
                    results = notify_caregivers_for_reminder(
                        patient_name=patient_name.strip(),
                        medicine_name=medicine_name.strip(),
                        dosage=dosage.strip(),
                        reminder_time=time_str,
                        frequency=frequency,
                        doctor_name=doctor_name.strip(),
                        special_instructions=notes.strip(),
                        is_missed=False,
                    )
                if results:
                    for r in results:
                        icon = "✅" if r["success"] else "⚠️"
                        st.markdown(
                            f"<div style='font-size:0.82rem;color:#475569;margin-top:0.3rem;'>"
                            f"{icon} Notified <b>{r['caregiver_name']}</b> via {r['channel']}: {r['message']}</div>",
                            unsafe_allow_html=True,
                        )
                else:
                    st.info("ℹ️ No caregivers linked to this patient. Add one in Caregiver Management.")
        except Exception as e:
            st.error(f"Failed to add reminder: {e}")

    # Show linked caregivers live (outside form)
    if "view_reminder_filter" not in st.session_state:
        st.session_state["view_reminder_filter"] = ""


# ── Edit ──────────────────────────────────────────────────────────────────────
def _render_edit_tab() -> None:
    lang = get_lang(st.session_state)
    rid = st.number_input(t("tab_edit_reminder", lang), min_value=1, step=1, key="edit_rid", label_visibility="collapsed")
    if st.button(t("load", lang) + " Reminder", key="load_edit"):
        r = db.get_reminder_by_id(int(rid))
        if not r:
            st.error(f"No reminder found with ID {rid}.")
        elif not r.get("is_active"):
            st.error("This reminder has been deleted.")
        else:
            st.session_state["editing_reminder"] = r

    if "editing_reminder" in st.session_state:
        r = st.session_state["editing_reminder"]
        with st.form("edit_reminder_form"):
            c1, c2 = st.columns(2)
            with c1:
                new_name    = st.text_input(t("medicine_name", lang), value=r["medicine_name"])
                new_dosage  = st.text_input(t("dosage", lang),         value=r["dosage"])
                new_patient = st.text_input(t("patient_name_optional", lang), value=r.get("patient_name") or "")
            with c2:
                cur_time    = datetime.strptime(r["reminder_time"], "%H:%M").time()
                new_time    = st.time_input(t("reminder_time", lang), value=cur_time)
                cur_idx     = FREQUENCY_OPTIONS.index(r["frequency"]) if r["frequency"] in FREQUENCY_OPTIONS else 0
                new_freq    = st.selectbox(t("frequency", lang), FREQUENCY_OPTIONS, index=cur_idx)
                new_notes   = st.text_area(t("notes", lang), value=r.get("notes") or "")
            submitted = st.form_submit_button(t("save_changes", lang), type="primary", use_container_width=True)

        if submitted:
            errors = []
            for fn, val in [(validate_medicine_name, new_name), (validate_dosage, new_dosage)]:
                ok, msg = fn(val)
                if not ok:
                    errors.append(msg)
            new_time_str = new_time.strftime("%H:%M")
            ok, msg = validate_reminder_time(new_time_str)
            if not ok:
                errors.append(msg)
            if errors:
                for err in errors:
                    st.error(err)
                return
            try:
                if db.update_reminder(
                    reminder_id=r["id"],
                    medicine_name=new_name.strip(),
                    dosage=new_dosage.strip(),
                    reminder_time=new_time_str,
                    frequency=new_freq,
                    patient_name=new_patient.strip(),
                    notes=new_notes.strip(),
                ):
                    st.success(f"✅ Reminder #{r['id']} updated!")
                    del st.session_state["editing_reminder"]
                else:
                    st.error("Update failed.")
            except Exception as e:
                st.error(f"Error: {e}")


# ── Delete ────────────────────────────────────────────────────────────────────
def _render_delete_tab() -> None:
    lang = get_lang(st.session_state)
    st.markdown(f"""
    <div style="background:#FEF2F2; border:1px solid #FECACA; border-radius:10px;
                padding:0.85rem 1.1rem; margin-bottom:1rem; font-size:0.85rem; color:#7F1D1D;">
        🗑️ {t("tab_delete_reminder", lang).replace("🗑️ ", "")} — deactivates it from active reminders.
    </div>
    """, unsafe_allow_html=True)

    rid = st.number_input(t("tab_delete_reminder", lang), min_value=1, step=1, key="del_rid", label_visibility="collapsed")
    if st.button(t("look_up", lang) + " Reminder", key="lookup_del"):
        r = db.get_reminder_by_id(int(rid))
        if not r:
            st.error(f"No reminder found with ID {rid}.")
        elif not r.get("is_active"):
            st.warning("This reminder is already deleted.")
        else:
            st.session_state["deleting_reminder"] = r

    if "deleting_reminder" in st.session_state:
        r = st.session_state["deleting_reminder"]
        st.markdown(f"""
        <div style="background:#FFF7ED; border:1px solid #FED7AA; border-radius:12px;
                    padding:1rem 1.25rem; font-size:0.88rem; line-height:1.9; margin-bottom:0.75rem;">
            <div style="font-weight:700; color:#0F172A; margin-bottom:0.4rem;">⚠️ Confirm Deletion</div>
            <div><b>ID:</b> #{r['id']}</div>
            <div><b>Medicine:</b> {r['medicine_name']}</div>
            <div><b>Dosage:</b> {r['dosage']}</div>
            <div><b>Time:</b> {format_time_12h(r['reminder_time'])}</div>
            <div><b>Frequency:</b> {r['frequency']}</div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns([1, 4])
        with c1:
            if st.button(t("delete", lang), type="primary"):
                try:
                    if db.delete_reminder(r["id"]):
                        st.success(f"✅ Reminder #{r['id']} deleted.")
                        del st.session_state["deleting_reminder"]
                    else:
                        st.error("Update failed.")
                except Exception as e:
                    st.error(f"Error: {e}")
        with c2:
            if st.button(t("cancel", lang), key="cancel_delete"):
                del st.session_state["deleting_reminder"]


# ── Missed Medicine Alert ─────────────────────────────────────────────────────
def _render_missed_medicine_tab() -> None:
    lang = get_lang(st.session_state)
    st.markdown(f"""
    <div style="background:#FFF7ED; border:1px solid #FED7AA; border-radius:10px;
                padding:0.85rem 1.1rem; margin-bottom:1.25rem; font-size:0.85rem; color:#92400E;">
        ⚠️ {t("tab_missed_medicine", lang).replace("⚠️ ", "")}
    </div>
    """, unsafe_allow_html=True)

    with st.form("missed_medicine_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            m_patient  = st.text_input(t("patient_name", lang)+"*",   placeholder=t("patient_name_placeholder", lang))
            m_medicine = st.text_input(t("medicine_name", lang),       placeholder=t("medicine_placeholder", lang))
            m_dosage   = st.text_input(t("dosage", lang),              placeholder=t("dosage_placeholder", lang))
        with c2:
            m_time     = st.time_input(t("scheduled_time", lang),      value=datetime.strptime("08:00", "%H:%M").time())
            m_freq     = st.selectbox(t("frequency", lang),            FREQUENCY_OPTIONS)
            m_doctor   = st.text_input(t("doctor_name", lang),         placeholder=t("doctor_name_placeholder", lang))

        m_notes = st.text_area(t("special_instructions", lang), placeholder=t("notes_placeholder", lang))
        submitted = st.form_submit_button(t("send_missed_alert", lang), type="primary", use_container_width=True)

    if submitted:
        errors = []
        for fn, val in [
            (validate_medicine_name, m_medicine),
            (validate_dosage,        m_dosage),
        ]:
            ok, msg = fn(val)
            if not ok:
                errors.append(msg)
        if not m_patient.strip():
            errors.append("Patient name is required.")
        if errors:
            for err in errors:
                st.error(err)
            return

        time_str = m_time.strftime("%H:%M")
        with st.spinner("📤 Sending missed medicine alert to caregivers…"):
            results = notify_caregivers_for_reminder(
                patient_name=m_patient.strip(),
                medicine_name=m_medicine.strip(),
                dosage=m_dosage.strip(),
                reminder_time=time_str,
                frequency=m_freq,
                doctor_name=m_doctor.strip(),
                special_instructions=m_notes.strip(),
                is_missed=True,
            )

        if not results:
            st.warning(f"No active caregivers found for '{m_patient.strip()}'. Add a caregiver in Caregiver Management.")
        else:
            st.markdown("""
            <div style="background:#FEF2F2; border-left:4px solid #EF4444; border-radius:10px;
                        padding:1rem 1.25rem; font-size:0.88rem; color:#7F1D1D; margin-bottom:0.75rem;">
                <div style="font-weight:700; font-size:1rem; margin-bottom:0.4rem;">⚠️ Missed Medicine Alert Sent</div>
            </div>
            """, unsafe_allow_html=True)
            for r in results:
                icon = "✅" if r["success"] else "❌"
                st.markdown(
                    f"<div style='font-size:0.85rem;color:#475569;margin-bottom:0.2rem;'>"
                    f"{icon} <b>{r['caregiver_name']}</b> via {r['channel']}: {r['message']}</div>",
                    unsafe_allow_html=True,
                )


# ── Main render ───────────────────────────────────────────────────────────────
def render() -> None:
    lang = get_lang(st.session_state)
    st.markdown(f"""
    <div class="page-header">
        <div style="display:flex; align-items:center; gap:1rem;">
            <span style="font-size:2.2rem;">💊</span>
            <div>
                <h1 style="margin:0;">{t("prescription_title", lang)}</h1>
                <p style="margin:0;">{t("prescription_subtitle", lang)}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs([
        t("tab_view_reminders", lang),
        t("tab_add_reminder", lang),
        t("tab_edit_reminder", lang),
        t("tab_delete_reminder", lang),
        t("tab_missed_medicine", lang),
    ])
    with tabs[0]: _render_view_tab()
    with tabs[1]: _render_add_tab()
    with tabs[2]: _render_edit_tab()
    with tabs[3]: _render_delete_tab()
    with tabs[4]: _render_missed_medicine_tab()
