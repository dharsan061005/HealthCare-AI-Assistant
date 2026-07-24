"""
Family Management Agent — Healthcare AI Assistant
9-section nested sidebar navigation, all powered by family.db.

Sections:
  1. 📋 Family Dashboard   → Overview | Statistics
  2. 👥 Family Members     → Add | View | Edit
  3. 📅 Appointments       → Book | Upcoming | History
  4. 💊 Medicines          → Reminders | Schedule | Missed
  5. 📄 Medical Reports    → Upload | View | AI Analysis | Compare
  6. ❤️  Health Monitoring  → Timeline | Health Score | Vitals
  7. 🚑 Emergency          → Contacts | Medical Info | Nearby Hospitals
  8. 🤖 AI Assistant       → Summary | Recommendations | Ask AI
  9. ⚙️  Settings           → Preferences | Notifications
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

import config
from database import family_db as fdb
from utils import family_utils as fu
from utils.llm import simple_query            # reuse existing LLM helper
from utils.pdf_reader import extract_text_from_uploaded_file  # reuse existing PDF reader

logger = logging.getLogger(__name__)

# ── ensure DB tables exist on first import ────────────────────────────────────
try:
    fdb.init_family_db()
except Exception as _e:
    logger.warning("Family DB init on import: %s", _e)

# ══════════════════════════════════════════════════════════════════════════════
# CSS — injected once per session
# ══════════════════════════════════════════════════════════════════════════════

_FM_CSS = """
<style>
/* ── Family page header ─────────────────────────────── */
.fm-header {
  background: linear-gradient(135deg, #FFFFFF 0%, #EFF6FF 60%, #F8F9FA 100%);
  border: 1px solid #E5E7EB;
  border-radius: 18px;
  padding: 1.6rem 2rem;
  margin-bottom: 1.5rem;
  position: relative;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.fm-header::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, transparent, #2563EB, #3B82F6, transparent);
}
.fm-header::after {
  content: '';
  position: absolute;
  top: -50%; right: -3%;
  width: 220px; height: 220px;
  background: radial-gradient(circle, rgba(37,99,235,0.08) 0%, transparent 65%);
  pointer-events: none;
}
.fm-header h1 {
  color: #111827 !important;
  font-size: 1.6rem !important;
  margin: 0 0 0.2rem !important;
  font-weight: 800 !important;
}
.fm-header p {
  color: #6B7280 !important;
  margin: 0 !important;
  font-size: 0.87rem !important;
}

/* ── Section title ──────────────────────────────────── */
.fm-section-title {
  font-size: 0.63rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #9CA3AF;
  padding: 0.5rem 0 0.2rem;
  margin-bottom: 0.1rem;
}

/* ── Stat card ──────────────────────────────────────── */
.fm-stat {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 1rem 1.1rem;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  transition: transform .18s, box-shadow .18s, border-color .18s;
}
.fm-stat:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(0,0,0,0.08);
  border-color: #BFDBFE;
}
.fm-stat .icon  { font-size: 1.6rem; margin-bottom: 0.25rem; }
.fm-stat .value { font-size: 1.8rem; font-weight: 800; line-height: 1; }
.fm-stat .label {
  font-size: 0.67rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.06em; color: #6B7280; margin-top: 0.25rem;
}

/* ── Member card ────────────────────────────────────── */
.fm-member-card {
  border-radius: 14px;
  padding: 1.1rem 1.2rem;
  margin-bottom: 0.6rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  transition: transform .18s, box-shadow .18s;
}
.fm-member-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.10);
}
.fm-member-avatar {
  width: 46px; height: 46px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.35rem;
  margin-bottom: 0.45rem;
  box-shadow: 0 3px 8px rgba(0,0,0,0.12);
}
.fm-member-name   { font-size: 0.97rem; font-weight: 700; color: #111827; }
.fm-member-rel    { font-size: 0.74rem; font-weight: 600; color: #6B7280; }
.fm-member-detail { font-size: 0.79rem; color: #374151; line-height: 1.8; }

/* ── Info row ───────────────────────────────────────── */
.fm-info-row {
  display: flex; gap: 0.4rem; align-items: center;
  font-size: 0.82rem; color: #374151; margin: 0.15rem 0;
}
.fm-info-row b { color: #111827; }

/* ── Pill badge ─────────────────────────────────────── */
.fm-pill {
  display: inline-block;
  padding: 0.18rem 0.65rem;
  border-radius: 99px;
  font-size: 0.67rem;
  font-weight: 700;
  letter-spacing: 0.04em;
}

/* ── Empty state ────────────────────────────────────── */
.fm-empty {
  text-align: center;
  padding: 2.75rem 1rem;
}
.fm-empty .icon { font-size: 2.75rem; display: block; margin-bottom: 0.5rem; opacity: 0.45; }
.fm-empty h3    { color: #9CA3AF; margin: 0 0 0.25rem; font-size: 0.95rem; font-weight: 600; }
.fm-empty p     { font-size: 0.8rem; margin: 0; color: #D1D5DB; font-style: italic; }

/* ── Timeline item ──────────────────────────────────── */
.fm-timeline-item {
  border-left: 2px solid #BFDBFE;
  padding: 0.45rem 0 0.45rem 1rem;
  margin-bottom: 0.5rem;
  position: relative;
}
.fm-timeline-item::before {
  content: '';
  width: 8px; height: 8px;
  background: #2563EB;
  border-radius: 50%;
  position: absolute;
  left: -5px; top: 0.65rem;
}

/* ── AI response box ────────────────────────────────── */
.fm-ai-box {
  background: #EFF6FF;
  border: 1px solid #BFDBFE;
  border-radius: 12px;
  padding: 1.1rem 1.3rem;
  margin-top: 0.75rem;
  font-size: 0.88rem;
  line-height: 1.75;
  color: #1E40AF;
}
.fm-ai-box strong { color: #1E3A8A; }

/* ── Vital gauge ────────────────────────────────────── */
.fm-vital-box {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 10px;
  padding: 0.8rem 0.95rem;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.fm-vital-label { font-size: 0.63rem; font-weight: 700; text-transform: uppercase;
                   letter-spacing: 0.08em; color: #6B7280; }
.fm-vital-value { font-size: 1.4rem; font-weight: 800; line-height: 1.1; }
.fm-vital-unit  { font-size: 0.65rem; color: #9CA3AF; }
</style>
"""


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — nested navigation
# ══════════════════════════════════════════════════════════════════════════════

_SECTIONS = {
    "📋 Family Dashboard": ["🏠 Overview", "📊 Statistics"],
    "👥 Family Members":   ["➕ Add Member", "👁️ View Members", "✏️ Edit Member"],
    "📅 Appointments":     ["🗓️ Book Appointment", "⏰ Upcoming", "📜 History"],
    "💊 Medicines":        ["💊 Reminders", "📆 Schedule", "⚠️ Missed Medicines"],
    "📄 Medical Reports":  ["📤 Upload Report", "📂 View Reports",
                            "🤖 AI Analysis", "🔍 Compare Reports"],
    "❤️ Health Monitoring":["🕒 Health Timeline", "🏅 Health Score", "📈 Vital Records"],
    "🚑 Emergency":        ["📞 Emergency Contacts", "🏥 Medical Info",
                            "🗺️ Nearby Hospitals"],
    "🤖 AI Assistant":     ["📝 Health Summary", "💡 Recommendations",
                            "💬 Ask AI"],
    "⚙️ Settings":         ["🎛️ Preferences", "🔔 Notifications"],
}


def _render_fm_sidebar() -> tuple[str, str]:
    """Render the Family Management nested sidebar, return (section, subsection)."""

    st.sidebar.markdown(
        '<div class="fm-section-title">📋 Navigate</div>',
        unsafe_allow_html=True,
    )

    if "fm_section" not in st.session_state:
        st.session_state.fm_section = "📋 Family Dashboard"
    if "fm_sub" not in st.session_state:
        st.session_state.fm_sub = "🏠 Overview"

    for section, subs in _SECTIONS.items():
        is_active = st.session_state.fm_section == section
        icon_style = "color:#60A5FA;font-weight:800;" if is_active else "color:#6B7280;font-weight:700;"
        st.sidebar.markdown(
            f'<div style="font-size:0.72rem;{icon_style} text-transform:uppercase;'
            f'letter-spacing:0.08em;padding:0.45rem 0.1rem 0.1rem;">{section}</div>',
            unsafe_allow_html=True,
        )
        for sub in subs:
            key = f"fm_nav_{section}_{sub}".replace(" ", "_")
            is_sub_active = is_active and st.session_state.fm_sub == sub
            btn_style = (
                "background:rgba(59,130,246,0.15);color:#60A5FA;"
                "border-left:3px solid #3B82F6;font-weight:700;"
            ) if is_sub_active else (
                "background:transparent;color:#6B7280;"
                "border-left:3px solid transparent;font-weight:500;"
            )
            if st.sidebar.button(
                sub, key=key,
                use_container_width=True,
            ):
                st.session_state.fm_section = section
                st.session_state.fm_sub = sub
                st.rerun()

    return st.session_state.fm_section, st.session_state.fm_sub


# ══════════════════════════════════════════════════════════════════════════════
# HELPER — current user id (None for guests)
# ══════════════════════════════════════════════════════════════════════════════

def _uid() -> Optional[int]:
    user = st.session_state.get("user")
    return user.get("id") if isinstance(user, dict) else None


def _member_selector(label: str = "Select Family Member",
                     key: str = "fm_sel_member") -> Optional[Dict]:
    """Dropdown of active members; returns the selected member dict or None."""
    members = fdb.get_family_members(user_id=_uid())
    if not members:
        st.info("No family members added yet. Go to 👥 Family Members → ➕ Add Member first.")
        return None
    names = [f"{fu.member_emoji(m['relationship'])} {m['full_name']} ({m['relationship']})"
             for m in members]
    idx = st.selectbox(label, range(len(names)), format_func=lambda i: names[i], key=key)
    return members[idx]


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — FAMILY DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def _render_empty_state_form() -> None:
    st.markdown("""
    <div class="fm-empty">
      <span class="icon">👨‍👩‍👧‍👦</span>
      <h3>No family members found.</h3>
      <p style="font-size:1.1rem; color:#6B7280; font-style:normal;">Please add your first family member.</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("fm_add_first_member_form", clear_on_submit=True):
        st.markdown("#### 👤 Personal Information")
        c1, c2, c3 = st.columns(3)
        with c1:
            full_name = st.text_input("Full Name *", placeholder="Jane Doe")
        with c2:
            relationship = st.selectbox("Relationship to Patient *", fu.RELATIONSHIP_OPTIONS)
        with c3:
            dob = st.date_input("Date of Birth *", min_value=date(1900, 1, 1), max_value=date.today())
            
        c4, c5, c6 = st.columns(3)
        with c4:
            gender = st.selectbox("Gender *", [""] + fu.GENDER_OPTIONS)
        with c5:
            blood_group = st.selectbox("Blood Group", [""] + fu.BLOOD_GROUPS)
        with c6:
            photo_emoji = st.selectbox("Photo Upload (Avatar)", ["👤","👨","👩","👦","👧","👴","👵","👶","🧑","💑"])

        st.markdown("---")
        st.markdown("#### 📞 Contact Information")
        c7, c8 = st.columns(2)
        with c7:
            phone = st.text_input("Mobile Number *", placeholder="+91 9876543210")
            email = st.text_input("Email", placeholder="jane@example.com")
        with c8:
            alt_phone = st.text_input("Alternative Mobile Number")
            address = st.text_area("Address", height=68)

        st.markdown("---")
        st.markdown("#### 🚑 Emergency Details")
        c9, c10, c11 = st.columns(3)
        with c9:
            em_name = st.text_input("Emergency Contact Name")
        with c10:
            em_phone = st.text_input("Emergency Contact Number")
        with c11:
            em_rel = st.text_input("Emergency Contact Relationship")

        st.markdown("---")
        st.markdown("#### 🏥 Medical Information")
        c12, c13 = st.columns(2)
        with c12:
            conditions = st.text_area("Existing Diseases", height=68)
            current_meds = st.text_area("Current Medications", height=68)
            disability = st.selectbox("Disability", ["No", "Yes"])
        with c13:
            allergies = st.text_area("Allergies", height=68)
            medical_hist = st.text_area("Medical History", height=68)
            c14, c15 = st.columns(2)
            with c14:
                insurance_prov = st.text_input("Health Insurance Provider")
            with c15:
                insurance_num = st.text_input("Insurance Number")

        st.markdown("---")
        st.markdown("#### ❤️ Health Details")
        c16, c17, c18, c19 = st.columns(4)
        with c16:
            height = st.number_input("Height (cm)", min_value=0.0, step=1.0)
        with c17:
            weight = st.number_input("Weight (kg)", min_value=0.0, step=0.1)
        with c18:
            smoking = st.selectbox("Smoking", ["No", "Yes"])
        with c19:
            alcohol = st.selectbox("Alcohol", ["No", "Yes"])

        st.markdown("---")
        st.markdown("#### 🔔 Notification Preferences")
        c20, c21, c22 = st.columns(3)
        with c20:
            not_appt = st.checkbox("Receive Appointment Reminders", value=True)
        with c21:
            not_meds = st.checkbox("Receive Medicine Reminders", value=True)
        with c22:
            not_alerts = st.checkbox("Receive Health Alerts", value=True)

        st.markdown("---")
        c23, c24 = st.columns([1, 1])
        with c23:
            submitted = st.form_submit_button("✅ Save Family Member", type="primary", use_container_width=True)
        with c24:
            st.form_submit_button("🧹 Clear Form", type="secondary", use_container_width=True)

    if submitted:
        ok, err = fu.validate_member_name(full_name)
        if not ok: st.error(err); return
        ok_p, err_p = fu.validate_phone(phone)
        if not ok_p: st.error(err_p); return
        if not relationship: st.error("Relationship is required."); return
        if not gender: st.error("Gender is required."); return
        if dob is None: st.error("Date of Birth is required."); return

        dob_str = dob.strftime("%Y-%m-%d")
        age_val = fu.age_from_dob(dob_str)
        bmi_val = 0.0
        if height > 0:
            bmi_val = weight / ((height / 100) ** 2)

        try:
            fdb.create_family_member(
                full_name=full_name.strip(), relationship=relationship,
                date_of_birth=dob_str, age=age_val, gender=gender, blood_group=blood_group,
                phone=phone.strip(), email=email.strip(), address=address.strip(),
                medical_conditions=conditions.strip(), allergies=allergies.strip(),
                emergency_contact=f"{em_name} ({em_phone})", photo_emoji=photo_emoji,
                user_id=_uid(), alt_phone=alt_phone.strip(),
                emergency_contact_number=em_phone.strip(), emergency_contact_relationship=em_rel.strip(),
                current_medications=current_meds.strip(), medical_history=medical_hist.strip(),
                disability=1 if disability == "Yes" else 0,
                health_insurance_provider=insurance_prov.strip(), insurance_number=insurance_num.strip(),
                height=height, weight=weight, bmi=bmi_val,
                smoking=1 if smoking == "Yes" else 0, alcohol=1 if alcohol == "Yes" else 0,
                notify_appointments=1 if not_appt else 0,
                notify_medicines=1 if not_meds else 0,
                notify_health_alerts=1 if not_alerts else 0
            )
            st.success("Family member successfully saved!")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to add member: {e}")


def _render_member_profile(member: dict) -> None:
    st.markdown(f"### Profile: {member['photo_emoji']} {member['full_name']}")
    st.button("⬅️ Back to Dashboard", key="fm_profile_back", on_click=lambda: st.session_state.pop("fm_view_member_id", None))
    
    t1, t2, t3, t4 = st.tabs(["👤 Personal Info", "🏥 Medical History", "📋 Reports & Prescriptions", "🚑 Emergency"])
    
    with t1:
        st.write(f"**Relationship:** {member['relationship']}")
        st.write(f"**Date of Birth:** {member['date_of_birth']} (Age {member['age']})")
        st.write(f"**Gender:** {member['gender']} | **Blood Group:** {member['blood_group']}")
        st.write(f"**Contact:** {member['phone']}  | {member['email']}")
        st.write(f"**Address:** {member['address']}")
        st.write(f"**Height:** {member['height']} cm | **Weight:** {member['weight']} kg")
        st.write(f"**BMI:** {round(member['bmi'], 2) if member.get('bmi') else 'N/A'}")
        
    with t2:
        st.write(f"**Existing Diseases:** {member['medical_conditions']}")
        st.write(f"**Allergies:** {member['allergies']}")
        st.write(f"**Disability:** {'Yes' if member['disability'] else 'No'}")
        st.write(f"**Smoking:** {'Yes' if member['smoking'] else 'No'} | **Alcohol:** {'Yes' if member['alcohol'] else 'No'}")
        st.write("**Vaccination History:** (Coming soon)")

    with t3:
        st.write(f"**Current Medications:** {member['current_medications']}")
        st.write("**Prescriptions:**")
        meds = fdb.get_family_medicines(member_id=member['id'])
        if meds:
            st.dataframe(pd.DataFrame(fu.medicines_to_rows(meds)), use_container_width=True, hide_index=True)
        else:
            st.info("No active prescriptions")
            
        st.write("**Reports:**")
        reps = fdb.get_family_reports(member_id=member['id'])
        if reps:
             st.dataframe(pd.DataFrame(fu.reports_to_rows(reps)), use_container_width=True, hide_index=True)
        else:
             st.info("No reports found")

    with t4:
        st.write(f"**Health Insurance Provider:** {member['health_insurance_provider']}")
        st.write(f"**Insurance Number:** {member['insurance_number']}")
        st.write(f"**Emergency Contact Name:** {member['emergency_contact']}")
        st.write(f"**Emergency Contact Number:** {member['emergency_contact_number']}")
        st.write(f"**Relationship:** {member['emergency_contact_relationship']}")


def _dash_overview() -> None:
    members = fdb.get_family_members(user_id=_uid())
    if not members:
        _render_empty_state_form()
        return

    # If "View" was clicked on the table
    if "fm_view_member_id" in st.session_state:
        target_id = st.session_state.fm_view_member_id
        selected = next((m for m in members if m["id"] == target_id), None)
        if selected:
            _render_member_profile(selected)
            return

    # Dashboard Statistics
    stats = fdb.get_family_dashboard_stats(user_id=_uid())
    cols = st.columns(3)
    
    # Calculate average health score (mock computation based on vitals or defaults)
    avg_health_score = 85 # Dummy value placeholder
    
    cards = [
        ("👨‍👩‍👧‍👦", stats["total_members"],    "Total Members",    "#3B82F6"),
        ("📅",        stats["upcoming_appts"],  "Upcoming Appts",   "#22C55E"),
        ("💊",        stats["active_medicines"],"Active Prescriptions",  "#A78BFA"),
        ("📄",        stats["total_reports"],   "Reports",          "#06B6D4"),
        ("⚠️",        stats["missed_medicines"],"Emergency Alerts", "#F59E0B"), # Maps to missed for now
        ("❤️",        f"{avg_health_score}%",   "Health Score",     "#F43F5E"),
    ]
    for i, (icon, val, label, color) in enumerate(cards):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="fm-stat">
              <div class="icon">{icon}</div>
              <div class="value" style="color:{color};">{val}</div>
              <div class="label">{label}</div>
            </div>
            """, unsafe_allow_html=True)
        if (i + 1) % 3 == 0 and i < len(cards) - 1:
            cols = st.columns(3)

    st.markdown("---")
    st.markdown("#### 👥 Family Members List")
    
    scol1, scol2, scol3, scol4 = st.columns(4)
    with scol1:
        s_query = st.text_input("🔍 Search", placeholder="Name / Phone...")
    with scol2:
        f_rel = st.selectbox("Relationship", ["All"] + fu.RELATIONSHIP_OPTIONS)
    with scol3:
        f_gen = st.selectbox("Gender", ["All"] + fu.GENDER_OPTIONS)
    with scol4:
        f_blood = st.selectbox("Blood Group", ["All"] + fu.BLOOD_GROUPS)
        
    filtered = members
    if s_query:
        s_q = s_query.lower()
        filtered = [m for m in filtered if s_q in m['full_name'].lower() or s_q in m.get('phone','').lower()]
    if f_rel != "All":
        filtered = [m for m in filtered if m['relationship'] == f_rel]
    if f_gen != "All":
        filtered = [m for m in filtered if m['gender'] == f_gen]
    if f_blood != "All":
        filtered = [m for m in filtered if m['blood_group'] == f_blood]

    if not filtered:
        st.info("No members match the current filters.")
        return

    # Render a responsive list-like table using columns
    st.markdown("""
        <div style="display:flex; font-weight:700; color:#6B7280; font-size:0.8rem; padding-bottom: 0.5rem; border-bottom: 1px solid #E5E7EB;">
            <div style="width: 5%;">#</div>
            <div style="width: 25%;">Name & Relationship</div>
            <div style="width: 10%;">Age / Gender</div>
            <div style="width: 10%;">Blood</div>
            <div style="width: 15%;">Phone</div>
            <div style="width: 15%;">Last Appt</div>
            <div style="width: 20%;">Actions</div>
        </div>
    """, unsafe_allow_html=True)
    
    for idx, m in enumerate(filtered):
        # Fetch last appointment
        appts = fdb.get_family_appointments(member_id=m["id"])
        last_appt_dt = "N/A"
        if appts:
            past_appts = [a for a in appts if a.get("status") == "completed"]
            if past_appts:
                last_appt_dt = fu.fmt_date(past_appts[-1]["appointment_date"])

        col1, col2, col3, col4, col5, col6, col7 = st.columns([0.5, 2.5, 1, 1, 1.5, 1.5, 2])
        col1.write(m.get('photo_emoji', '👤'))
        col2.write(f"**{m['full_name']}**\n\n{m['relationship']}")
        col3.write(f"{m.get('age') or '—'}\n\n{m.get('gender') or '—'}")
        col4.write(m.get('blood_group') or '—')
        col5.write(m.get('phone') or '—')
        col6.write(last_appt_dt)
        
        with col7:
            a1, a2, a3 = st.columns(3)
            with a1:
                if st.button("👁️", key=f"view_{m['id']}", help="View Profile"):
                    st.session_state.fm_view_member_id = m['id']
                    st.rerun()
            with a2:
                if st.button("✏️", key=f"edit_{m['id']}", help="Edit Member"):
                    st.session_state.fm_section = "👥 Family Members"
                    st.session_state.fm_sub = "✏️ Edit Member"
                    st.session_state.fm_edit_sel = idx # Note: this is a weak map, but helps navigate
                    st.rerun()
            with a3:
                if st.button("🗑️", key=f"del_{m['id']}", help="Delete Member"):
                    fdb.delete_family_member(m['id'])
                    st.rerun()

def _dash_statistics() -> None:
    # Retain the exact same implementation redirect for old stats, or show charts
    members = fdb.get_family_members(user_id=_uid())
    if not members:
        _render_empty_state_form()
        return

    # Relationship breakdown
    rel_counts: Dict[str, int] = {}
    for m in members:
        rel_counts[m["relationship"]] = rel_counts.get(m["relationship"], 0) + 1

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**👥 Members by Relationship**")
        for rel, cnt in sorted(rel_counts.items(), key=lambda x: -x[1]):
            pct = int(cnt / len(members) * 100)
            st.markdown(f"""
            <div style="margin-bottom:0.4rem;">
              <div style="display:flex;justify-content:space-between;font-size:0.82rem;
                          color:#374151;margin-bottom:2px;">
                <span>{fu.member_emoji(rel)} {rel}</span>
                <span>{cnt} ({pct}%)</span>
              </div>
              <div style="height:5px;background:rgba(255,255,255,0.07);border-radius:99px;">
                <div style="width:{pct}%;height:100%;background:#3B82F6;border-radius:99px;"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    with c2:
        st.markdown("**🩸 Blood Group Distribution**")
        bg_counts: Dict[str, int] = {}
        for m in members:
            bg = m.get("blood_group") or "Unknown"
            bg_counts[bg] = bg_counts.get(bg, 0) + 1
        bg_df = pd.DataFrame(
            [{"Blood Group": k, "Count": v} for k, v in bg_counts.items()]
        )
        st.dataframe(bg_df, use_container_width=True, hide_index=True)

    # Age distribution
    st.markdown("**📊 Age Summary**")
    ages = []
    for m in members:
        a = m.get("age") or fu.age_from_dob(m.get("date_of_birth", ""))
        if a:
            ages.append(a)
    if ages:
        c3, c4, c5 = st.columns(3)
        c3.metric("Youngest", f"{min(ages)} yrs")
        c4.metric("Oldest",   f"{max(ages)} yrs")
        c5.metric("Average",  f"{sum(ages)//len(ages)} yrs")
    else:
        st.caption("No age data recorded.")

    # Medicine load
    st.markdown("**💊 Medicine Load per Member**")
    rows = []
    for m in members:
        meds = fdb.get_family_medicines(member_id=m["id"])
        rows.append({"Member": m["full_name"], "Active Medicines": len(meds)})
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — FAMILY MEMBERS
# ══════════════════════════════════════════════════════════════════════════════

def _members_add() -> None:
    st.markdown("#### ➕ Add Family Member")
    with st.form("fm_add_member_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            full_name    = st.text_input("Full Name *", placeholder="e.g. Ramesh Kumar")
            relationship = st.selectbox("Relationship *", fu.RELATIONSHIP_OPTIONS)
            dob          = st.date_input("Date of Birth", value=None,
                                          min_value=date(1900, 1, 1), max_value=date.today())
            gender       = st.selectbox("Gender", [""] + fu.GENDER_OPTIONS)
        with c2:
            blood_group  = st.selectbox("Blood Group", [""] + fu.BLOOD_GROUPS)
            phone        = st.text_input("Phone", placeholder="+91 9876543210")
            email        = st.text_input("Email", placeholder="name@example.com")
            photo_emoji  = st.selectbox("Avatar Emoji",
                                         ["👤","👨","👩","👦","👧","👴","👵","👶","🧑","💑"])

        medical_conditions = st.text_area("Medical Conditions",
                                           placeholder="e.g. Diabetes Type 2, Hypertension",
                                           height=70)
        allergies          = st.text_area("Allergies",
                                           placeholder="e.g. Penicillin, Peanuts",
                                           height=60)
        address            = st.text_input("Address", placeholder="City, State")
        submitted = st.form_submit_button("➕ Add Member", type="primary",
                                           use_container_width=True)

    if submitted:
        ok, err = fu.validate_member_name(full_name)
        if not ok:
            st.error(err); return
        ok2, err2 = fu.validate_phone(phone)
        if not ok2:
            st.error(err2); return
        dob_str = dob.strftime("%Y-%m-%d") if dob else ""
        age_val = fu.age_from_dob(dob_str) if dob_str else None
        try:
            mid = fdb.create_family_member(
                full_name=full_name.strip(),
                relationship=relationship,
                date_of_birth=dob_str, age=age_val,
                gender=gender, blood_group=blood_group,
                phone=phone.strip(), email=email.strip(),
                address=address.strip(),
                medical_conditions=medical_conditions.strip(),
                allergies=allergies.strip(),
                photo_emoji=photo_emoji,
                user_id=_uid(),
            )
            st.success(f"✅ **{full_name.strip()}** added as family member! (ID: #{mid})")
        except Exception as e:
            st.error(f"Failed to add member: {e}")


def _members_view() -> None:
    st.markdown("#### 👥 All Family Members")
    members = fdb.get_family_members(user_id=_uid())
    if not members:
        st.markdown("""
        <div class="fm-empty">
          <span class="icon">👨‍👩‍👧‍👦</span>
          <h3>No members yet</h3>
          <p>Click <b>➕ Add Member</b> to get started.</p>
        </div>""", unsafe_allow_html=True)
        return

    # Search filter
    search = st.text_input("🔍 Search by name", placeholder="Type a name…",
                            key="fm_member_search")
    if search:
        members = [m for m in members
                   if search.lower() in m["full_name"].lower()]

    cols_n = 3
    for i in range(0, len(members), cols_n):
        row_members = members[i: i + cols_n]
        cols = st.columns(cols_n)
        for col, m in zip(cols, row_members):
            clr = fu.member_card_color(m["id"])
            age_disp = (m.get("age") or fu.age_from_dob(m.get("date_of_birth", "")) or "—")
            with col:
                st.markdown(f"""
                <div class="fm-member-card"
                     style="background:{clr['bg']};border:1px solid {clr['border']};">
                  <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.6rem;">
                    <div class="fm-member-avatar"
                         style="background:linear-gradient(135deg,{clr['accent']},{clr['border']});">
                      {m.get('photo_emoji','👤')}
                    </div>
                    <div>
                      <div class="fm-member-name">{m['full_name']}</div>
                      <div class="fm-member-rel">{m['relationship']}</div>
                    </div>
                  </div>
                  <div class="fm-member-detail">
                    <div>🎂 Age: <b>{age_disp}</b> &nbsp;·&nbsp; {m.get('gender','') or '—'}</div>
                    <div>🩸 {m.get('blood_group','—') or '—'}</div>
                    <div>📱 {m.get('phone','—') or '—'}</div>
                    {"<div>🏥 " + (m.get('medical_conditions') or '—')[:50] + "…</div>" if m.get('medical_conditions') else ""}
                  </div>
                  <div style="margin-top:0.5rem;">
                    <span class="fm-pill"
                          style="background:{clr['accent']}22;color:{clr['accent']};
                                 border:1px solid {clr['border']};">
                      #{m['id']}
                    </span>
                    <span style="font-size:0.68rem;color:#6B7280;margin-left:0.4rem;">
                      Added {fu.fmt_date(m['created_at'][:10])}
                    </span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

    with st.expander("📊 View as Table", expanded=False):
        st.dataframe(pd.DataFrame(fu.members_to_rows(members)),
                     use_container_width=True, hide_index=True)


def _members_edit() -> None:
    st.markdown("#### ✏️ Edit Family Member")
    member = _member_selector("Select member to edit", key="fm_edit_sel")
    if not member:
        return
    m = member
    with st.form("fm_edit_member_form"):
        c1, c2 = st.columns(2)
        with c1:
            new_name  = st.text_input("Full Name", value=m["full_name"])
            rel_idx   = fu.RELATIONSHIP_OPTIONS.index(m["relationship"]) \
                        if m["relationship"] in fu.RELATIONSHIP_OPTIONS else 0
            new_rel   = st.selectbox("Relationship", fu.RELATIONSHIP_OPTIONS, index=rel_idx)
            new_dob_v = None
            if m.get("date_of_birth"):
                try:
                    new_dob_v = datetime.strptime(m["date_of_birth"][:10], "%Y-%m-%d").date()
                except Exception:
                    pass
            new_dob   = st.date_input("Date of Birth", value=new_dob_v,
                                       min_value=date(1900, 1, 1), max_value=date.today())
            gen_idx   = (fu.GENDER_OPTIONS.index(m["gender"])
                         if m.get("gender") in fu.GENDER_OPTIONS else 0)
            new_gender = st.selectbox("Gender", fu.GENDER_OPTIONS, index=gen_idx)
        with c2:
            bg_list   = [""] + fu.BLOOD_GROUPS
            bg_idx    = bg_list.index(m["blood_group"]) if m.get("blood_group") in bg_list else 0
            new_bg    = st.selectbox("Blood Group", bg_list, index=bg_idx)
            new_phone = st.text_input("Phone", value=m.get("phone", ""))
            new_email = st.text_input("Email", value=m.get("email", ""))
            emoji_opts = ["👤","👨","👩","👦","👧","👴","👵","👶","🧑","💑"]
            em_idx    = emoji_opts.index(m.get("photo_emoji","👤")) \
                        if m.get("photo_emoji") in emoji_opts else 0
            new_emoji = st.selectbox("Avatar Emoji", emoji_opts, index=em_idx)

        new_cond    = st.text_area("Medical Conditions",
                                    value=m.get("medical_conditions",""), height=70)
        new_allergy = st.text_area("Allergies", value=m.get("allergies",""), height=60)
        new_addr    = st.text_input("Address", value=m.get("address",""))
        saved = st.form_submit_button("💾 Save Changes", type="primary",
                                       use_container_width=True)

    if saved:
        ok, err = fu.validate_member_name(new_name)
        if not ok:
            st.error(err); return
        dob_str = new_dob.strftime("%Y-%m-%d") if new_dob else ""
        age_val = fu.age_from_dob(dob_str) if dob_str else None
        try:
            fdb.update_family_member(
                member_id=m["id"],
                full_name=new_name.strip(),
                relationship=new_rel,
                date_of_birth=dob_str, age=age_val,
                gender=new_gender, blood_group=new_bg,
                phone=new_phone.strip(), email=new_email.strip(),
                address=new_addr.strip(),
                medical_conditions=new_cond.strip(),
                allergies=new_allergy.strip(),
                photo_emoji=new_emoji,
            )
            st.success(f"✅ **{new_name.strip()}** updated successfully!")
        except Exception as e:
            st.error(f"Update failed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — APPOINTMENTS
# ══════════════════════════════════════════════════════════════════════════════

def _appt_book() -> None:
    st.markdown("#### 🗓️ Book Appointment")
    member = _member_selector("Select family member", key="fm_appt_book_sel")
    if not member:
        return

    with st.form("fm_book_appt_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            doctor_name  = st.text_input("Doctor Name *", placeholder="Dr. Ramesh Patel")
            specialization = st.selectbox("Specialization", fu.SPECIALIZATIONS)
            appt_date    = st.date_input("Date *", min_value=date.today())
        with c2:
            appt_time    = st.time_input("Time *", value=datetime.strptime("09:00", "%H:%M").time())
            hospital     = st.text_input("Hospital / Clinic", placeholder="City General Hospital")
            purpose      = st.text_input("Purpose", placeholder="Annual check-up")

        notes = st.text_area("Notes", height=65, placeholder="Any special instructions…")
        submitted = st.form_submit_button("📅 Book Appointment", type="primary",
                                           use_container_width=True)

    if submitted:
        if not doctor_name.strip():
            st.error("Doctor name is required."); return
        try:
            aid = fdb.create_family_appointment(
                member_id=member["id"],
                member_name=member["full_name"],
                doctor_name=doctor_name.strip(),
                appointment_date=appt_date.strftime("%Y-%m-%d"),
                appointment_time=appt_time.strftime("%H:%M"),
                specialization=specialization,
                hospital=hospital.strip(),
                purpose=purpose.strip(),
                notes=notes.strip(),
            )
            st.success(
                f"✅ Appointment booked for **{member['full_name']}** with "
                f"**{doctor_name.strip()}** on {fu.fmt_date(appt_date.strftime('%Y-%m-%d'))} "
                f"at {fu.fmt_time(appt_time.strftime('%H:%M'))} (ID: #{aid})"
            )
        except Exception as e:
            st.error(f"Booking failed: {e}")


def _appt_upcoming() -> None:
    st.markdown("#### ⏰ Upcoming Appointments")
    days = st.slider("Show next N days", 7, 90, 30, key="fm_upcoming_days")
    upcoming = fdb.get_upcoming_appointments(days_ahead=days)

    if not upcoming:
        st.markdown("""
        <div class="fm-empty">
          <span class="icon">📅</span>
          <h3>No upcoming appointments</h3>
          <p>Book an appointment to see it here.</p>
        </div>""", unsafe_allow_html=True)
        return

    for a in upcoming:
        color = fu.status_color(a.get("status", ""))
        with st.container():
            st.markdown(f"""
            <div style="background:#FFFFFF;border:1px solid rgba(255,255,255,0.07);
                        border-radius:14px;padding:1rem 1.25rem;margin-bottom:0.6rem;">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                  <div style="color:#111827;font-weight:700;font-size:0.95rem;">
                    📅 {a['doctor_name']}
                    <span style="font-size:0.74rem;color:#6B7280;font-weight:500;
                                 margin-left:0.4rem;">({a.get('specialization','') or 'General'})</span>
                  </div>
                  <div style="color:#6B7280;font-size:0.8rem;margin-top:0.2rem;">
                    👤 {a['member_name']} &nbsp;·&nbsp; 📆 {fu.fmt_date(a['appointment_date'])}
                    &nbsp;·&nbsp; 🕐 {fu.fmt_time(a['appointment_time'])}
                  </div>
                  {f'<div style="color:#6B7280;font-size:0.76rem;">🏥 {a["hospital"]}</div>' if a.get("hospital") else ""}
                </div>
                <span class="fm-pill" style="background:{color}22;color:{color};
                      border:1px solid {color}44;">{a.get('status','').capitalize()}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 1, 4])
            with col1:
                if st.button("✅ Done", key=f"fm_appt_done_{a['id']}"):
                    fdb.update_appointment_status(a["id"], "completed")
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", key=f"fm_appt_cancel_{a['id']}"):
                    fdb.update_appointment_status(a["id"], "cancelled")
                    st.rerun()


def _appt_history() -> None:
    st.markdown("#### 📜 Appointment History")
    member = _member_selector("Filter by member (optional)", key="fm_hist_sel")
    mid = member["id"] if member else None
    all_appts = fdb.get_family_appointments(member_id=mid)

    if not all_appts:
        st.info("No appointment records found.")
        return

    status_filter = st.selectbox("Filter by status",
                                   ["All"] + fu.APPOINTMENT_STATUSES,
                                   key="fm_hist_status")
    if status_filter != "All":
        all_appts = [a for a in all_appts if a.get("status") == status_filter]

    st.dataframe(
        pd.DataFrame(fu.appointments_to_rows(all_appts)),
        use_container_width=True, hide_index=True,
    )
    st.caption(f"{len(all_appts)} record(s) shown.")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — MEDICINES
# ══════════════════════════════════════════════════════════════════════════════

def _med_reminders() -> None:
    st.markdown("#### 💊 Prescription Reminders")
    member = _member_selector(key="fm_med_sel")
    if not member:
        return

    with st.form("fm_add_med_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            med_name  = st.text_input("Medicine Name *", placeholder="Metformin 500mg")
            dosage    = st.text_input("Dosage *", placeholder="1 tablet")
            frequency = st.selectbox("Frequency", fu.FREQUENCY_OPTIONS)
        with c2:
            rem_time  = st.time_input("Reminder Time",
                                       value=datetime.strptime("08:00", "%H:%M").time())
            start_dt  = st.date_input("Start Date", value=date.today())
            end_dt    = st.date_input("End Date (optional)", value=None,
                                       min_value=date.today())
        prescribed_by = st.text_input("Prescribed By", placeholder="Dr. Sharma")
        notes = st.text_area("Notes", height=60)
        submitted = st.form_submit_button("➕ Add Reminder", type="primary",
                                           use_container_width=True)

    if submitted:
        if not med_name.strip() or not dosage.strip():
            st.error("Medicine name and dosage are required."); return
        try:
            fdb.create_family_medicine(
                member_id=member["id"],
                member_name=member["full_name"],
                medicine_name=med_name.strip(),
                dosage=dosage.strip(),
                frequency=frequency,
                reminder_time=rem_time.strftime("%H:%M"),
                start_date=start_dt.strftime("%Y-%m-%d"),
                end_date=end_dt.strftime("%Y-%m-%d") if end_dt else "",
                prescribed_by=prescribed_by.strip(),
                notes=notes.strip(),
            )
            st.success(f"✅ Reminder set for **{med_name.strip()}** — {rem_time.strftime('%H:%M')}")
        except Exception as e:
            st.error(f"Error: {e}")


def _med_schedule() -> None:
    st.markdown("#### 📆 Medicine Schedule — All Members")
    meds = fdb.get_family_medicines(active_only=True)
    if not meds:
        st.info("No active medicines. Add reminders first.")
        return

    # Group by reminder_time
    by_time: Dict[str, List] = {}
    for m in meds:
        t = m.get("reminder_time", "00:00")
        by_time.setdefault(t, []).append(m)

    for t in sorted(by_time.keys()):
        slot_meds = by_time[t]
        st.markdown(f"""
        <div style="background:#FFFFFF;border:1px solid rgba(255,255,255,0.07);
                    border-radius:12px;padding:0.85rem 1.1rem;margin-bottom:0.6rem;">
          <div style="color:#60A5FA;font-weight:700;font-size:0.88rem;margin-bottom:0.4rem;">
            🕐 {fu.fmt_time(t)}
          </div>
        """, unsafe_allow_html=True)
        for m in slot_meds:
            st.markdown(f"""
          <div style="color:#374151;font-size:0.82rem;padding:0.15rem 0;">
            💊 <b>{m['medicine_name']}</b> — {m['dosage']} — {m['member_name']}
            <span style="color:#6B7280;"> ({m['frequency']})</span>
          </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("📊 Full Schedule Table"):
        st.dataframe(pd.DataFrame(fu.medicines_to_rows(meds)),
                     use_container_width=True, hide_index=True)


def _med_missed() -> None:
    st.markdown("#### ⚠️ Missed Medicines")
    member = _member_selector(key="fm_missed_sel")
    if not member:
        return

    meds = fdb.get_family_medicines(member_id=member["id"])
    if not meds:
        st.info("No active medicines for this member."); return

    st.markdown("**Log a missed dose:**")
    with st.form("fm_missed_form", clear_on_submit=True):
        med_names = [f"{m['medicine_name']} ({m['dosage']})" for m in meds]
        sel_idx   = st.selectbox("Medicine", range(len(med_names)),
                                   format_func=lambda i: med_names[i])
        reason    = st.text_input("Reason (optional)", placeholder="Forgot, Travelling…")
        submitted = st.form_submit_button("⚠️ Log Missed Dose", type="primary",
                                           use_container_width=True)

    if submitted:
        med = meds[sel_idx]
        fdb.log_missed_medicine(med["id"], member["full_name"], reason.strip())
        st.warning(f"⚠️ Missed dose logged for **{med['medicine_name']}**.")

    st.markdown("---")
    st.markdown("**Recent Missed Doses:**")
    missed = fdb.get_missed_medicines(member_name=member["full_name"])
    if not missed:
        st.caption("No missed doses recorded.")
    else:
        for mm in missed[:10]:
            st.markdown(f"""
            <div class="fm-timeline-item">
              <div style="color:#FCD34D;font-weight:700;font-size:0.85rem;">
                ⚠️ {mm.get('medicine_name','')} — {mm.get('dosage','')}
              </div>
              <div style="color:#6B7280;font-size:0.76rem;">
                📅 {fu.fmt_date(mm['missed_date'])}
                {(" · Reason: " + mm['reason']) if mm.get('reason') else ""}
              </div>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — MEDICAL REPORTS
# ══════════════════════════════════════════════════════════════════════════════

def _report_upload() -> None:
    st.markdown("#### 📤 Upload Medical Report")
    member = _member_selector(key="fm_rep_upload_sel")
    if not member:
        return

    with st.form("fm_upload_report_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            report_type = st.selectbox("Report Type *", fu.REPORT_TYPES)
            report_date = st.date_input("Report Date", value=date.today())
            lab_name    = st.text_input("Lab / Hospital", placeholder="City Diagnostics")
        with c2:
            doctor_name = st.text_input("Doctor", placeholder="Dr. Sharma")
            is_normal   = st.selectbox("Overall Result", ["Normal", "Abnormal"])
            tags        = st.text_input("Tags (comma-separated)", placeholder="diabetes,sugar")

        uploaded = st.file_uploader("Upload PDF / Image (optional)",
                                     type=["pdf", "png", "jpg", "jpeg"])
        submitted = st.form_submit_button("📤 Save Report", type="primary",
                                           use_container_width=True)

    if submitted:
        raw_text = ""
        file_name = ""
        if uploaded:
            file_name = uploaded.name
            if uploaded.type == "application/pdf":
                try:
                    raw_text = extract_text_from_uploaded_file(uploaded)
                except Exception:
                    raw_text = ""
        try:
            rid = fdb.create_family_report(
                member_id=member["id"],
                member_name=member["full_name"],
                report_type=report_type,
                report_date=report_date.strftime("%Y-%m-%d"),
                lab_name=lab_name.strip(),
                doctor_name=doctor_name.strip(),
                file_name=file_name,
                raw_text=raw_text,
                tags=tags.strip(),
                is_normal=(is_normal == "Normal"),
            )
            st.success(
                f"✅ Report saved for **{member['full_name']}** "
                f"({report_type}, {fu.fmt_date(report_date.strftime('%Y-%m-%d'))}) — ID #{rid}"
            )
        except Exception as e:
            st.error(f"Save failed: {e}")


def _report_view() -> None:
    st.markdown("#### 📂 View Reports")
    member = _member_selector(key="fm_rep_view_sel")
    if not member:
        return
    reports = fdb.get_family_reports(member_id=member["id"])
    if not reports:
        st.info("No reports found for this member.")
        return
    for r in reports:
        is_normal = r.get("is_normal", 1)
        badge_color = "#22C55E" if is_normal else "#EF4444"
        badge_text  = "Normal"  if is_normal else "Abnormal"
        with st.expander(
            f"{'✅' if is_normal else '❌'} {r['report_type']} — "
            f"{fu.fmt_date(r['report_date'])} (#{r['id']})",
            expanded=False,
        ):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Member:** {r['member_name']}")
                st.markdown(f"**Lab:** {r.get('lab_name','—') or '—'}")
                st.markdown(f"**Doctor:** {r.get('doctor_name','—') or '—'}")
            with c2:
                st.markdown(f"""
                <span class="fm-pill"
                      style="background:{badge_color}22;color:{badge_color};
                             border:1px solid {badge_color}44;">
                  {badge_text}
                </span>
                """, unsafe_allow_html=True)
                if r.get("tags"):
                    st.markdown(f"**Tags:** {r['tags']}")
                if r.get("file_name"):
                    st.markdown(f"**File:** {r['file_name']}")
            if r.get("ai_summary"):
                st.markdown("**AI Summary:**")
                st.markdown(
                    f'<div class="fm-ai-box">{r["ai_summary"]}</div>',
                    unsafe_allow_html=True,
                )
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("🗑️ Delete", key=f"fm_del_rep_{r['id']}"):
                    fdb.delete_family_report(r["id"])
                    st.rerun()


def _report_ai_analysis() -> None:
    st.markdown("#### 🤖 AI Report Analysis")
    member = _member_selector(key="fm_rep_ai_sel")
    if not member:
        return
    reports = fdb.get_family_reports(member_id=member["id"])
    if not reports:
        st.info("No reports available. Upload a report first.")
        return

    report_labels = [
        f"{r['report_type']} — {fu.fmt_date(r['report_date'])} (#{r['id']})"
        for r in reports
    ]
    sel = st.selectbox("Choose report", range(len(reports)),
                        format_func=lambda i: report_labels[i],
                        key="fm_ai_report_sel")
    report = reports[sel]

    if not report.get("raw_text"):
        st.warning("No text content extracted from this report. "
                   "Please re-upload as a searchable PDF.")
        return

    if st.button("🤖 Analyse with AI", type="primary", key="fm_analyse_btn"):
        with st.spinner("Analysing report…"):
            system_prompt = (
                "You are a medical report analysis assistant. Analyse the provided report "
                "and return: ## Summary, ## Key Findings, ## Abnormal Values, ## Recommendations. "
                "End with a disclaimer that this is AI-generated and not a substitute for medical advice."
            )
            user_msg = (
                f"Patient: {member['full_name']}, "
                f"Age: {member.get('age') or '?'}, "
                f"Conditions: {member.get('medical_conditions','none') or 'none'}\n\n"
                f"Report Type: {report['report_type']}\n"
                f"Date: {report['report_date']}\n\n"
                f"Report Text:\n{report['raw_text'][:3000]}"
            )
            try:
                summary = simple_query(system_prompt, user_msg)
                fdb.update_report_ai_summary(report["id"], summary)
                st.markdown(
                    f'<div class="fm-ai-box">{summary}</div>',
                    unsafe_allow_html=True,
                )
                st.success("✅ Summary saved to report.")
            except Exception as e:
                st.error(f"AI analysis failed: {e}")


def _report_compare() -> None:
    st.markdown("#### 🔍 Compare Two Reports")
    member = _member_selector(key="fm_rep_cmp_sel")
    if not member:
        return
    reports = fdb.get_family_reports(member_id=member["id"])
    if len(reports) < 2:
        st.info("At least 2 reports needed for comparison.")
        return
    labels = [f"{r['report_type']} — {fu.fmt_date(r['report_date'])}" for r in reports]
    c1, c2 = st.columns(2)
    with c1:
        i1 = st.selectbox("Report A", range(len(reports)),
                            format_func=lambda i: labels[i], key="fm_cmp_a")
    with c2:
        i2 = st.selectbox("Report B", range(len(reports)),
                            format_func=lambda i: labels[i], index=1, key="fm_cmp_b")

    if st.button("🔍 Compare", type="primary", key="fm_cmp_btn"):
        ra, rb = reports[i1], reports[i2]
        if not ra.get("raw_text") or not rb.get("raw_text"):
            st.warning("Both reports need extracted text for comparison."); return
        with st.spinner("Comparing reports…"):
            system_prompt = (
                "You are a medical assistant. Compare two medical reports and provide: "
                "## Key Differences, ## Improvements (values that improved), "
                "## Concerns (values that worsened), ## Recommendations. "
                "End with: ⚠️ AI-generated — not a substitute for medical advice."
            )
            user_msg = (
                f"Patient: {member['full_name']}\n\n"
                f"--- Report A ({ra['report_type']}, {ra['report_date']}) ---\n"
                f"{ra['raw_text'][:1500]}\n\n"
                f"--- Report B ({rb['report_type']}, {rb['report_date']}) ---\n"
                f"{rb['raw_text'][:1500]}"
            )
            try:
                result = simple_query(system_prompt, user_msg)
                st.markdown(
                    f'<div class="fm-ai-box">{result}</div>',
                    unsafe_allow_html=True,
                )
            except Exception as e:
                st.error(f"Comparison failed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — HEALTH MONITORING
# ══════════════════════════════════════════════════════════════════════════════

def _health_timeline() -> None:
    st.markdown("#### 🕒 Health Timeline")
    member = _member_selector(key="fm_timeline_sel")
    if not member:
        return

    vitals  = fdb.get_vitals(member_id=member["id"], limit=20)
    appts   = fdb.get_family_appointments(member_id=member["id"])
    reports = fdb.get_family_reports(member_id=member["id"])

    events: List[Dict] = []
    for v in vitals:
        events.append({"date": v["recorded_date"], "type": "vital",
                        "icon": "❤️", "text": f"Vitals recorded",
                        "color": "#F43F5E"})
    for a in appts:
        events.append({"date": a["appointment_date"], "type": "appt",
                        "icon": "📅",
                        "text": f"Appointment: {a['doctor_name']} ({a.get('status','')})",
                        "color": fu.status_color(a.get("status",""))})
    for r in reports:
        events.append({"date": r["report_date"], "type": "report",
                        "icon": "📄", "text": f"Report: {r['report_type']}",
                        "color": "#06B6D4"})

    events.sort(key=lambda x: x["date"], reverse=True)

    if not events:
        st.markdown("""
        <div class="fm-empty">
          <span class="icon">🕒</span>
          <h3>No health events yet</h3>
          <p>Book appointments, record vitals, or upload reports.</p>
        </div>""", unsafe_allow_html=True)
        return

    for ev in events[:25]:
        st.markdown(f"""
        <div class="fm-timeline-item" style="border-left-color:{ev['color']}40;">
          <div style="color:#111827;font-size:0.86rem;font-weight:600;">
            {ev['icon']} {ev['text']}
          </div>
          <div style="color:#6B7280;font-size:0.74rem;">{fu.fmt_date(ev['date'])}</div>
        </div>
        """, unsafe_allow_html=True)


def _health_score() -> None:
    st.markdown("#### 🏅 Health Score")
    member = _member_selector(key="fm_score_sel")
    if not member:
        return

    vitals  = fdb.get_vitals(member_id=member["id"], limit=1)
    meds    = fdb.get_family_medicines(member_id=member["id"])
    reports = fdb.get_family_reports(member_id=member["id"])
    missed  = fdb.get_missed_medicines(member_name=member["full_name"])
    appts   = fdb.get_family_appointments(member_id=member["id"])
    completed = [a for a in appts if a.get("status") == "completed"]

    # Simple scoring
    score = 50
    if vitals:       score += 15
    if meds:         score += 10
    if reports:      score += 10
    if completed:    score += 10
    score -= min(len(missed) * 3, 25)
    score = max(0, min(score, 100))

    label, color, emoji = fu.health_grade(score)

    latest = fdb.get_latest_health_score(member["id"])
    delta  = (score - latest["score"]) if latest else 0

    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown(f"""
        <div style="background:#FFFFFF;border:2px solid {color}44;border-radius:20px;
                    padding:2rem;text-align:center;">
          <div style="font-size:3rem;">{emoji}</div>
          <div style="font-size:3.5rem;font-weight:900;color:{color};line-height:1;">
            {score}
          </div>
          <div style="font-size:1rem;font-weight:700;color:{color};">{label}</div>
          <div style="font-size:0.75rem;color:#6B7280;margin-top:0.4rem;">
            out of 100
          </div>
          {"<div style='color:#22C55E;font-size:0.8rem;margin-top:0.3rem;'>▲ +" + str(delta) + " since last check</div>" if delta > 0 else ""}
          {"<div style='color:#EF4444;font-size:0.8rem;margin-top:0.3rem;'>▼ " + str(delta) + " since last check</div>" if delta < 0 else ""}
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("**Score Breakdown:**")
        factors = [
            ("❤️ Recent vitals recorded",    15 if vitals else 0,    15),
            ("💊 Active medicines tracked",   10 if meds else 0,     10),
            ("📄 Reports uploaded",           10 if reports else 0,  10),
            ("📅 Appointments completed",     10 if completed else 0,10),
            ("⚠️ Missed medicines (penalty)", -min(len(missed)*3,25), 0),
            ("📌 Base score",                 50,                    50),
        ]
        for label_f, pts, _max in factors:
            color_f = "#22C55E" if pts > 0 else ("#EF4444" if pts < 0 else "#6B7280")
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                        font-size:0.82rem;color:#374151;padding:0.2rem 0;">
              <span>{label_f}</span>
              <span style="color:{color_f};font-weight:700;">
                {"+" if pts > 0 else ""}{pts}
              </span>
            </div>
            """, unsafe_allow_html=True)

    if st.button("💾 Save Score", key="fm_save_score"):
        fdb.save_health_score(member["id"], member["full_name"], score, label)
        st.success(f"✅ Health score of **{score}** ({label}) saved!")


def _health_vitals() -> None:
    st.markdown("#### 📈 Vital Records")
    member = _member_selector(key="fm_vitals_sel")
    if not member:
        return

    with st.expander("➕ Record New Vitals", expanded=False):
        with st.form("fm_vitals_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                rec_date   = st.date_input("Date", value=date.today())
                rec_time   = st.time_input("Time")
                bp_sys     = st.number_input("BP Systolic (mmHg)", 0, 250, value=None)
                bp_dia     = st.number_input("BP Diastolic (mmHg)", 0, 150, value=None)
            with c2:
                heart_rate = st.number_input("Heart Rate (bpm)", 0, 250, value=None)
                temp       = st.number_input("Temperature (°C)", 30.0, 45.0,
                                              value=None, step=0.1)
                spo2       = st.number_input("SpO2 (%)", 0, 100, value=None)
            with c3:
                weight     = st.number_input("Weight (kg)", 0.0, 300.0,
                                              value=None, step=0.1)
                height     = st.number_input("Height (cm)", 0.0, 250.0,
                                              value=None, step=0.1)
                glucose    = st.number_input("Blood Glucose (mg/dL)", 0, 600, value=None)
            notes = st.text_input("Notes")
            submitted = st.form_submit_button("📊 Record Vitals", type="primary",
                                               use_container_width=True)

        if submitted:
            try:
                fdb.record_vitals(
                    member_id=member["id"],
                    member_name=member["full_name"],
                    recorded_date=rec_date.strftime("%Y-%m-%d"),
                    recorded_time=rec_time.strftime("%H:%M"),
                    bp_systolic=int(bp_sys) if bp_sys else None,
                    bp_diastolic=int(bp_dia) if bp_dia else None,
                    heart_rate=int(heart_rate) if heart_rate else None,
                    temperature=float(temp) if temp else None,
                    weight_kg=float(weight) if weight else None,
                    height_cm=float(height) if height else None,
                    spo2=int(spo2) if spo2 else None,
                    blood_glucose=int(glucose) if glucose else None,
                    notes=notes.strip(),
                )
                st.success("✅ Vitals recorded!")
            except Exception as e:
                st.error(f"Error: {e}")

    # Latest vitals display
    vitals = fdb.get_vitals(member_id=member["id"], limit=1)
    if vitals:
        v = vitals[0]
        st.markdown(f"**Latest reading — {fu.fmt_date(v['recorded_date'])} {v['recorded_time']}**")
        vc1, vc2, vc3, vc4 = st.columns(4)
        bp_disp = (f"{v['bp_systolic']}/{v['bp_diastolic']}" if v.get("bp_systolic") else "—")
        bp_cat, bp_col = fu.bp_category(
            v.get("bp_systolic", 0) or 0, v.get("bp_diastolic", 0) or 0
        ) if v.get("bp_systolic") else ("—", "#6B7280")

        for col, icon, val, label, color in [
            (vc1, "🩺", bp_disp,                   "Blood Pressure", bp_col),
            (vc2, "💓", f"{v.get('heart_rate','—')} bpm", "Heart Rate", "#F43F5E"),
            (vc3, "🌡️", f"{v.get('temperature','—')} °C", "Temperature", "#F59E0B"),
            (vc4, "💧", f"{v.get('spo2','—')} %",   "SpO2",         "#3B82F6"),
        ]:
            with col:
                st.markdown(f"""
                <div class="fm-vital-box">
                  <div class="fm-vital-label">{icon} {label}</div>
                  <div class="fm-vital-value" style="color:{color};">{val}</div>
                </div>
                """, unsafe_allow_html=True)

        if v.get("weight_kg") and v.get("height_cm"):
            bmi_val, bmi_cat, bmi_col = fu.bmi_category(v["weight_kg"], v["height_cm"])
            st.markdown(f"""
            <div style="margin-top:0.75rem;background:#FFFFFF;border:1px solid rgba(255,255,255,0.07);
                        border-radius:12px;padding:0.85rem 1rem;display:inline-block;">
              <span style="color:#6B7280;font-size:0.78rem;">BMI: </span>
              <span style="color:{bmi_col};font-weight:800;font-size:1.1rem;">{bmi_val}</span>
              <span style="color:{bmi_col};font-size:0.8rem;margin-left:0.3rem;">({bmi_cat})</span>
            </div>
            """, unsafe_allow_html=True)

    # History table
    all_vitals = fdb.get_vitals(member_id=member["id"])
    if all_vitals:
        st.markdown("---")
        st.markdown("**Vitals History**")
        st.dataframe(pd.DataFrame(fu.vitals_to_rows(all_vitals)),
                     use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — EMERGENCY
# ══════════════════════════════════════════════════════════════════════════════

def _emergency_contacts() -> None:
    st.markdown("#### 📞 Emergency Contacts")
    member = _member_selector(key="fm_ec_sel")
    if not member:
        return

    with st.expander("➕ Add Emergency Contact", expanded=False):
        with st.form("fm_ec_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                ec_name  = st.text_input("Contact Name *")
                ec_rel   = st.selectbox("Relationship", fu.RELATIONSHIP_OPTIONS)
                ec_phone = st.text_input("Phone *")
            with c2:
                ec_alt   = st.text_input("Alt Phone")
                ec_email = st.text_input("Email")
                priority = st.selectbox("Priority", [1, 2, 3],
                                         format_func=lambda p: fu.PRIORITY_LABELS[p])
            ec_notes = st.text_input("Notes")
            submitted = st.form_submit_button("➕ Add Contact", type="primary",
                                               use_container_width=True)

        if submitted:
            if not ec_name.strip() or not ec_phone.strip():
                st.error("Contact name and phone are required."); return
            try:
                fdb.create_emergency_contact(
                    member_id=member["id"],
                    member_name=member["full_name"],
                    contact_name=ec_name.strip(),
                    relationship=ec_rel,
                    phone=ec_phone.strip(),
                    alt_phone=ec_alt.strip(),
                    email=ec_email.strip(),
                    priority=priority,
                    notes=ec_notes.strip(),
                )
                st.success(f"✅ Emergency contact **{ec_name.strip()}** added!")
            except Exception as e:
                st.error(f"Error: {e}")

    contacts = fdb.get_emergency_contacts(member_id=member["id"])
    if not contacts:
        st.info("No emergency contacts added for this member.")
        return

    for ec in contacts:
        p_label = fu.PRIORITY_LABELS.get(ec.get("priority", 1), "")
        st.markdown(f"""
        <div style="background:#FFFFFF;border:1px solid rgba(255,255,255,0.07);
                    border-radius:14px;padding:1rem 1.25rem;margin-bottom:0.5rem;">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <div style="color:#111827;font-weight:700;">
              📞 {ec['contact_name']}
              <span style="color:#6B7280;font-weight:400;font-size:0.8rem;">
                ({ec['relationship']})
              </span>
            </div>
            <span class="fm-pill"
                  style="background:rgba(59,130,246,0.15);color:#60A5FA;
                         border:1px solid rgba(59,130,246,0.3);">{p_label}</span>
          </div>
          <div style="color:#374151;font-size:0.82rem;margin-top:0.4rem;line-height:1.9;">
            📱 {ec['phone']}
            {f" &nbsp;·&nbsp; 📲 {ec['alt_phone']}" if ec.get('alt_phone') else ""}
            {f" &nbsp;·&nbsp; 📧 {ec['email']}" if ec.get('email') else ""}
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"🗑️ Remove #{ec['id']}", key=f"fm_del_ec_{ec['id']}"):
            fdb.delete_emergency_contact(ec["id"])
            st.rerun()


def _emergency_medical_info() -> None:
    st.markdown("#### 🏥 Medical Information Card")
    member = _member_selector(key="fm_medinfo_sel")
    if not member:
        return

    clr = fu.member_card_color(member["id"])
    age_disp = member.get("age") or fu.age_from_dob(member.get("date_of_birth", "")) or "—"
    meds  = fdb.get_family_medicines(member_id=member["id"])
    med_list = ", ".join(m["medicine_name"] for m in meds) if meds else "None"

    st.markdown(f"""
    <div style="background:{clr['bg']};border:2px solid {clr['border']};
                border-radius:20px;padding:1.5rem 2rem;max-width:500px;">
      <div style="color:{clr['accent']};font-size:0.65rem;font-weight:800;
                  text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.8rem;">
        🆘 Medical Information Card
      </div>
      <div style="font-size:1.3rem;font-weight:800;color:#111827;margin-bottom:0.15rem;">
        {member.get('photo_emoji','👤')} {member['full_name']}
      </div>
      <div style="color:#6B7280;font-size:0.82rem;margin-bottom:1rem;">
        {member['relationship']} · Age: {age_disp} · {member.get('gender','') or '—'}
      </div>
      <div style="color:#374151;font-size:0.84rem;line-height:2;">
        <div>🩸 <b>Blood Group:</b> {member.get('blood_group','—') or '—'}</div>
        <div>🏥 <b>Conditions:</b> {member.get('medical_conditions','None') or 'None'}</div>
        <div>⚠️ <b>Allergies:</b> {member.get('allergies','None') or 'None'}</div>
        <div>💊 <b>Medicines:</b> {med_list}</div>
        <div>📞 <b>Emergency:</b> {member.get('emergency_contact','—') or '—'}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def _emergency_nearby() -> None:
    st.markdown("#### 🗺️ Nearby Hospitals")
    st.markdown("""
    <div style="background:#FFFFFF;border:1px solid rgba(255,255,255,0.07);
                border-radius:14px;padding:1.5rem;margin-bottom:1rem;">
      <div style="color:#60A5FA;font-size:1rem;font-weight:700;margin-bottom:0.6rem;">
        🏥 How to find nearby hospitals
      </div>
      <div style="color:#374151;font-size:0.86rem;line-height:2;">
        <div>📍 <b>Google Maps:</b> Search "hospitals near me"</div>
        <div>📞 <b>Emergency (India):</b> 112 (All), 102 (Ambulance), 108 (Medical)</div>
        <div>🚑 <b>Ambulance:</b> 1066</div>
        <div>❤️ <b>Cardiac Emergency:</b> Contact nearest cardiac centre</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Quick Emergency Numbers:**")
    cols = st.columns(3)
    numbers = [
        ("🚨", "National Emergency", "112"),
        ("🚑", "Ambulance",          "102 / 108"),
        ("🏥", "Medical Helpline",    "1066"),
        ("🔥", "Fire",               "101"),
        ("👮", "Police",              "100"),
        ("👩‍⚕️", "Women Helpline",    "1091"),
    ]
    for i, (icon, label, num) in enumerate(numbers):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="fm-stat" style="margin-bottom:0.6rem;">
              <div class="icon">{icon}</div>
              <div class="value" style="color:#EF4444;font-size:1.4rem;">{num}</div>
              <div class="label">{label}</div>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — AI ASSISTANT
# ══════════════════════════════════════════════════════════════════════════════

def _ai_summary() -> None:
    st.markdown("#### 📝 AI Health Summary")
    member = _member_selector(key="fm_ai_sum_sel")
    if not member:
        return

    if st.button("🤖 Generate Health Summary", type="primary", key="fm_ai_sum_btn"):
        vitals  = fdb.get_vitals(member_id=member["id"], limit=3)
        meds    = fdb.get_family_medicines(member_id=member["id"])
        reports = fdb.get_family_reports(member_id=member["id"])

        with st.spinner("Generating summary…"):
            system_prompt = "You are an empathetic AI health assistant providing family health summaries."
            user_msg = fu.build_health_summary_prompt(member, vitals, meds, reports)
            try:
                result = simple_query(system_prompt, user_msg)
                st.markdown(
                    f'<div class="fm-ai-box">{result}</div>',
                    unsafe_allow_html=True,
                )
            except Exception as e:
                st.error(f"AI error: {e}")


def _ai_recommendations() -> None:
    st.markdown("#### 💡 Family Health Recommendations")
    members = fdb.get_family_members(user_id=_uid())
    if not members:
        st.info("Add family members first to get recommendations.")
        return

    if st.button("💡 Get Recommendations for Entire Family",
                 type="primary", key="fm_ai_rec_btn"):
        with st.spinner("Generating recommendations…"):
            system_prompt = "You are a family health advisor providing personalised health recommendations."
            user_msg = fu.build_recommendations_prompt(members)
            try:
                result = simple_query(system_prompt, user_msg)
                st.markdown(
                    f'<div class="fm-ai-box">{result}</div>',
                    unsafe_allow_html=True,
                )
            except Exception as e:
                st.error(f"AI error: {e}")


def _ai_ask() -> None:
    st.markdown("#### 💬 Ask AI About a Family Member")
    member = _member_selector(key="fm_ai_ask_sel")
    if not member:
        return

    # Conversation history per member
    hist_key = f"fm_ai_hist_{member['id']}"
    if hist_key not in st.session_state:
        st.session_state[hist_key] = []

    # Display history
    for msg in st.session_state[hist_key]:
        row_cls = "user" if msg["role"] == "user" else "assistant"
        bubble_style = (
            "background:linear-gradient(135deg,#3B82F6,#2563EB);color:#FFF;"
            "border-bottom-right-radius:4px;"
            if msg["role"] == "user"
            else "background:#FFFFFF;color:#E2E8F0;border:1px solid rgba(255,255,255,0.07);"
                 "border-bottom-left-radius:4px;"
        )
        align = "flex-end" if msg["role"] == "user" else "flex-start"
        st.markdown(f"""
        <div style="display:flex;justify-content:{align};margin-bottom:0.6rem;">
          <div style="{bubble_style}border-radius:16px;padding:0.75rem 1rem;
                      max-width:78%;font-size:0.88rem;line-height:1.65;">
            {msg['content']}
          </div>
        </div>
        """, unsafe_allow_html=True)

    # Input
    question = st.chat_input(
        placeholder=f"Ask about {member['full_name']}'s health…",
        key=f"fm_ask_input_{member['id']}",
    )
    if question:
        st.session_state[hist_key].append({"role": "user", "content": question})
        meds    = fdb.get_family_medicines(member_id=member["id"])
        context = {"medicines": meds}
        with st.spinner("Thinking…"):
            try:
                system_prompt = "You are a knowledgeable and caring AI health assistant."
                user_msg = fu.build_ask_ai_prompt(member, question, context)
                answer = simple_query(system_prompt, user_msg)
                st.session_state[hist_key].append(
                    {"role": "assistant", "content": answer}
                )
            except Exception as e:
                st.session_state[hist_key].append(
                    {"role": "assistant",
                     "content": f"❌ AI error: {e}. Please try again."}
                )
        st.rerun()

    if st.session_state[hist_key]:
        if st.button("🗑️ Clear Chat", key=f"fm_clear_chat_{member['id']}"):
            st.session_state[hist_key] = []
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 9 — SETTINGS
# ══════════════════════════════════════════════════════════════════════════════

def _settings_preferences() -> None:
    st.markdown("#### 🎛️ Family Preferences")
    uid = _uid() or 0
    prefs = fdb.get_family_preferences(uid)

    with st.form("fm_prefs_form"):
        fam_name = st.text_input("Family Name", value=prefs.get("family_name", "My Family"))
        c1, c2   = st.columns(2)
        with c1:
            notify_email = st.checkbox("Email Notifications",
                                        value=bool(prefs.get("notify_email", 1)))
        with c2:
            notify_sms   = st.checkbox("SMS Notifications",
                                        value=bool(prefs.get("notify_sms", 0)))
        advance = st.slider("Remind me this many minutes before appointment",
                             5, 120, prefs.get("reminder_advance_mins", 30), step=5)
        saved = st.form_submit_button("💾 Save Preferences", type="primary",
                                       use_container_width=True)

    if saved:
        try:
            fdb.save_family_preferences(uid, fam_name.strip(), notify_email,
                                         notify_sms, advance)
            st.success("✅ Preferences saved!")
        except Exception as e:
            st.error(f"Error: {e}")


def _settings_notifications() -> None:
    st.markdown("#### 🔔 Notification Settings")
    st.markdown("""
    <div style="background:#FFFFFF;border:1px solid rgba(255,255,255,0.07);
                border-radius:14px;padding:1.25rem 1.5rem;">
      <div style="color:#111827;font-weight:700;margin-bottom:0.75rem;">
        🔔 Notification Channels
      </div>
      <div style="color:#374151;font-size:0.86rem;line-height:2.2;">
        <div>📧 <b>Email:</b> Configure SMTP in your .env file (SMTP_HOST, SMTP_USER, SMTP_PASS)</div>
        <div>📱 <b>SMS:</b> Integrate Twilio / AWS SNS for SMS alerts</div>
        <div>🔔 <b>In-App:</b> Always enabled — reminders shown in Medicine Schedule</div>
        <div>💊 <b>Medicine Reminders:</b> Triggered at your set reminder time</div>
        <div>📅 <b>Appointment Reminders:</b> Triggered 30 mins before (configurable)</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Upcoming Reminders Preview:**")
    meds = fdb.get_family_medicines(active_only=True)
    if meds:
        for m in meds[:5]:
            st.markdown(f"""
            <div class="fm-timeline-item">
              <div style="color:#111827;font-size:0.84rem;font-weight:600;">
                💊 {m['medicine_name']} — {m['dosage']}
              </div>
              <div style="color:#6B7280;font-size:0.76rem;">
                {m['member_name']} · {fu.fmt_time(m['reminder_time'])} · {m['frequency']}
              </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("No active medicines to remind about.")


# ══════════════════════════════════════════════════════════════════════════════
# DISPATCHER — maps (section, sub) → render function
# ══════════════════════════════════════════════════════════════════════════════

_DISPATCH = {
    ("📋 Family Dashboard",  "🏠 Overview"):           _dash_overview,
    ("📋 Family Dashboard",  "📊 Statistics"):          _dash_statistics,
    ("👥 Family Members",    "➕ Add Member"):           _members_add,
    ("👥 Family Members",    "👁️ View Members"):        _members_view,
    ("👥 Family Members",    "✏️ Edit Member"):          _members_edit,
    ("📅 Appointments",      "🗓️ Book Appointment"):    _appt_book,
    ("📅 Appointments",      "⏰ Upcoming"):              _appt_upcoming,
    ("📅 Appointments",      "📜 History"):              _appt_history,
    ("💊 Medicines",         "💊 Reminders"):            _med_reminders,
    ("💊 Medicines",         "📆 Schedule"):             _med_schedule,
    ("💊 Medicines",         "⚠️ Missed Medicines"):     _med_missed,
    ("📄 Medical Reports",   "📤 Upload Report"):        _report_upload,
    ("📄 Medical Reports",   "📂 View Reports"):         _report_view,
    ("📄 Medical Reports",   "🤖 AI Analysis"):          _report_ai_analysis,
    ("📄 Medical Reports",   "🔍 Compare Reports"):      _report_compare,
    ("❤️ Health Monitoring", "🕒 Health Timeline"):      _health_timeline,
    ("❤️ Health Monitoring", "🏅 Health Score"):         _health_score,
    ("❤️ Health Monitoring", "📈 Vital Records"):        _health_vitals,
    ("🚑 Emergency",         "📞 Emergency Contacts"):   _emergency_contacts,
    ("🚑 Emergency",         "🏥 Medical Info"):         _emergency_medical_info,
    ("🚑 Emergency",         "🗺️ Nearby Hospitals"):    _emergency_nearby,
    ("🤖 AI Assistant",      "📝 Health Summary"):       _ai_summary,
    ("🤖 AI Assistant",      "💡 Recommendations"):      _ai_recommendations,
    ("🤖 AI Assistant",      "💬 Ask AI"):               _ai_ask,
    ("⚙️ Settings",          "🎛️ Preferences"):          _settings_preferences,
    ("⚙️ Settings",          "🔔 Notifications"):        _settings_notifications,
}


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def render() -> None:
    """Called by the router when '👨‍👩‍👧‍👦 Family Management' is selected."""

    # Inject CSS once
    if "fm_css_injected" not in st.session_state:
        st.markdown(_FM_CSS, unsafe_allow_html=True)
        st.session_state.fm_css_injected = True

    # Page header
    prefs = fdb.get_family_preferences(_uid() or 0)
    fam_name = prefs.get("family_name", "My Family")
    member_count = fdb.count_family_members(user_id=_uid())

    st.markdown(f"""
    <div class="fm-header">
      <div style="display:flex;align-items:center;gap:1rem;">
        <span style="font-size:2.4rem;">👨‍👩‍👧‍👦</span>
        <div>
          <h1>{fam_name} — Family Management</h1>
          <p>Manage health records, appointments, medicines and more
             for all {member_count} family member(s).</p>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Nested sidebar
    with st.sidebar:
        st.divider()
        section, sub = _render_fm_sidebar()

    # Dispatch to the correct page function
    fn = _DISPATCH.get((section, sub))
    if fn:
        try:
            fn()
        except Exception as e:
            logger.exception("Family Management error in %s / %s: %s", section, sub, e)
            st.error(f"An error occurred: {e}")
    else:
        st.warning(f"Page not found: {section} → {sub}")
