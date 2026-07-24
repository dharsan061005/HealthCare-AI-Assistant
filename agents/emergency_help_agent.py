"""
Emergency Help Agent — emergency numbers, first-aid guides, AI emergency triage.
"""
import logging

import streamlit as st

from utils.i18n import get_lang, t
from utils.llm import simple_query

logger = logging.getLogger(__name__)

_FIRST_AID_PROMPT = """You are a certified first-aid and emergency response guide.
Provide clear, step-by-step first-aid instructions for the described situation.

Format your response as:

## ⚠️ Immediate Actions (Do This First)
Numbered steps to take RIGHT NOW.

## What NOT to Do
Bullet list of common mistakes to avoid.

## When to Call Emergency Services
Clear criteria for when 112/108 should be called.

## While Waiting for Help
What to do while waiting for professional help to arrive.

Keep instructions simple, numbered, and actionable.
Always prioritize calling emergency services for life-threatening situations.
Add a clear disclaimer that this is guidance only and professional help should be sought."""

EMERGENCY_NUMBERS = [
    ("🚑", "Ambulance",          "108"),
    ("🚒", "Fire Brigade",       "101"),
    ("🚔", "Police",             "100"),
    ("🆘", "National Emergency", "112"),
    ("👶", "Child Helpline",     "1098"),
    ("👩", "Women Helpline",     "1091"),
    ("🏥", "Disaster Management","1077"),
    ("☎️", "COVID Helpline",     "1800-112"),
]

FIRST_AID_SCENARIOS = [
    ("❤️ Heart Attack",          "Signs of heart attack and first aid steps"),
    ("🫁 Choking",               "Someone is choking and cannot breathe"),
    ("🩸 Severe Bleeding",       "Deep wound with heavy bleeding"),
    ("🔥 Burns",                  "Burn injury from fire, heat or chemicals"),
    ("⚡ Electric Shock",        "Person received electric shock"),
    ("💊 Poisoning / Overdose",  "Suspected poisoning or medication overdose"),
    ("🌡️ Heatstroke",            "Person collapsed from extreme heat"),
    ("🦴 Fracture / Broken Bone","Suspected broken bone or fracture"),
]


def _render_emergency_numbers() -> None:
    st.markdown("""
    <div style="background:linear-gradient(135deg,#FEF2F2,#FECACA);border:1px solid #FCA5A5;
                border-radius:12px;padding:1rem 1.25rem;margin-bottom:1.25rem;">
        <div style="font-weight:700;color:#991B1B;font-size:1rem;margin-bottom:0.75rem;">
            🚨 Emergency Contact Numbers — India
        </div>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(4)
    for i, (icon, label, number) in enumerate(EMERGENCY_NUMBERS):
        with cols[i % 4]:
            st.markdown(f"""
            <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;
                        padding:1rem;text-align:center;margin-bottom:0.75rem;
                        box-shadow:0 1px 4px rgba(0,0,0,0.06);">
                <div style="font-size:1.6rem;margin-bottom:0.35rem;">{icon}</div>
                <div style="font-size:0.75rem;color:#64748B;font-weight:600;
                             text-transform:uppercase;letter-spacing:0.05em;">{label}</div>
                <div style="font-size:1.5rem;font-weight:800;color:#EF4444;margin-top:0.2rem;">
                    {number}
                </div>
            </div>
            """, unsafe_allow_html=True)


def _render_first_aid() -> None:
    st.markdown("""
    <div style="font-weight:700;font-size:0.95rem;color:#0F172A;margin-bottom:0.75rem;">
        🩹 First Aid Guides — click a scenario or describe your emergency below
    </div>
    """, unsafe_allow_html=True)

    # Quick-scenario buttons
    cols = st.columns(2)
    for i, (label, prompt) in enumerate(FIRST_AID_SCENARIOS):
        if cols[i % 2].button(label, use_container_width=True, key=f"fa_{label}"):
            st.session_state["fa_query"] = prompt
            st.rerun()

    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

    # Custom query form
    with st.form("first_aid_form"):
        col1, col2 = st.columns([4, 1])
        with col1:
            query = st.text_input(
                "Describe the emergency",
                value=st.session_state.pop("fa_query", ""),
                placeholder="e.g. Someone fainted and is unresponsive…",
                label_visibility="collapsed",
            )
        with col2:
            submitted = st.form_submit_button("🚨 Get Help", type="primary", use_container_width=True)

    if submitted and query.strip():
        with st.spinner("Getting first-aid guidance…"):
            result = simple_query(_FIRST_AID_PROMPT, query.strip())

        if result.startswith("⚠️"):
            st.error(result)
        else:
            st.markdown("""
            <div style="background:#FEF2F2;border-left:4px solid #EF4444;border-radius:10px;
                        padding:0.75rem 1rem;margin-bottom:0.75rem;font-size:0.85rem;
                        color:#991B1B;font-weight:600;">
                🚨 If this is a life-threatening emergency, call 112 immediately. Do not wait.
            </div>
            """, unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown(result)
    elif submitted:
        st.warning("Please describe the emergency situation.")


def _render_tips() -> None:
    tips = [
        ("🧰", "Keep First Aid Kit Ready",
         "Stock bandages, antiseptic, gloves, scissors, thermometer, and basic medicines."),
        ("📱", "Save Emergency Contacts",
         "Save 112, 108 and your nearest hospital number in your phone."),
        ("🫀", "Learn Basic CPR",
         "30 chest compressions + 2 rescue breaths. Push hard and fast — 100–120/min."),
        ("🩸", "Blood Group Awareness",
         "Know your blood group and that of your family members. Keep it on a card."),
        ("💊", "Medicine List",
         "Carry a list of your current medications and allergies when traveling."),
        ("🏥", "Nearest Hospital",
         "Know the location and route to your nearest 24/7 emergency hospital."),
    ]

    st.markdown("<div class='section-label'>💡 Emergency Preparedness Tips</div>", unsafe_allow_html=True)
    cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(tips):
        with cols[i % 3]:
            st.markdown(f"""
            <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;
                        padding:1rem 1.1rem;margin-bottom:0.75rem;">
                <div style="font-size:1.4rem;margin-bottom:0.4rem;">{icon}</div>
                <div style="font-weight:700;font-size:0.88rem;color:#0F172A;
                             margin-bottom:0.3rem;">{title}</div>
                <div style="font-size:0.82rem;color:#475569;line-height:1.6;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)


def render() -> None:
    lang = get_lang(st.session_state)

    st.markdown(f"""
    <div class="page-header" style="background:linear-gradient(135deg,#FEF2F2,#FEE2E2);">
        <div style="display:flex;align-items:center;gap:1rem;">
            <span style="font-size:2.2rem;">🚑</span>
            <div>
                <h1 style="margin:0;">{t("emergency_title", lang)}</h1>
                <p style="margin:0;">{t("emergency_subtitle", lang)}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Big SOS banner
    st.markdown("""
    <div style="background:#EF4444;border-radius:12px;padding:1rem 1.5rem;
                margin-bottom:1.5rem;text-align:center;">
        <span style="font-size:1.1rem;font-weight:800;color:#FFFFFF;letter-spacing:0.05em;">
            🚨 LIFE-THREATENING EMERGENCY? CALL 112 NOW 🚨
        </span>
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["📞 Emergency Numbers", "🩹 First Aid Guide", "💡 Preparedness Tips"])

    with tabs[0]:
        _render_emergency_numbers()
    with tabs[1]:
        _render_first_aid()
    with tabs[2]:
        _render_tips()
