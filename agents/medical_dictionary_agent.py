"""
Medical Dictionary Agent — AI-powered medical term lookup.
"""
import logging

import streamlit as st

from utils.i18n import get_lang, t
from utils.llm import simple_query

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a medical dictionary and terminology expert.
When given a medical term, provide a clear, structured explanation:

## Definition
Plain-language definition (1-2 sentences).

## Pronunciation
Phonetic pronunciation guide.

## Origin / Etymology
Brief word-root explanation (Latin/Greek if applicable).

## Medical Context
How and where this term is used in medicine.

## Related Terms
2-4 related terms with brief definitions.

## Simple Explanation
One sentence a non-medical person can easily understand.

Keep it educational and easy to understand for patients and students."""

COMMON_TERMS = [
    "Hypertension", "Tachycardia", "Bradycardia", "Dyspnea",
    "Edema", "Arrhythmia", "Hypoglycemia", "Anemia",
    "Inflammation", "Ischemia", "Biopsy", "Prognosis",
]


def render() -> None:
    lang = get_lang(st.session_state)

    st.markdown(f"""
    <div class="page-header">
        <div style="display:flex;align-items:center;gap:1rem;">
            <span style="font-size:2.2rem;">📖</span>
            <div>
                <h1 style="margin:0;">{t("medical_dict_title", lang)}</h1>
                <p style="margin:0;">{t("medical_dict_subtitle", lang)}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:10px;
                padding:0.85rem 1.1rem;margin-bottom:1.25rem;font-size:0.85rem;color:#1E40AF;">
        📖 Look up any medical term, abbreviation, or procedure name for a plain-language explanation.
    </div>
    """, unsafe_allow_html=True)

    # Quick-select common terms
    st.markdown("<div class='section-label'>🔖 Common Terms — click to look up</div>", unsafe_allow_html=True)
    cols = st.columns(4)
    for i, term in enumerate(COMMON_TERMS):
        if cols[i % 4].button(term, use_container_width=True, key=f"dict_{term}"):
            st.session_state["dict_query"] = term
            st.rerun()

    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

    # Search form
    with st.form("dict_search_form"):
        col1, col2 = st.columns([4, 1])
        with col1:
            query = st.text_input(
                "Medical Term",
                value=st.session_state.pop("dict_query", ""),
                placeholder="e.g. Hypertension, ECG, Biopsy, CBC…",
                label_visibility="collapsed",
            )
        with col2:
            submitted = st.form_submit_button("🔍 Look Up", type="primary", use_container_width=True)

    if submitted and query.strip():
        term = query.strip()
        with st.spinner(f"Looking up '{term}'…"):
            result = simple_query(
                _SYSTEM_PROMPT,
                f"Explain the medical term: {term}",
            )

        if result.startswith("⚠️"):
            st.error(result)
        else:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.75rem;">
                <span style="font-size:1.4rem;">📖</span>
                <span style="font-weight:700;font-size:1.1rem;color:#0F172A;">{term}</span>
            </div>
            """, unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown(result)
            st.download_button(
                label="⬇️ Download Definition (.txt)",
                data=f"Medical Dictionary: {term}\n\n{result}".encode("utf-8"),
                file_name=f"{term.replace(' ', '_')}_definition.txt",
                mime="text/plain",
            )
    elif submitted:
        st.warning("Please enter a medical term to look up.")
