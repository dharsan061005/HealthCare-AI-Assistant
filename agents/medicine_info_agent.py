"""
Medicine Information Agent — AI-powered medicine lookup.
"""
import logging

import streamlit as st

from utils.i18n import get_lang, t
from utils.llm import simple_query

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a pharmaceutical information assistant.
When given a medicine name, provide a structured summary covering:

## Medicine Overview
Brief description and drug class.

## Common Uses
Bullet list of what it is prescribed for.

## Typical Dosage
General dosage information (always note that actual dosage must be prescribed by a doctor).

## Common Side Effects
Bullet list of frequent side effects.

## Important Warnings
Key precautions, contraindications, and drug interactions to be aware of.

## Storage
How to store the medicine properly.

Keep language simple and patient-friendly.
Always remind the user to follow their doctor's or pharmacist's instructions.
Do NOT recommend specific doses — only provide general information."""

COMMON_MEDICINES = [
    "Paracetamol", "Ibuprofen", "Metformin", "Amlodipine",
    "Atorvastatin", "Omeprazole", "Amoxicillin", "Azithromycin",
]


def render() -> None:
    lang = get_lang(st.session_state)

    st.markdown(f"""
    <div class="page-header">
        <div style="display:flex;align-items:center;gap:1rem;">
            <span style="font-size:2.2rem;">💊</span>
            <div>
                <h1 style="margin:0;">{t("medicine_info_title", lang)}</h1>
                <p style="margin:0;">{t("medicine_info_subtitle", lang)}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:#FEF3C7;border-left:4px solid #F59E0B;border-radius:10px;
                padding:0.85rem 1.1rem;margin-bottom:1.25rem;font-size:0.85rem;color:#78350F;">
        {t("medical_disclaimer", lang)}
    </div>
    """, unsafe_allow_html=True)

    # Common medicines quick-select
    st.markdown("<div class='section-label'>🔖 Common Medicines — click to look up</div>", unsafe_allow_html=True)
    cols = st.columns(4)
    for i, med in enumerate(COMMON_MEDICINES):
        if cols[i % 4].button(med, use_container_width=True, key=f"med_{med}"):
            st.session_state["med_query"] = med
            st.rerun()

    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

    # Search form
    with st.form("medicine_search_form"):
        col1, col2 = st.columns([4, 1])
        with col1:
            query = st.text_input(
                t("medicine_name", lang),
                value=st.session_state.pop("med_query", ""),
                placeholder="e.g. Paracetamol, Metformin, Atorvastatin…",
                label_visibility="collapsed",
            )
        with col2:
            submitted = st.form_submit_button("🔍 Search", type="primary", use_container_width=True)

    if submitted and query.strip():
        medicine = query.strip()
        with st.spinner(f"Looking up {medicine}…"):
            result = simple_query(
                _SYSTEM_PROMPT,
                f"Provide detailed information about the medicine: {medicine}",
            )

        if result.startswith("⚠️"):
            st.error(result)
        else:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.75rem;">
                <span style="font-size:1.4rem;">💊</span>
                <span style="font-weight:700;font-size:1.1rem;color:#0F172A;">{medicine}</span>
            </div>
            """, unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown(result)

            # Download
            st.download_button(
                label="⬇️ Download Info (.txt)",
                data=f"Medicine Information: {medicine}\n\n{result}".encode("utf-8"),
                file_name=f"{medicine.replace(' ', '_')}_info.txt",
                mime="text/plain",
            )
    elif submitted:
        st.warning("Please enter a medicine name.")
