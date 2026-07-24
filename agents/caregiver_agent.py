"""
Caregiver Management Agent — Patient Companion Module

Tabs: Dashboard | View | Add | Edit | Delete | Notification History
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

from database import database as db
from services.caregiver_service import get_dashboard_stats, notify_caregivers_for_reminder
from utils.constants import (
    CAREGIVER_COLORS,
    NOTIFICATION_CHANNEL_ICONS,
    NOTIFICATION_METHODS,
    RELATIONSHIP_ICONS,
    RELATIONSHIP_OPTIONS,
)
from utils.helpers import (
    caregivers_to_display_rows,
    format_date,
    notification_logs_to_display_rows,
)
from utils.i18n import t, get_lang
from utils.validators import (
    validate_caregiver_name,
    validate_email_address,
    validate_patient_name,
    validate_phone_number,
)

logger = logging.getLogger(__name__)


# ─── Dashboard ────────────────────────────────────────────────────────────────

def _render_dashboard_tab() -> None:
    lang = get_lang(st.session_state)
    stats = get_dashboard_stats()

    st.markdown(f"""
    <div style="margin-bottom:1.25rem;">
        <span style="font-size:0.75rem;font-weight:700;text-transform:uppercase;
                     letter-spacing:0.08em;color:#6B7280;">{t("overview", lang)}</span>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    cards = [
        (c1, "👨‍👩‍👧", t("total_caregivers", lang),  stats["total_caregivers"], "#0EA5E9", "#EFF6FF", "#BFDBFE"),
        (c2, "⏰",       t("todays_reminders", lang), stats["todays_reminders"], "#10B981", "#F0FDF4", "#BBF7D0"),
        (c3, "📄",       t("reports_shared", lang),   stats["reports_shared"],   "#8B5CF6", "#F5F3FF", "#DDD6FE"),
        (c4, "⚠️",       t("missed_alerts", lang),    stats["missed_alerts"],    "#F59E0B", "#FFFBEB", "#FDE68A"),
    ]
    for col, icon, label, value, color, bg, border in cards:
        with col:
            st.markdown(f"""
            <div style="background:{bg};border:1px solid {border};border-radius:14px;
                        padding:1.25rem 1.4rem;text-align:center;">
                <div style="font-size:1.8rem;margin-bottom:0.4rem;">{icon}</div>
                <div style="font-size:2rem;font-weight:800;color:{color};line-height:1;">{value}</div>
                <div style="font-size:0.78rem;color:#6B7280;font-weight:600;
                             margin-top:0.35rem;text-transform:uppercase;letter-spacing:0.05em;">
                    {label}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    # Recent notification log preview
    st.markdown(f"""
    <div style="font-weight:700;font-size:0.95rem;color:#F9FAFB;margin-bottom:0.65rem;">
        {t("recent_notifications", lang)}
    </div>
    """, unsafe_allow_html=True)

    try:
        logs = db.get_notification_logs(limit=8)
    except Exception as e:
        st.error(f"Could not load notification log: {e}")
        return

    if not logs:
        st.markdown("""
        <div style="text-align:center;padding:2rem;color:#6B7280;font-size:0.88rem;">
            No notifications sent yet.
        </div>
        """, unsafe_allow_html=True)
        return

    rows = notification_logs_to_display_rows(logs)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ─── View ─────────────────────────────────────────────────────────────────────

def _render_view_tab() -> None:
    lang = get_lang(st.session_state)
    patient_filter = st.text_input(
        t("search_by_patient", lang),
        placeholder=t("leave_blank_caregivers", lang),
        key="cg_view_filter",
    )
    patient = patient_filter.strip() or None

    try:
        caregivers = db.get_caregivers(patient_name=patient, active_only=True)
    except Exception as e:
        st.error(f"Failed to load caregivers: {e}")
        return

    if not caregivers:
        st.markdown(f"""
        <div style="text-align:center;padding:3rem;color:#6B7280;font-size:0.9rem;">
            {t("no_caregivers", lang)}
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown(
        f"<div class='section-label'>{len(caregivers)} caregiver(s) found</div>",
        unsafe_allow_html=True,
    )

    cols_per_row = 3
    for i in range(0, len(caregivers), cols_per_row):
        row_cgs = caregivers[i : i + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, cg in zip(cols, row_cgs):
            bg, border, accent = CAREGIVER_COLORS[cg["id"] % len(CAREGIVER_COLORS)]
            rel_icon   = RELATIONSHIP_ICONS.get(cg["relationship"], "👤")
            notif_icon = NOTIFICATION_CHANNEL_ICONS.get(cg["notification_preference"], "🔔")
            with col:
                st.markdown(f"""
                <div style="background:{bg};border:{border};border-radius:14px;
                            padding:1.1rem 1.25rem;margin-bottom:0.75rem;height:100%;">
                    <div style="display:flex;justify-content:space-between;
                                align-items:flex-start;margin-bottom:0.75rem;">
                        <div style="font-size:1rem;font-weight:700;color:#F9FAFB;line-height:1.3;">
                            {rel_icon} {cg['caregiver_name']}
                        </div>
                        <span style="font-size:0.68rem;background:rgba(255,255,255,0.8);
                                     border-radius:99px;padding:2px 8px;
                                     color:#6B7280;font-weight:600;">#{cg['id']}</span>
                    </div>
                    <div style="font-size:0.83rem;color:#6B7280;line-height:1.9;">
                        <div>👤 <b>Patient:</b> {cg['patient_name']}</div>
                        <div>🔗 <b>Relation:</b> {cg['relationship']}</div>
                        <div>📱 {cg['mobile_number']}</div>
                        <div>📧 {cg['email']}</div>
                        <div>{notif_icon} <b>Notify via:</b> {cg['notification_preference']}</div>
                        <div style="color:#6B7280;font-size:0.75rem;margin-top:0.25rem;">
                            Added: {format_date(cg['created_at'][:10])}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with st.expander("📊 View as Table", expanded=False):
        rows = caregivers_to_display_rows(caregivers)
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ─── Add ──────────────────────────────────────────────────────────────────────

def _render_add_tab() -> None:
    lang = get_lang(st.session_state)
    st.markdown(f"""
    <div style="background:#F0F9FF;border:1px solid #BAE6FD;border-radius:10px;
                padding:0.85rem 1.1rem;margin-bottom:1.25rem;font-size:0.85rem;color:#0C4A6E;">
        ➕ {t("tab_add_caregiver", lang).replace("➕ ","")} — {t("notification_method", lang).split("*")[0]}
    </div>
    """, unsafe_allow_html=True)

    with st.form("add_caregiver_form", clear_on_submit=True):
        st.markdown(
            f"<div style='font-weight:700;font-size:0.9rem;color:#F9FAFB;"
            f"margin-bottom:0.6rem;'>{t('patient_caregiver_details', lang)}</div>",
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            patient_name    = st.text_input(t("patient_name", lang), placeholder=t("patient_name_placeholder", lang))
            caregiver_name  = st.text_input(t("caregiver_name", lang), placeholder=t("caregiver_name_placeholder", lang))
            relationship    = st.selectbox(t("relationship", lang), RELATIONSHIP_OPTIONS)
        with c2:
            mobile_number   = st.text_input(t("mobile_number", lang), placeholder=t("mobile_placeholder", lang))
            email           = st.text_input(t("email_address", lang), placeholder=t("email_placeholder", lang))
            notification_pref = st.selectbox(t("notification_method", lang), NOTIFICATION_METHODS)

        submitted = st.form_submit_button(t("save_caregiver", lang), type="primary", use_container_width=True)

    if submitted:
        errors: List[str] = []
        for fn, val in [
            (validate_patient_name,   patient_name),
            (validate_caregiver_name, caregiver_name),
            (validate_phone_number,   mobile_number),
            (validate_email_address,  email),
        ]:
            ok, msg = fn(val)
            if not ok:
                errors.append(msg)

        if errors:
            for err in errors:
                st.error(err)
            return

        try:
            cid = db.create_caregiver(
                patient_name=patient_name.strip(),
                caregiver_name=caregiver_name.strip(),
                relationship=relationship,
                mobile_number=mobile_number.strip(),
                email=email.strip(),
                notification_preference=notification_pref,
            )
            rel_icon   = RELATIONSHIP_ICONS.get(relationship, "👤")
            notif_icon = NOTIFICATION_CHANNEL_ICONS.get(notification_pref, "🔔")
            st.markdown(f"""
            <div style="background:#F0FDF4;border-left:4px solid #10B981;border-radius:10px;
                        padding:1rem 1.25rem;font-size:0.88rem;color:#065F46;">
                <div style="font-weight:700;font-size:1rem;margin-bottom:0.5rem;">
                    ✅ Caregiver Added! (ID: #{cid})
                </div>
                <div>👤 <b>Patient:</b> {patient_name.strip()}</div>
                <div>{rel_icon} <b>Caregiver:</b> {caregiver_name.strip()} ({relationship})</div>
                <div>📧 {email.strip()}</div>
                <div>📱 {mobile_number.strip()}</div>
                <div>{notif_icon} Notifications via: {notification_pref}</div>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Failed to save caregiver: {e}")


# ─── Edit ─────────────────────────────────────────────────────────────────────

def _render_edit_tab() -> None:
    lang = get_lang(st.session_state)
    cid = st.number_input(
        t("tab_edit_caregiver", lang), min_value=1, step=1,
        key="cg_edit_id", label_visibility="collapsed",
    )
    if st.button(t("load_caregiver", lang), key="cg_load_edit"):
        cg = db.get_caregiver_by_id(int(cid))
        if not cg:
            st.error(f"No caregiver found with ID {cid}.")
        elif not cg.get("is_active"):
            st.error("This caregiver has been deleted.")
        else:
            st.session_state["editing_caregiver"] = cg

    if "editing_caregiver" in st.session_state:
        cg = st.session_state["editing_caregiver"]
        with st.form("edit_caregiver_form"):
            c1, c2 = st.columns(2)
            with c1:
                new_cg_name   = st.text_input(t("caregiver_name", lang), value=cg["caregiver_name"])
                rel_idx       = RELATIONSHIP_OPTIONS.index(cg["relationship"]) if cg["relationship"] in RELATIONSHIP_OPTIONS else 0
                new_rel       = st.selectbox(t("relationship", lang), RELATIONSHIP_OPTIONS, index=rel_idx)
                new_mobile    = st.text_input(t("mobile_number", lang), value=cg["mobile_number"])
            with c2:
                new_email     = st.text_input(t("email_address", lang), value=cg["email"])
                notif_idx     = NOTIFICATION_METHODS.index(cg["notification_preference"]) if cg["notification_preference"] in NOTIFICATION_METHODS else 0
                new_notif     = st.selectbox(t("notification_method", lang), NOTIFICATION_METHODS, index=notif_idx)
                st.markdown(
                    f"<div style='font-size:0.8rem;color:#6B7280;margin-top:1.5rem;'>"
                    f"{t('patient_name', lang)}: <b>{cg['patient_name']}</b> (read-only)</div>",
                    unsafe_allow_html=True,
                )

            submitted = st.form_submit_button(t("save_changes", lang), type="primary", use_container_width=True)

        if submitted:
            errors: List[str] = []
            for fn, val in [
                (validate_caregiver_name, new_cg_name),
                (validate_phone_number,   new_mobile),
                (validate_email_address,  new_email),
            ]:
                ok, msg = fn(val)
                if not ok:
                    errors.append(msg)
            if errors:
                for err in errors:
                    st.error(err)
                return
            try:
                if db.update_caregiver(
                    caregiver_id=cg["id"],
                    caregiver_name=new_cg_name.strip(),
                    relationship=new_rel,
                    mobile_number=new_mobile.strip(),
                    email=new_email.strip(),
                    notification_preference=new_notif,
                ):
                    st.success(f"✅ Caregiver #{cg['id']} updated!")
                    del st.session_state["editing_caregiver"]
                else:
                    st.error("Update failed.")
            except Exception as e:
                st.error(f"Error: {e}")


# ─── Delete ───────────────────────────────────────────────────────────────────

def _render_delete_tab() -> None:
    lang = get_lang(st.session_state)
    st.markdown(f"""
    <div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:10px;
                padding:0.85rem 1.1rem;margin-bottom:1rem;font-size:0.85rem;color:#7F1D1D;">
        🗑️ {t("tab_delete_caregiver", lang).replace("🗑️ ","")} — deactivates their record.
    </div>
    """, unsafe_allow_html=True)

    cid = st.number_input(
        t("tab_delete_caregiver", lang), min_value=1, step=1,
        key="cg_del_id", label_visibility="collapsed",
    )
    if st.button(t("look_up_caregiver", lang), key="cg_lookup_del"):
        cg = db.get_caregiver_by_id(int(cid))
        if not cg:
            st.error(f"No caregiver found with ID {cid}.")
        elif not cg.get("is_active"):
            st.warning("This caregiver is already deleted.")
        else:
            st.session_state["deleting_caregiver"] = cg

    if "deleting_caregiver" in st.session_state:
        cg = st.session_state["deleting_caregiver"]
        rel_icon = RELATIONSHIP_ICONS.get(cg["relationship"], "👤")
        st.markdown(f"""
        <div style="background:#FFF7ED;border:1px solid #FED7AA;border-radius:12px;
                    padding:1rem 1.25rem;font-size:0.88rem;line-height:1.9;margin-bottom:0.75rem;">
            <div style="font-weight:700;color:#F9FAFB;margin-bottom:0.4rem;">⚠️ Confirm Deletion</div>
            <div><b>ID:</b> #{cg['id']}</div>
            <div><b>Patient:</b> {cg['patient_name']}</div>
            <div><b>Caregiver:</b> {rel_icon} {cg['caregiver_name']} ({cg['relationship']})</div>
            <div><b>Mobile:</b> {cg['mobile_number']}</div>
            <div><b>Email:</b> {cg['email']}</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button(t("delete", lang), type="primary", key="cg_confirm_del"):
                try:
                    if db.delete_caregiver(cg["id"]):
                        st.success(f"✅ Caregiver #{cg['id']} deleted.")
                        del st.session_state["deleting_caregiver"]
                    else:
                        st.error("Deletion failed.")
                except Exception as e:
                    st.error(f"Error: {e}")
        with col2:
            if st.button(t("cancel", lang), key="cg_cancel_del"):
                del st.session_state["deleting_caregiver"]


# ─── Notification History ─────────────────────────────────────────────────────

def _render_notifications_tab() -> None:
    lang = get_lang(st.session_state)
    st.markdown(f"""
    <div style="background:#111827;border:1px solid #E2E8F0;border-radius:10px;
                padding:0.85rem 1.1rem;margin-bottom:1.25rem;font-size:0.85rem;color:#6B7280;">
        📋 {t("tab_notifications", lang).replace("🔔 ","")} — full log of all notifications sent.
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        patient_filter = st.text_input(
            t("filter_by_patient", lang), placeholder="Leave blank for all", key="notif_patient_filter"
        )
    with col2:
        type_filter = st.selectbox(
            t("filter_by_type", lang),
            ["All", "Reminder", "Report", "Missed Medicine"],
            key="notif_type_filter",
        )

    type_map = {
        "All": None,
        "Reminder": "reminder",
        "Report": "report",
        "Missed Medicine": "missed_medicine",
    }
    try:
        logs = db.get_notification_logs(
            patient_name=patient_filter.strip() or None,
            notification_type=type_map[type_filter],
            limit=200,
        )
    except Exception as e:
        st.error(f"Could not load notification log: {e}")
        return

    if not logs:
        st.markdown("""
        <div style="text-align:center;padding:3rem;color:#6B7280;font-size:0.9rem;">
            📭 No notification records match the current filter.
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown(
        f"<div class='section-label'>{len(logs)} record(s)</div>",
        unsafe_allow_html=True,
    )
    rows = notification_logs_to_display_rows(logs)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Summary counts
    total   = len(logs)
    sent    = sum(1 for l in logs if l.get("status") == "sent")
    failed  = total - sent
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Total", total)
    with col_b:
        st.metric("✅ Sent", sent)
    with col_c:
        st.metric("❌ Failed", failed)


# ─── Test Notification ────────────────────────────────────────────────────────

def _render_test_section() -> None:
    with st.expander("🧪 Send Test Reminder Notification", expanded=False):
        lang = get_lang(st.session_state)
        st.markdown(
            "<div style='font-size:0.83rem;color:#6B7280;margin-bottom:0.75rem;'>"
            "Send a sample reminder to verify your SMTP setup.</div>",
            unsafe_allow_html=True,
        )
        test_patient = st.text_input(
            t("patient_name", lang),
            placeholder=t("patient_name_placeholder", lang),
            key="test_notif_patient",
        )
        if st.button(t("send_test_reminder", lang), key="send_test_notif"):
            if not test_patient.strip():
                st.warning("Please enter a patient name.")
                return
            with st.spinner("Sending test notification…"):
                results = notify_caregivers_for_reminder(
                    patient_name=test_patient.strip(),
                    medicine_name="Paracetamol 500mg",
                    dosage="1 tablet",
                    reminder_time="20:00",
                    frequency="Once daily",
                    doctor_name="Dr. Ananya Sharma",
                    special_instructions="Take after meals",
                    is_missed=False,
                )
            if not results:
                st.warning(f"No active caregivers found for patient '{test_patient.strip()}'.")
            else:
                for r in results:
                    icon = "✅" if r["success"] else "❌"
                    st.markdown(
                        f"{icon} **{r['caregiver_name']}** via {r['channel']}: {r['message']}"
                    )


# ─── Main render ──────────────────────────────────────────────────────────────

def render() -> None:
    lang = get_lang(st.session_state)
    st.markdown(f"""
    <div class="page-header">
        <div style="display:flex;align-items:center;gap:1rem;">
            <span style="font-size:2.2rem;">👨‍👩‍👧</span>
            <div>
                <h1 style="margin:0;">{t("caregiver_title", lang)}</h1>
                <p style="margin:0;">{t("caregiver_subtitle", lang)}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs([
        t("tab_dashboard", lang),
        t("tab_view_caregivers", lang),
        t("tab_add_caregiver", lang),
        t("tab_edit_caregiver", lang),
        t("tab_delete_caregiver", lang),
        t("tab_notifications", lang),
    ])
    with tabs[0]: _render_dashboard_tab()
    with tabs[1]: _render_view_tab()
    with tabs[2]: _render_add_tab()
    with tabs[3]: _render_edit_tab()
    with tabs[4]: _render_delete_tab()
    with tabs[5]:
        _render_notifications_tab()
        _render_test_section()
