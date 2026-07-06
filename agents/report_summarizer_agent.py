"""
Medical Report Summarizer Agent — with Patient Details form
"""

import logging
from datetime import date, datetime

import streamlit as st

from utils import constants
from utils.llm import simple_query
from utils.pdf_reader import extract_text_from_uploaded_file

logger = logging.getLogger(__name__)
MAX_TEXT_CHARS = 6000

REPORT_TYPES = [
    "Select report type…",
    "Blood Test / CBC",
    "Liver Function Test (LFT)",
    "Kidney Function Test (KFT)",
    "Lipid Profile",
    "Thyroid Function Test",
    "Blood Sugar / HbA1c",
    "Urine Analysis",
    "X-Ray Report",
    "MRI / CT Scan Report",
    "ECG / Echo Report",
    "Discharge Summary",
    "Pathology / Biopsy Report",
    "Other",
]

GENDERS = ["Select…", "Male", "Female", "Other", "Prefer not to say"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _truncate_for_llm(text: str) -> tuple[str, bool]:
    if len(text) <= MAX_TEXT_CHARS:
        return text, False
    truncated = text[:MAX_TEXT_CHARS]
    last_period = truncated.rfind(".")
    if last_period > MAX_TEXT_CHARS * 0.8:
        truncated = truncated[: last_period + 1]
    return truncated + "\n\n[... Report truncated for processing ...]", True


def _build_patient_context(patient: dict) -> str:
    """Build a natural-language patient context string for the LLM."""
    lines = []
    if patient.get("name"):
        lines.append(f"Patient Name: {patient['name']}")
    if patient.get("age"):
        lines.append(f"Age: {patient['age']} years")
    if patient.get("gender") and patient["gender"] not in ("Select…", ""):
        lines.append(f"Gender: {patient['gender']}")
    if patient.get("report_type") and patient["report_type"] not in ("Select report type…", ""):
        lines.append(f"Report Type: {patient['report_type']}")
    if patient.get("report_date"):
        lines.append(f"Report Date: {patient['report_date']}")
    if patient.get("doctor"):
        lines.append(f"Referring Doctor: {patient['doctor']}")
    if patient.get("lab"):
        lines.append(f"Laboratory / Hospital: {patient['lab']}")
    if patient.get("notes"):
        lines.append(f"Patient Notes / Symptoms: {patient['notes']}")
    return "\n".join(lines)


def _generate_summary(extracted_text: str, patient: dict, language: str = "Tamil") -> str:
    text_for_llm, was_truncated = _truncate_for_llm(extracted_text)

    if language == "Tamil":
        truncation_note = (
            "\n\n*குறிப்பு: அறிக்கை நீளம் அதிகமாக இருப்பதால் சுருக்கப்பட்டது. "
            "சுருக்கம் முதல் பகுதியை மட்டும் உள்ளடக்கியது.*"
            if was_truncated else ""
        )
        system_prompt = constants.REPORT_SUMMARIZER_SYSTEM_PROMPT_TAMIL
    else:
        truncation_note = (
            "\n\n*Note: The report was truncated due to length. Summary covers the first portion.*"
            if was_truncated else ""
        )
        system_prompt = constants.REPORT_SUMMARIZER_SYSTEM_PROMPT

    patient_ctx = _build_patient_context(patient)

    if language == "Tamil":
        patient_section = (
            f"\n\nநோயாளி விவரங்கள் (PATIENT CONTEXT):\n{patient_ctx}\n\n"
            f"நோயாளியின் வயது, பாலினம் மற்றும் குறிப்புகளை கணக்கில் எடுத்து பகுப்பாய்வு செய்யவும்."
            if patient_ctx else ""
        )
        prompt = (
            f"கீழே கொடுக்கப்பட்டுள்ள மருத்துவ அறிக்கையை பகுப்பாய்வு செய்து தமிழில் சுருக்கமாக வழங்கவும்."
            f"{patient_section}\n\n"
            f"அறிக்கை உரை (REPORT TEXT):\n---\n{text_for_llm}\n---"
        )
    else:
        patient_section = (
            f"\n\nPATIENT CONTEXT:\n{patient_ctx}\n\nPlease tailor your analysis considering the patient's age, gender, and any notes provided."
            if patient_ctx else ""
        )
        prompt = (
            f"Please analyze and summarize the following medical report text."
            f"{patient_section}\n\n"
            f"REPORT TEXT:\n---\n{text_for_llm}\n---"
        )

    return simple_query(system_prompt, prompt) + truncation_note


def _create_download_text(filename: str, extracted_text: str, summary: str, patient: dict, language: str = "Tamil") -> str:
    ts  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sep = "=" * 60
    patient_ctx = _build_patient_context(patient)
    patient_block = f"\nPATIENT DETAILS\n{sep}\n{patient_ctx}\n\n" if patient_ctx else ""
    disclaimer = (
        constants.REPORT_DISCLAIMER_TAMIL if language == "Tamil"
        else constants.REPORT_DISCLAIMER
    )
    summary_label   = "AI சுருக்கம் (AI SUMMARY)" if language == "Tamil" else "AI SUMMARY"
    disclaimer_label = "முன்னெச்சரிக்கை (DISCLAIMER)" if language == "Tamil" else "DISCLAIMER"
    raw_label        = "எடுக்கப்பட்ட உரை — அசல் (EXTRACTED TEXT — Original)" if language == "Tamil" else "EXTRACTED TEXT (Original)"
    return (
        f"MEDICAL REPORT SUMMARY\n{sep}\n"
        f"Original File : {filename}\n"
        f"Generated At  : {ts}\n"
        f"Language      : {language}\n"
        f"{sep}\n\n"
        f"{patient_block}"
        f"{summary_label}\n{sep}\n"
        f"{summary}\n\n"
        f"{sep}\n{disclaimer_label}\n{sep}\n"
        f"{disclaimer.replace('**','').replace('⚠️ ','')}\n\n"
        f"{sep}\n{raw_label}\n{sep}\n{extracted_text}\n"
    )


# ── Main render ───────────────────────────────────────────────────────────────

def render() -> None:
    # ── Page header ───────────────────────────────────────────────────────────
    st.markdown("""
    <div class="page-header">
        <div style="display:flex; align-items:center; gap:1rem;">
            <span style="font-size:2.2rem;">📄</span>
            <div>
                <h1 style="margin:0;">Medical Report Summarizer</h1>
                <p style="margin:0;">Enter patient details, upload a PDF report and get an AI-generated structured summary</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Session state ─────────────────────────────────────────────────────────
    for key in ("report_summary", "report_extracted_text", "report_filename", "report_patient", "report_language"):
        if key not in st.session_state:
            st.session_state[key] = None

    # ══════════════════════════════════════════════════════════════════════════
    # LANGUAGE SELECTOR
    # ══════════════════════════════════════════════════════════════════════════
    lang_col, _ = st.columns([2, 3])
    with lang_col:
        lang_choice = st.radio(
            "🌐 Output Language / வெளியீட்டு மொழி",
            options=["Tamil (தமிழ்)", "English"],
            index=0,
            horizontal=True,
            key="lang_selector",
        )
    language = "Tamil" if lang_choice.startswith("Tamil") else "English"

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── Disclaimer (language-aware) ───────────────────────────────────────────
    if language == "Tamil":
        st.markdown("""
        <div style="background:#FEF3C7; border-left:4px solid #F59E0B; border-radius:10px;
                    padding:0.85rem 1.1rem; margin-bottom:1.5rem; font-size:0.85rem; color:#78350F;">
            <strong>⚠️ முன்னெச்சரிக்கை:</strong> இந்த AI சுருக்கம் தகவல் நோக்கங்களுக்காக மட்டுமே.
            இது தொழில்முறை மருத்துவ விளக்கத்திற்கு மாற்றாகாது. உங்கள் மருத்துவரிடம் முடிவுகளை விவாதிக்கவும்.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#FEF3C7; border-left:4px solid #F59E0B; border-radius:10px;
                    padding:0.85rem 1.1rem; margin-bottom:1.5rem; font-size:0.85rem; color:#78350F;">
            <strong>⚠️ Disclaimer:</strong> This AI summary is for informational purposes only.
            It does not replace professional medical interpretation. Please discuss results with your doctor.
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — Patient Details
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("""
    <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0.75rem;">
        <span style="background:#0EA5E9; color:#fff; border-radius:50%; width:24px; height:24px;
                     display:flex; align-items:center; justify-content:center;
                     font-size:0.75rem; font-weight:700; flex-shrink:0;">1</span>
        <span style="font-weight:700; font-size:1rem; color:#0F172A;">Patient Details</span>
        <span style="font-size:0.78rem; color:#94A3B8; margin-left:0.25rem;">(optional but improves accuracy)</span>
    </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        r1c1, r1c2, r1c3 = st.columns(3)
        with r1c1:
            patient_name = st.text_input(
                "Patient Name",
                placeholder="e.g. Ravi Kumar",
                key="pt_name",
            )
        with r1c2:
            patient_age = st.number_input(
                "Age (years)",
                min_value=0, max_value=120, value=0, step=1,
                key="pt_age",
            )
        with r1c3:
            patient_gender = st.selectbox(
                "Gender",
                GENDERS,
                key="pt_gender",
            )

        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1:
            report_type = st.selectbox(
                "Report Type",
                REPORT_TYPES,
                key="pt_report_type",
            )
        with r2c2:
            report_date = st.date_input(
                "Report Date",
                value=date.today(),
                max_value=date.today(),
                key="pt_report_date",
            )
        with r2c3:
            referring_doctor = st.text_input(
                "Referring Doctor",
                placeholder="e.g. Dr. Ananya Sharma",
                key="pt_doctor",
            )

        r3c1, r3c2 = st.columns(2)
        with r3c1:
            lab_name = st.text_input(
                "Laboratory / Hospital",
                placeholder="e.g. Apollo Diagnostics",
                key="pt_lab",
            )
        with r3c2:
            patient_notes = st.text_input(
                "Symptoms / Additional Notes",
                placeholder="e.g. fatigue, high BP, follow-up after 3 months",
                key="pt_notes",
            )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — Upload Report
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("""
    <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0.75rem;">
        <span style="background:#0EA5E9; color:#fff; border-radius:50%; width:24px; height:24px;
                     display:flex; align-items:center; justify-content:center;
                     font-size:0.75rem; font-weight:700; flex-shrink:0;">2</span>
        <span style="font-weight:700; font-size:1rem; color:#0F172A;">Upload Report PDF</span>
    </div>
    """, unsafe_allow_html=True)

    upload_col, tips_col = st.columns([3, 2], gap="large")

    with upload_col:
        uploaded_file = st.file_uploader(
            "Upload PDF",
            type=["pdf"],
            help="Text-based PDFs only. Scanned images are not supported.",
            label_visibility="collapsed",
            key="report_uploader",
        )

        if not uploaded_file:
            st.markdown("""
            <div style="text-align:center; padding:0.4rem 0 0.75rem; color:#94A3B8; font-size:0.83rem;">
                📎 Drag &amp; drop a PDF here, or click the button above to browse
            </div>
            """, unsafe_allow_html=True)

        action_col, clear_col = st.columns([3, 1])
        with action_col:
            summarize_btn = st.button(
                "🔍 Analyse Report",
                type="primary",
                disabled=uploaded_file is None,
                use_container_width=True,
            )
        with clear_col:
            if st.button("🗑️ Clear", use_container_width=True, key="clear_report"):
                for k in ("report_summary", "report_extracted_text", "report_filename", "report_patient", "report_language"):
                    st.session_state[k] = None
                st.rerun()

    with tips_col:
        st.markdown("""
        <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:12px; padding:1.1rem 1.4rem; height:100%;">
            <div class="section-label">Works best with</div>
            <div style="font-size:0.83rem; color:#475569; line-height:1.9;">
                ✅ Lab test reports (CBC, LFT, KFT)<br>
                ✅ Discharge summaries<br>
                ✅ Radiology reports (X-ray, MRI, CT)<br>
                ✅ Doctor consultation notes<br>
                ✅ Prescription documents
            </div>
            <div class="section-label" style="margin-top:0.85rem;">Limitations</div>
            <div style="font-size:0.83rem; color:#475569; line-height:1.9;">
                ⚠️ Scanned / image PDFs won't work<br>
                ⚠️ Handwritten text may not extract<br>
                ⚠️ Very long reports will be truncated
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 3 — Processing
    # ══════════════════════════════════════════════════════════════════════════
    if summarize_btn and uploaded_file is not None:
        patient = {
            "name":        patient_name.strip(),
            "age":         patient_age if patient_age > 0 else None,
            "gender":      patient_gender,
            "report_type": report_type,
            "report_date": str(report_date),
            "doctor":      referring_doctor.strip(),
            "lab":         lab_name.strip(),
            "notes":       patient_notes.strip(),
        }

        with st.spinner("📖 Extracting text from PDF…"):
            extracted_text = extract_text_from_uploaded_file(uploaded_file)

        if extracted_text.startswith("⚠️"):
            st.error(extracted_text)
            return

        char_count    = len(extracted_text)
        page_estimate = extracted_text.count("--- Page")
        st.markdown(f"""
        <div style="background:#F0FDF4; border:1px solid #BBF7D0; border-radius:8px;
                    padding:0.6rem 1rem; font-size:0.85rem; color:#15803D; margin:0.75rem 0;">
            ✅ Extracted <strong>{char_count:,}</strong> characters from
            <strong>{page_estimate}</strong> page(s) — ready for AI analysis
        </div>
        """, unsafe_allow_html=True)

        with st.spinner("🤖 AI is analysing the report…"):
            summary = _generate_summary(extracted_text, patient, language)

        if summary.startswith("⚠️"):
            st.error(summary)
            st.session_state.report_extracted_text = extracted_text
            st.session_state.report_filename       = uploaded_file.name
            st.session_state.report_patient        = patient
            st.session_state.report_language       = language
        else:
            st.session_state.report_summary        = summary
            st.session_state.report_extracted_text = extracted_text
            st.session_state.report_filename       = uploaded_file.name
            st.session_state.report_patient        = patient
            st.session_state.report_language       = language

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 4 — Results
    # ══════════════════════════════════════════════════════════════════════════
    if st.session_state.report_summary:
        st.markdown("<hr>", unsafe_allow_html=True)

        st.markdown("""
        <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:1rem;">
            <span style="background:#10B981; color:#fff; border-radius:50%; width:24px; height:24px;
                         display:flex; align-items:center; justify-content:center;
                         font-size:0.75rem; font-weight:700; flex-shrink:0;">3</span>
            <span style="font-weight:700; font-size:1rem; color:#0F172A;">Analysis Results</span>
        </div>
        """, unsafe_allow_html=True)

        # Patient info card (if present)
        p = st.session_state.report_patient or {}
        has_patient_info = any([
            p.get("name"), p.get("age"), p.get("gender") not in (None, "Select…", ""),
            p.get("report_type") not in (None, "Select report type…", ""),
            p.get("doctor"), p.get("lab"),
        ])

        if has_patient_info:
            fields = []
            if p.get("name"):        fields.append(("👤 Patient",    p["name"]))
            if p.get("age"):         fields.append(("🎂 Age",        f"{p['age']} years"))
            if p.get("gender") not in (None, "Select…", ""):
                                     fields.append(("⚧ Gender",     p["gender"]))
            if p.get("report_type") not in (None, "Select report type…", ""):
                                     fields.append(("🧪 Report",     p["report_type"]))
            if p.get("report_date"): fields.append(("📅 Date",       p["report_date"]))
            if p.get("doctor"):      fields.append(("🩺 Doctor",     p["doctor"]))
            if p.get("lab"):         fields.append(("🏥 Lab",        p["lab"]))
            if p.get("notes"):       fields.append(("📝 Notes",      p["notes"]))

            pills = "".join(
                f"""<div style="display:flex; flex-direction:column; background:#F8FAFC;
                               border:1px solid #E2E8F0; border-radius:10px;
                               padding:0.6rem 0.9rem; min-width:120px;">
                        <span style="font-size:0.68rem; color:#94A3B8; font-weight:600; text-transform:uppercase; letter-spacing:0.05em;">{label}</span>
                        <span style="font-size:0.88rem; font-weight:600; color:#0F172A; margin-top:0.15rem;">{value}</span>
                    </div>"""
                for label, value in fields
            )
            st.markdown(f"""
            <div style="display:flex; flex-wrap:wrap; gap:0.6rem; margin-bottom:1.25rem;">
                {pills}
            </div>
            """, unsafe_allow_html=True)

        # Summary card
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0.6rem;">
            <span style="font-size:1.1rem;">📋</span>
            <span style="font-weight:700; color:#0F172A;">AI Summary</span>
            <span style="font-size:0.78rem; color:#64748B; margin-left:0.2rem;">
                — {st.session_state.report_filename}
            </span>
        </div>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown(st.session_state.report_summary)

        # Action buttons
        dl_col, _ = st.columns([2, 3])
        with dl_col:
            saved_lang = st.session_state.get("report_language") or "Tamil"
            download_content = _create_download_text(
                st.session_state.report_filename or "report.pdf",
                st.session_state.report_extracted_text or "",
                st.session_state.report_summary,
                st.session_state.report_patient or {},
                saved_lang,
            )
            fname = (st.session_state.report_filename or "report.pdf").replace(".pdf", "_summary.txt")
            st.download_button(
                label="⬇️ Download Summary (.txt)",
                data=download_content.encode("utf-8"),
                file_name=fname,
                mime="text/plain",
                use_container_width=True,
            )

    # Raw text viewer
    if st.session_state.report_extracted_text:
        with st.expander("📄 View Extracted Raw Text", expanded=False):
            st.text_area(
                "raw",
                value=st.session_state.report_extracted_text,
                height=300,
                disabled=True,
                label_visibility="collapsed",
            )
