"""
Hospital Information Agent — redesigned UI
"""

import json
import logging
from typing import Any, Dict, List

import streamlit as st

import config
from utils import constants

logger = logging.getLogger(__name__)
DATA_DIR = config.DATA_DIR


# ── Data helpers ──────────────────────────────────────────────────────────────
def _load_json(filename: str) -> Any:
    path = DATA_DIR / filename
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error("Could not load %s: %s", path, e)
        return None

def _get_doctors()     -> List[Dict]: d = _load_json("doctors.json");     return (d or {}).get("doctors", [])
def _get_departments() -> List[Dict]: d = _load_json("departments.json"); return (d or {}).get("departments", [])
def _get_hospital_info() -> Dict:     return _load_json("hospital_info.json") or {}


# ── Page header banner ────────────────────────────────────────────────────────
def _page_header(title: str, subtitle: str, icon: str = "🏥") -> None:
    st.markdown(f"""
    <div class="page-header">
        <div style="display:flex; align-items:center; gap:1rem;">
            <span style="font-size:2.2rem;">{icon}</span>
            <div>
                <h1 style="margin:0;">{title}</h1>
                <p style="margin:0;">{subtitle}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Overview ──────────────────────────────────────────────────────────────────
def _render_overview(hospital: Dict) -> None:
    info = hospital.get("hospital", {})

    # Key stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Established",        info.get("established", "—"))
    c2.metric("Bed Capacity",       info.get("bed_capacity", "—"))
    c3.metric("ICU Beds",           info.get("icu_beds", "—"))
    c4.metric("Operation Theatres", info.get("operation_theatres", "—"))

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        addr = info.get("address", {})
        st.markdown(f"""
        <div class="info-card">
            <div class="section-label">📍 Address</div>
            <div style="font-size:0.95rem; color:#0F172A; line-height:1.7;">
                {addr.get('line1','')}<br>
                {addr.get('line2','')}<br>
                {addr.get('city','')}, {addr.get('state','')} — {addr.get('pin','')}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        contact = info.get("contact", {})
        st.markdown(f"""
        <div class="info-card">
            <div class="section-label">📞 Contact</div>
            <div style="font-size:0.9rem; line-height:2;">
                <span style="color:#64748B;">Main</span>
                <span style="float:right; font-weight:600; color:#0F172A;">{contact.get('main','—')}</span><br>
                <span style="color:#64748B;">Emergency</span>
                <span style="float:right; font-weight:600; color:#EF4444;">{contact.get('emergency','—')}</span><br>
                <span style="color:#64748B;">Appointments</span>
                <span style="float:right; font-weight:600; color:#0F172A;">{contact.get('appointment','—')}</span><br>
                <span style="color:#64748B;">Email</span>
                <span style="float:right; font-weight:600; color:#0EA5E9;">{contact.get('email','—')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # Timings
    timings = info.get("timings", {})
    timing_items = [
        ("🕐 OPD",           timings.get("opd", "—")),
        ("🚨 Emergency",     timings.get("emergency", "—")),
        ("💊 Pharmacy",      timings.get("pharmacy", "—")),
        ("🔬 Laboratory",    timings.get("lab", "—")),
        ("🩻 Radiology",     timings.get("radiology", "—")),
        ("👥 Visiting Hours",timings.get("visiting_hours", "—")),
    ]
    st.markdown("<div class='section-label'>🕐 Operating Hours</div>", unsafe_allow_html=True)
    t_cols = st.columns(3)
    for i, (label, value) in enumerate(timing_items):
        with t_cols[i % 3]:
            st.markdown(f"""
            <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px;
                        padding:0.85rem 1rem; margin-bottom:0.6rem;">
                <div style="font-size:0.75rem; color:#64748B; font-weight:600;">{label}</div>
                <div style="font-size:0.9rem; color:#0F172A; font-weight:600; margin-top:0.2rem;">{value}</div>
            </div>
            """, unsafe_allow_html=True)

    # Accreditations
    accreditations = info.get("accreditation", [])
    if accreditations:
        st.markdown("<div class='section-label' style='margin-top:1rem;'>🏆 Accreditations</div>", unsafe_allow_html=True)
        a_cols = st.columns(len(accreditations))
        for col, acc in zip(a_cols, accreditations):
            col.markdown(f"""
            <div style="background:linear-gradient(135deg,#D1FAE5,#A7F3D0); border:1px solid #6EE7B7;
                        border-radius:10px; padding:0.75rem 1rem; text-align:center;">
                <span style="font-size:1.1rem;">✅</span>
                <div style="font-size:0.85rem; font-weight:700; color:#065F46; margin-top:0.25rem;">{acc}</div>
            </div>
            """, unsafe_allow_html=True)


# ── Departments ───────────────────────────────────────────────────────────────
def _render_departments(departments: List[Dict]) -> None:
    search_term = st.text_input("🔍 Search departments", placeholder="e.g. Cardiology, Emergency...", key="dept_search").strip().lower()
    filtered = [
        d for d in departments
        if search_term in d.get("name", "").lower() or search_term in d.get("description", "").lower()
    ] if search_term else departments

    if not filtered:
        st.warning("No departments match your search.")
        return

    st.markdown(f"<div class='section-label'>{len(filtered)} department(s)</div>", unsafe_allow_html=True)

    for dept in filtered:
        is_emergency = dept.get("emergency", False)
        icon = "🚨" if is_emergency else "🏥"
        with st.expander(f"{icon}  {dept.get('name','')}  —  {dept.get('floor','')}", expanded=False):
            c1, c2 = st.columns([3, 2])
            with c1:
                st.markdown(f"**Head of Department:** {dept.get('head_of_department','—')}")
                st.markdown(f"**Phone:** {dept.get('phone','—')}")
                st.markdown(dept.get("description", ""))
            with c2:
                services = dept.get("services", [])
                if services:
                    st.markdown("**Services Offered:**")
                    for svc in services:
                        st.markdown(f"<span style='font-size:0.85rem;'>▸ {svc}</span>", unsafe_allow_html=True)
            if is_emergency:
                st.info("🚨 Emergency services available 24 / 7")


# ── Doctors ───────────────────────────────────────────────────────────────────
def _render_doctors(doctors: List[Dict]) -> None:
    specializations = sorted(set(d.get("specialization", "") for d in doctors))
    spec_filter = st.selectbox("Filter by Specialization", ["All Specializations"] + specializations, key="doc_spec_filter")

    filtered = [d for d in doctors if d.get("specialization") == spec_filter] if spec_filter != "All Specializations" else doctors

    if not filtered:
        st.warning("No doctors found.")
        return

    st.markdown(f"<div class='section-label'>{len(filtered)} doctor(s)</div>", unsafe_allow_html=True)

    for i in range(0, len(filtered), 2):
        cols = st.columns(2)
        for col, doc in zip(cols, filtered[i:i+2]):
            with col:
                with st.expander(f"👤  {doc.get('name','')}  ·  {doc.get('specialization','')}", expanded=False):
                    st.markdown(f"""
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.5rem; font-size:0.88rem; margin-bottom:0.75rem;">
                        <div><span style="color:#64748B;">Qualification</span><br><b>{doc.get('qualification','—')}</b></div>
                        <div><span style="color:#64748B;">Experience</span><br><b>{doc.get('experience_years','—')} yrs</b></div>
                        <div><span style="color:#64748B;">Consultation Fee</span><br><b>₹{doc.get('consultation_fee','—')}</b></div>
                        <div><span style="color:#64748B;">Room</span><br><b>{doc.get('room_number','—')}</b></div>
                        <div><span style="color:#64748B;">Timings</span><br><b>{doc.get('timings','—')}</b></div>
                        <div><span style="color:#64748B;">Languages</span><br><b>{', '.join(doc.get('languages',[]))}</b></div>
                    </div>
                    """, unsafe_allow_html=True)
                    slots = doc.get("available_slots", [])
                    if slots:
                        st.markdown("**Available Slots:**")
                        slot_html = " ".join(
                            f"<span style='background:#E0F2FE; color:#0284C7; border-radius:6px; "
                            f"padding:2px 10px; font-size:0.78rem; font-weight:600; margin:2px;'>{s}</span>"
                            for s in slots
                        )
                        st.markdown(slot_html, unsafe_allow_html=True)
                    if doc.get("about"):
                        st.caption(doc["about"])


# ── Facilities ────────────────────────────────────────────────────────────────
def _render_facilities(hospital: Dict) -> None:
    facilities = hospital.get("facilities", [])
    col1, col2 = st.columns(2)
    for i, fac in enumerate(facilities):
        col = col1 if i % 2 == 0 else col2
        with col:
            badge = "<span style='background:#FEF3C7;color:#92400E;font-size:0.7rem;font-weight:700;padding:2px 8px;border-radius:99px;'>24/7</span>" if fac.get("available_24_7") else ""
            st.markdown(f"""
            <div class="info-card" style="margin-bottom:0.75rem;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.5rem;">
                    <div style="font-weight:700; font-size:0.95rem; color:#0F172A;">{fac.get('name','')}</div>
                    {badge}
                </div>
                <div style="font-size:0.8rem; color:#64748B; margin-bottom:0.4rem;">📍 {fac.get('location','—')}</div>
                <div style="font-size:0.85rem; color:#475569;">{fac.get('description','')}</div>
            </div>
            """, unsafe_allow_html=True)


# ── Insurance ─────────────────────────────────────────────────────────────────
def _render_insurance(hospital: Dict) -> None:
    insurance = hospital.get("insurance", {})

    st.markdown("<div class='section-label'>Cashless Insurance Partners</div>", unsafe_allow_html=True)
    partners = insurance.get("cashless_partners", [])
    p_cols = st.columns(4)
    for i, p in enumerate(partners):
        p_cols[i % 4].markdown(f"""
        <div style="background:#F0FDF4; border:1px solid #BBF7D0; border-radius:8px;
                    padding:0.6rem 0.85rem; font-size:0.82rem; font-weight:600;
                    color:#15803D; margin-bottom:0.5rem; text-align:center;">✅ {p}</div>
        """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='section-label' style='margin-top:1rem;'>TPA Partners</div>", unsafe_allow_html=True)
        for tpa in insurance.get("tpa_partners", []):
            st.markdown(f"<span style='font-size:0.88rem;'>▸ {tpa}</span>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='section-label' style='margin-top:1rem;'>Government Schemes</div>", unsafe_allow_html=True)
        for scheme in insurance.get("government_schemes", []):
            st.markdown(f"<span style='font-size:0.88rem;'>▸ {scheme}</span>", unsafe_allow_html=True)


# ── FAQs ──────────────────────────────────────────────────────────────────────
def _render_faqs(hospital: Dict) -> None:
    faqs = hospital.get("faqs", [])
    for faq in faqs:
        with st.expander(f"❓  {faq.get('question','')}", expanded=False):
            st.markdown(faq.get("answer", ""))


# ── AI Chat ───────────────────────────────────────────────────────────────────
def _render_llm_chat(hospital: Dict, doctors: List[Dict], departments: List[Dict]) -> None:
    st.markdown("""
    <div style="background:linear-gradient(135deg,#EFF6FF,#DBEAFE); border:1px solid #BFDBFE;
                border-radius:12px; padding:1rem 1.25rem; margin-bottom:1.25rem;">
        <div style="font-weight:700; color:#1E40AF; font-size:0.95rem;">💬 Ask the Hospital AI</div>
        <div style="color:#3B82F6; font-size:0.83rem; margin-top:0.25rem;">
            Ask about departments, doctors, timings, facilities — anything not covered above.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if "hospital_chat_history" not in st.session_state:
        st.session_state.hospital_chat_history = []

    col_chat, col_clear = st.columns([6, 1])
    with col_clear:
        if st.button("🗑️ Clear", key="clear_hospital_chat"):
            st.session_state.hospital_chat_history = []
            st.rerun()

    for msg in st.session_state.hospital_chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask about the hospital...")
    if user_input:
        st.session_state.hospital_chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.chat_message("assistant"):
            with st.spinner("Looking up..."):
                context = (
                    f"Hospital: {json.dumps(hospital.get('hospital', {}), indent=2)}\n\n"
                    f"Departments: {[d.get('name') for d in departments]}\n\n"
                    f"Doctors: {[{'name': d.get('name'), 'spec': d.get('specialization'), 'timings': d.get('timings')} for d in doctors]}"
                )
                from utils.llm import simple_query
                reply = simple_query(
                    constants.HOSPITAL_INFO_SYSTEM_PROMPT + f"\n\nHospital data:\n{context}",
                    user_input,
                )
                st.markdown(reply)
        st.session_state.hospital_chat_history.append({"role": "assistant", "content": reply})


# ── Main render ───────────────────────────────────────────────────────────────
def render() -> None:
    _page_header("Hospital Information", "Explore departments, doctors, facilities and more")

    hospital    = _get_hospital_info()
    doctors     = _get_doctors()
    departments = _get_departments()

    if not hospital:
        st.error("Hospital data could not be loaded. Check `data/hospital_info.json`.")
        return

    tabs = st.tabs(["🏠 Overview", "🏬 Departments", "👨‍⚕️ Doctors", "🏗️ Facilities", "💳 Insurance", "❓ FAQs", "💬 Ask AI"])

    with tabs[0]: _render_overview(hospital)
    with tabs[1]: _render_departments(departments)
    with tabs[2]: _render_doctors(doctors)
    with tabs[3]: _render_facilities(hospital)
    with tabs[4]: _render_insurance(hospital)
    with tabs[5]: _render_faqs(hospital)
    with tabs[6]: _render_llm_chat(hospital, doctors, departments)
