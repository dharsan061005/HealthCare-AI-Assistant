"""
Prescription Reminder Agent — redesigned UI
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

from database import database as db
from utils.constants import FREQUENCY_OPTIONS
from utils.helpers import format_time_12h, reminders_to_display_rows
from utils.validators import validate_dosage, validate_medicine_name, validate_reminder_time

logger = logging.getLogger(__name__)

FREQ_ICONS = {
    "Once daily":       "1️⃣",
    "Twice daily":      "2️⃣",
    "Three times daily":"3️⃣",
    "Four times daily": "4️⃣",
    "Every 6 hours":    "⏰",
    "Every 8 hours":    "⏰",
    "Every 12 hours":   "⏰",
    "Weekly":           "📅",
    "As needed":        "🔔",
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


# ── View ──────────────────────────────────────────────────────────────────────
def _render_view_tab() -> None:
    patient_filter = st.text_input(
        "Filter by Patient Name", placeholder="Leave blank to see all", key="view_reminder_filter"
    )
    patient = patient_filter.strip() or None

    try:
        reminders = db.get_reminders(patient_name=patient, active_only=True)
    except Exception as e:
        st.error(f"Failed to load reminders: {e}")
        return

    if not reminders:
        st.markdown("""
        <div style="text-align:center; padding:3rem; color:#94A3B8; font-size:0.9rem;">
            💊 No active reminders. Add one using the <b>Add Reminder</b> tab.
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

    # Card grid
    cols_per_row = 3
    for i in range(0, len(reminders), cols_per_row):
        row_reminders = reminders[i:i+cols_per_row]
        cols = st.columns(cols_per_row)
        for col, reminder in zip(cols, row_reminders):
            bg, border = MED_COLORS[reminder["id"] % len(MED_COLORS)]
            freq_icon  = FREQ_ICONS.get(reminder["frequency"], "💊")
            with col:
                st.markdown(f"""
                <div style="background:{bg}; border:{border}; border-radius:14px;
                            padding:1.1rem 1.25rem; margin-bottom:0.75rem; height:100%;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.75rem;">
                        <div style="font-size:1rem; font-weight:700; color:#0F172A; line-height:1.3;">
                            💊 {reminder['medicine_name']}
                        </div>
                        <span style="font-size:0.68rem; background:rgba(255,255,255,0.8);
                                     border-radius:99px; padding:2px 8px; color:#475569; font-weight:600;">
                            #{reminder['id']}
                        </span>
                    </div>
                    <div style="font-size:0.83rem; color:#475569; line-height:1.8;">
                        <div>📏 <b>{reminder['dosage']}</b></div>
                        <div>⏰ <b>{format_time_12h(reminder['reminder_time'])}</b></div>
                        <div>{freq_icon} {reminder['frequency']}</div>
                        {'<div>👤 ' + reminder['patient_name'] + '</div>' if reminder.get('patient_name') else ''}
                        {'<div style="color:#94A3B8; font-size:0.78rem; margin-top:0.25rem;">' + reminder['notes'] + '</div>' if reminder.get('notes') else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Full table
    with st.expander("📊 View as Table", expanded=False):
        rows = reminders_to_display_rows(reminders)
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ── Add ───────────────────────────────────────────────────────────────────────
def _render_add_tab() -> None:
    st.markdown("""
    <div style="background:#F0F9FF; border:1px solid #BAE6FD; border-radius:10px;
                padding:0.85rem 1.1rem; margin-bottom:1.25rem; font-size:0.85rem; color:#0C4A6E;">
        ➕ Fill in the details below to set up a new medicine reminder.
    </div>
    """, unsafe_allow_html=True)

    with st.form("add_reminder_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            medicine_name = st.text_input("Medicine Name *", placeholder="e.g. Metformin 500mg")
            dosage        = st.text_input("Dosage *",         placeholder="e.g. 1 tablet, 5ml")
            patient_name  = st.text_input("Patient Name (optional)", placeholder="e.g. Ravi Kumar")
        with c2:
            reminder_time = st.time_input("Reminder Time *", value=datetime.strptime("08:00", "%H:%M").time())
            frequency     = st.selectbox("Frequency *", FREQUENCY_OPTIONS)
            notes         = st.text_area("Notes (optional)", placeholder="e.g. Take after meals")

        submitted = st.form_submit_button("➕ Add Reminder", type="primary", use_container_width=True)

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
        except Exception as e:
            st.error(f"Failed to add reminder: {e}")


# ── Edit ──────────────────────────────────────────────────────────────────────
def _render_edit_tab() -> None:
    rid = st.number_input("Reminder ID to Edit", min_value=1, step=1, key="edit_rid", label_visibility="collapsed")
    if st.button("🔍 Load Reminder", key="load_edit"):
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
                new_name    = st.text_input("Medicine Name *", value=r["medicine_name"])
                new_dosage  = st.text_input("Dosage *",         value=r["dosage"])
                new_patient = st.text_input("Patient Name",    value=r.get("patient_name") or "")
            with c2:
                cur_time    = datetime.strptime(r["reminder_time"], "%H:%M").time()
                new_time    = st.time_input("Reminder Time *", value=cur_time)
                cur_idx     = FREQUENCY_OPTIONS.index(r["frequency"]) if r["frequency"] in FREQUENCY_OPTIONS else 0
                new_freq    = st.selectbox("Frequency *", FREQUENCY_OPTIONS, index=cur_idx)
                new_notes   = st.text_area("Notes", value=r.get("notes") or "")
            submitted = st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)

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
    st.markdown("""
    <div style="background:#FEF2F2; border:1px solid #FECACA; border-radius:10px;
                padding:0.85rem 1.1rem; margin-bottom:1rem; font-size:0.85rem; color:#7F1D1D;">
        🗑️ Deleting a reminder deactivates it — it won't appear in active reminders.
    </div>
    """, unsafe_allow_html=True)

    rid = st.number_input("Reminder ID to Delete", min_value=1, step=1, key="del_rid", label_visibility="collapsed")
    if st.button("🔍 Look Up Reminder", key="lookup_del"):
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
            if st.button("🗑️ Delete", type="primary"):
                try:
                    if db.delete_reminder(r["id"]):
                        st.success(f"✅ Reminder #{r['id']} deleted.")
                        del st.session_state["deleting_reminder"]
                    else:
                        st.error("Deletion failed.")
                except Exception as e:
                    st.error(f"Error: {e}")
        with c2:
            if st.button("Cancel", key="cancel_delete"):
                del st.session_state["deleting_reminder"]


# ── Main render ───────────────────────────────────────────────────────────────
def render() -> None:
    st.markdown("""
    <div class="page-header">
        <div style="display:flex; align-items:center; gap:1rem;">
            <span style="font-size:2.2rem;">💊</span>
            <div>
                <h1 style="margin:0;">Prescription Reminders</h1>
                <p style="margin:0;">Manage medicine reminders and stay on schedule</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["📋 View Reminders", "➕ Add Reminder", "✏️ Edit Reminder", "🗑️ Delete Reminder"])
    with tabs[0]: _render_view_tab()
    with tabs[1]: _render_add_tab()
    with tabs[2]: _render_edit_tab()
    with tabs[3]: _render_delete_tab()
