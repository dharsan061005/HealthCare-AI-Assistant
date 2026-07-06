"""
Symptom Checker Agent — redesigned UI with optional patient context
"""

import logging
from typing import Dict, List

import streamlit as st

from utils import constants
from utils.llm import chat_completion
from utils.validators import validate_symptoms_input

logger = logging.getLogger(__name__)

QUICK_EXAMPLES = [
    ("🤕 Headache & Fever",    "I have a severe headache and fever of 102°F for the past 2 days, with body aches and fatigue."),
    ("💔 Chest Pain",          "I'm experiencing mild chest pain and shortness of breath when climbing stairs. No history of heart disease."),
    ("🤢 Stomach Issues",      "I've had stomach cramps, nausea, and loose stools for the past day. I ate out yesterday."),
    ("😴 Fatigue & Dizziness", "I feel extremely tired and dizzy for the last 3 days. I haven't changed my diet or sleep schedule."),
    ("🤧 Cold & Cough",        "I have a runny nose, sore throat, and dry cough for 4 days. Mild fever of 99°F."),
    ("🦴 Joint Pain",          "My knees and ankles have been aching for 2 weeks, worse in the morning. I'm 45 years old."),
]

KNOWN_CONDITIONS = [
    "None",
    "Diabetes (Type 1)",
    "Diabetes (Type 2)",
    "Hypertension",
    "Asthma",
    "Heart Disease",
    "Thyroid Disorder",
    "Kidney Disease",
    "Liver Disease",
    "Arthritis",
    "Epilepsy",
    "Depression / Anxiety",
    "Other",
]


def _build_system_prompt(patient: dict) -> str:
    """Append patient context to the base system prompt if provided."""
    base = constants.SYMPTOM_CHECKER_SYSTEM_PROMPT
    lines = []
    if patient.get("age"):
        lines.append(f"Patient Age: {patient['age']} years")
    if patient.get("gender") and patient["gender"] != "Select…":
        lines.append(f"Patient Gender: {patient['gender']}")
    conditions = [c for c in patient.get("conditions", []) if c and c != "None"]
    if conditions:
        lines.append(f"Known Medical Conditions: {', '.join(conditions)}")
    if patient.get("allergies"):
        lines.append(f"Known Allergies: {patient['allergies']}")
    if patient.get("medications"):
        lines.append(f"Current Medications: {patient['medications']}")

    if not lines:
        return base

    ctx_block = (
        "\n\nPATIENT CONTEXT (use this to tailor your response):\n"
        + "\n".join(lines)
        + "\n\nTailor your possible conditions, self-care advice, and urgency level based on the patient's age, gender, and known conditions."
    )
    return base + ctx_block


def _build_messages(history: List[Dict[str, str]], user_msg: str, patient: dict) -> List[Dict[str, str]]:
    msgs = [{"role": "system", "content": _build_system_prompt(patient)}]
    msgs.extend(history)
    msgs.append({"role": "user", "content": user_msg})
    return msgs


def render() -> None:
    # ── Page header ───────────────────────────────────────────────────────────
    st.markdown("""
    <div class="page-header">
        <div style="display:flex; align-items:center; gap:1rem;">
            <span style="font-size:2.2rem;">🩺</span>
            <div>
                <h1 style="margin:0;">Symptom Checker</h1>
                <p style="margin:0;">Describe your symptoms and get AI-powered health guidance</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Disclaimer ────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="background:#FEF3C7; border-left:4px solid #F59E0B; border-radius:10px;
                padding:0.85rem 1.1rem; margin-bottom:1.25rem; font-size:0.85rem; color:#78350F;">
        <strong>⚠️ Medical Disclaimer:</strong> This is AI-generated information only and
        does not constitute a medical diagnosis. Always consult a qualified healthcare
        professional for advice, diagnosis, or treatment.
    </div>
    """, unsafe_allow_html=True)

    # ── Session state ─────────────────────────────────────────────────────────
    if "symptom_chat_history" not in st.session_state:
        st.session_state.symptom_chat_history = []
    if "symptom_patient" not in st.session_state:
        st.session_state.symptom_patient = {}

    # ── Patient context panel ─────────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0.6rem;">
        <span style="background:#0EA5E9; color:#fff; border-radius:50%; width:22px; height:22px;
                     display:flex; align-items:center; justify-content:center;
                     font-size:0.72rem; font-weight:700; flex-shrink:0;">1</span>
        <span style="font-weight:700; font-size:0.95rem; color:#0F172A;">Patient Context</span>
        <span style="font-size:0.78rem; color:#94A3B8;">(optional — improves accuracy)</span>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Fill in patient details for a more tailored analysis", expanded=False):
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            pt_age = st.number_input(
                "Age (years)", min_value=0, max_value=120, value=0, step=1, key="sc_age"
            )
        with pc2:
            pt_gender = st.selectbox(
                "Gender", ["Select…", "Male", "Female", "Other", "Prefer not to say"], key="sc_gender"
            )
        with pc3:
            pt_allergies = st.text_input(
                "Known Allergies", placeholder="e.g. Penicillin, dust", key="sc_allergies"
            )

        pc4, pc5 = st.columns(2)
        with pc4:
            pt_conditions = st.multiselect(
                "Known Medical Conditions",
                options=KNOWN_CONDITIONS[1:],   # exclude "None" from multiselect
                key="sc_conditions",
                placeholder="Select any that apply…",
            )
        with pc5:
            pt_medications = st.text_input(
                "Current Medications", placeholder="e.g. Metformin, Lisinopril", key="sc_medications"
            )

        # Persist into session state so it survives chat reruns
        st.session_state.symptom_patient = {
            "age":         pt_age if pt_age > 0 else None,
            "gender":      pt_gender,
            "conditions":  pt_conditions,
            "allergies":   pt_allergies.strip(),
            "medications": pt_medications.strip(),
        }

        # Show active context pills
        active = []
        if pt_age > 0:                                 active.append(f"👤 {pt_age} yrs")
        if pt_gender not in ("Select…", ""):           active.append(f"⚧ {pt_gender}")
        if pt_conditions:                              active.append(f"🏥 {', '.join(pt_conditions)}")
        if pt_allergies.strip():                       active.append(f"⚠️ Allergy: {pt_allergies.strip()}")
        if pt_medications.strip():                     active.append(f"💊 {pt_medications.strip()}")

        if active:
            pills_html = "".join(
                f"<span style='background:#E0F2FE; color:#0284C7; border-radius:99px; "
                f"padding:3px 10px; font-size:0.78rem; font-weight:600; margin:2px;'>{p}</span>"
                for p in active
            )
            st.markdown(
                f"<div style='margin-top:0.75rem; display:flex; flex-wrap:wrap; gap:4px;'>"
                f"<span style='font-size:0.78rem; color:#64748B; align-self:center;'>Active context:</span>"
                f"{pills_html}</div>",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── Chat controls row ─────────────────────────────────────────────────────
    ctl_col, tips_col = st.columns([1, 3])
    with ctl_col:
        msg_count = len(st.session_state.symptom_chat_history)
        st.markdown(
            f"<div style='font-size:0.82rem; color:#64748B; padding-top:0.4rem;'>"
            f"💬 {msg_count} message{'s' if msg_count != 1 else ''} in session</div>",
            unsafe_allow_html=True,
        )
        if st.button("🗑️ Clear Chat", key="clear_symptom_chat", use_container_width=True):
            st.session_state.symptom_chat_history = []
            st.rerun()
    with tips_col:
        st.markdown("""
        <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px;
                    padding:0.6rem 1rem; font-size:0.8rem; color:#475569; line-height:1.7;">
            <b style="color:#0F172A;">Tips for better results:</b>
            &nbsp;· Mention duration (e.g. <i>3 days</i>)
            &nbsp;· Rate severity (mild / moderate / severe)
            &nbsp;· Include related symptoms
            &nbsp;· Fill in Patient Context above
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── Step 2 label ──────────────────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0.75rem;">
        <span style="background:#0EA5E9; color:#fff; border-radius:50%; width:22px; height:22px;
                     display:flex; align-items:center; justify-content:center;
                     font-size:0.72rem; font-weight:700; flex-shrink:0;">2</span>
        <span style="font-weight:700; font-size:0.95rem; color:#0F172A;">Describe Your Symptoms</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Quick examples (only when chat is empty) ──────────────────────────────
    if not st.session_state.symptom_chat_history:
        st.markdown("<div class='section-label'>Quick Examples — click to try</div>", unsafe_allow_html=True)
        row1 = st.columns(3)
        row2 = st.columns(3)
        for col, (label, text) in zip(row1 + row2, QUICK_EXAMPLES):
            if col.button(label, use_container_width=True, key=f"ex_{label}"):
                st.session_state["prefill_symptom"] = text
                st.rerun()
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── Chat history ──────────────────────────────────────────────────────────
    for msg in st.session_state.symptom_chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ── Input ─────────────────────────────────────────────────────────────────
    prefill    = st.session_state.pop("prefill_symptom", "")
    user_input = st.chat_input("Describe your symptoms… (e.g. 'headache and sore throat for 2 days')")
    if not user_input and prefill:
        user_input = prefill

    if user_input:
        valid, error_msg = validate_symptoms_input(user_input)
        if not valid:
            st.error(error_msg)
            return

        st.session_state.symptom_chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Analysing your symptoms…"):
                messages = _build_messages(
                    st.session_state.symptom_chat_history[:-1],
                    user_input,
                    st.session_state.symptom_patient,
                )
                response = chat_completion(messages)
            st.markdown(response)
            st.markdown("""
            <div style="margin-top:0.75rem; padding-top:0.75rem; border-top:1px solid #E2E8F0;
                        font-size:0.75rem; color:#94A3B8;">
                ⚠️ AI-generated — not a medical diagnosis. Consult a healthcare professional.
            </div>
            """, unsafe_allow_html=True)

        st.session_state.symptom_chat_history.append({"role": "assistant", "content": response})
