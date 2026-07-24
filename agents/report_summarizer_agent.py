"""
Medical Report Summarizer Agent — with Patient Details form
Improved UI: dark-theme sectioned summary card, copy/download buttons,
             colour-coded section headings, patient info pills on dark bg.
"""

import io
import datetime
import logging
import re
from datetime import date

import streamlit as st

from services.caregiver_service import share_report_with_caregivers
from utils import constants
from utils.i18n import t, get_lang
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


# ══════════════════════════════════════════════════════════════════════════════
# CSS — Report Summary Card (dark theme)
# ══════════════════════════════════════════════════════════════════════════════

_REPORT_CSS = """
<style>
/* ── Summary card wrapper ────────────────────────────────── */
.rs-card {
  background: #FFFFFF;
  border-left: 4px solid #2563EB;
  border-radius: 0 14px 14px 0;
  padding: 1.5rem 1.75rem;
  margin: 0.5rem 0 1rem 0;
  box-shadow: 0 2px 12px rgba(0,0,0,0.07), 0 1px 3px rgba(0,0,0,0.04);
  word-wrap: break-word;
  overflow-wrap: break-word;
  border: 1px solid #E5E7EB;
  border-left: 4px solid #2563EB;
}

/* ── Card title bar ──────────────────────────────────────── */
.rs-card-title {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 1.2rem;
  padding-bottom: 0.8rem;
  border-bottom: 1px solid #E5E7EB;
}
.rs-card-title-text {
  font-size: 1rem;
  font-weight: 700;
  color: #111827;
}
.rs-card-filename {
  font-size: 0.77rem;
  color: #6B7280;
  margin-left: auto;
}

/* ── Individual section ──────────────────────────────────── */
.rs-section {
  margin-bottom: 1.1rem;
  padding-bottom: 0.9rem;
  border-bottom: 1px solid #F3F4F6;
}
.rs-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

/* ── Section heading ─────────────────────────────────────── */
.rs-heading {
  font-size: 0.93rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  letter-spacing: 0.01em;
}

/* ── Section body text ───────────────────────────────────── */
.rs-body {
  font-size: 15px;
  line-height: 1.78;
  color: #374151;
  word-wrap: break-word;
  overflow-wrap: break-word;
}
.rs-body p  { margin: 0.25rem 0; }
.rs-body ul { padding-left: 1.2rem; margin: 0.3rem 0 0.5rem; }
.rs-body li { margin-bottom: 0.28rem; }
.rs-body br { display: block; content: ""; margin: 0.12rem 0; }

/* ── Colour tokens per section — adapted for white bg ────── */
.rs-c-patient   { color: #1D4ED8; }  /* blue      */
.rs-c-diagnosis { color: #15803D; }  /* green     */
.rs-c-abnormal  { color: #DC2626; }  /* red       */
.rs-c-meds      { color: #7C3AED; }  /* purple    */
.rs-c-tests     { color: #B45309; }  /* amber     */
.rs-c-recs      { color: #0369A1; }  /* sky       */
.rs-c-disclaimer{ color: #6B7280; }  /* slate     */

/* ── Inline table inside card ────────────────────────────── */
.rs-body table {
  border-collapse: collapse;
  width: 100%;
  margin: 0.5rem 0;
  font-size: 14px;
}
.rs-body th {
  background: #F3F4F6;
  color: #1D4ED8;
  padding: 0.45rem 0.7rem;
  text-align: left;
  font-weight: 700;
  border: 1px solid #E5E7EB;
}
.rs-body td {
  padding: 0.4rem 0.7rem;
  border: 1px solid #E5E7EB;
  color: #374151;
  background: #FFFFFF;
}
.rs-body tr:nth-child(even) td { background: #F9FAFB; }

/* ── Download/Copy action row ────────────────────────────── */
.rs-actions {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
  margin-top: 1rem;
  padding-top: 0.85rem;
  border-top: 1px solid #E5E7EB;
}

/* ── Action row: button text contrast overrides ──────────── */
/* Copy button — white bg → dark label                        */
.rs-actions .stButton > button {
  color: #111827 !important;
  -webkit-text-fill-color: #111827 !important;
}
.rs-actions .stButton > button:hover {
  color: #2563EB !important;
  -webkit-text-fill-color: #2563EB !important;
}
/* Download buttons — green bg → white label                  */
.rs-actions .stDownloadButton > button {
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
}
.rs-actions .stDownloadButton > button:hover {
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
}

/* ── Patient info pills ──────────────────────────────────── */
.rs-pill {
  display: flex;
  flex-direction: column;
  background: #F9FAFB;
  border: 1px solid #E5E7EB;
  border-radius: 10px;
  padding: 0.5rem 0.85rem;
  min-width: 110px;
  transition: border-color .15s;
}
.rs-pill:hover { border-color: #BFDBFE; }
.rs-pill-label {
  font-size: 0.63rem;
  color: #9CA3AF;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.rs-pill-value {
  font-size: 0.87rem;
  font-weight: 600;
  color: #111827;
  margin-top: 0.12rem;
}

/* ── Section label (reused) ──────────────────────────────── */
.section-label {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: #9CA3AF;
  margin-bottom: 0.4rem;
}
</style>
"""


# ══════════════════════════════════════════════════════════════════════════════
# SECTION MAP  —  heading keywords → (css colour class, display label)
# ══════════════════════════════════════════════════════════════════════════════

_SECTION_MAP = [
    (["patient information", "patient info",
      "நோயாளி தகவல்"],                          "rs-c-patient",    "📄", "Patient Information"),
    (["diagnosis", "key findings",
      "நோயறிதல்", "முக்கிய கண்டுபிடிப்புகள்"],  "rs-c-diagnosis",  "🩺", "Diagnosis / Key Findings"),
    (["abnormal findings", "abnormal",
      "அசாதாரண மதிப்புகள்"],                    "rs-c-abnormal",   "⚠️", "Abnormal Findings"),
    (["medications", "medication",
      "மருந்துகள்"],                             "rs-c-meds",       "💊", "Medications"),
    (["test results", "tests",
      "சோதனை முடிவுகள்"],                        "rs-c-tests",      "🧪", "Test Results"),
    (["recommendations", "follow",
      "பரிந்துரைகள்"],                           "rs-c-recs",       "📋", "Recommendations"),
    (["disclaimer", "முன்னெச்சரிக்கை"],           "rs-c-disclaimer", "📌", "Disclaimer"),
]


def _classify(heading: str) -> tuple:
    """Return (css_colour_class, emoji, label) for a section heading."""
    h = heading.lower().strip()
    for keywords, css_cls, emoji, label in _SECTION_MAP:
        if any(kw in h for kw in keywords):
            return css_cls, emoji, label
    # Fallback — use raw heading text, no colour class
    clean = re.sub(r"[📄🩺⚠️💊🧪📋📌]\s*", "", heading).strip()
    return "rs-c-recs", "📋", clean


# ══════════════════════════════════════════════════════════════════════════════
# INLINE MARKDOWN → HTML
# ══════════════════════════════════════════════════════════════════════════════

def _inline_md(text: str) -> str:
    """Convert inline bold, italic, code markdown to HTML."""
    # Bold **text** or __text__  — #1D4ED8 (blue) readable on white card bg
    text = re.sub(r"\*\*(.+?)\*\*",
                  r"<strong style='color:#1D4ED8;'>\1</strong>", text)
    text = re.sub(r"__(.+?)__",
                  r"<strong style='color:#1D4ED8;'>\1</strong>", text)
    # Italic *text* or _text_  — #6D28D9 (violet) readable on white card bg
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)",
                  r"<em style='color:#6D28D9;'>\1</em>", text)
    text = re.sub(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)",
                  r"<em style='color:#6D28D9;'>\1</em>", text)
    # Inline code `text`
    text = re.sub(
        r"`(.+?)`",
        r"<code style='background:#FFFFFF;color:#34D399;padding:0.1rem 0.35rem;"
        r"border-radius:4px;font-size:0.87em;'>\1</code>",
        text,
    )
    return text


def _md_body_to_html(text: str) -> str:
    """
    Convert a markdown body (bullet lists, numbered lists, tables,
    bold, italic, horizontal rules, paragraphs) to safe HTML for
    display inside the .rs-body div.
    """
    lines  = text.splitlines()
    out    = []
    in_ul  = False
    in_ol  = False
    # Simple table detection state
    table_rows: list[str] = []

    def flush_list():
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    def flush_table():
        nonlocal table_rows
        if not table_rows:
            return
        html = "<table>"
        for ri, row in enumerate(table_rows):
            cells = [c.strip() for c in row.strip("|").split("|")]
            # Skip separator rows (---|---|---)
            if all(re.match(r"^:?-+:?$", c.strip()) for c in cells if c.strip()):
                continue
            tag = "th" if ri == 0 else "td"
            html += "<tr>" + "".join(
                f"<{tag}>{_inline_md(c)}</{tag}>" for c in cells
            ) + "</tr>"
        html += "</table>"
        out.append(html)
        table_rows.clear()

    for line in lines:
        raw = line.rstrip()
        stripped = raw.strip()

        # Horizontal rule
        if stripped in ("---", "***", "___"):
            flush_list()
            flush_table()
            out.append(
                '<hr style="border:none;border-top:1px solid #E5E7EB;margin:0.55rem 0;">'
            )
            continue

        # Table row (contains at least one |)
        if "|" in stripped and stripped.startswith("|"):
            flush_list()
            table_rows.append(stripped)
            continue
        else:
            flush_table()

        # Bullet list
        if stripped.startswith("- ") or stripped.startswith("* "):
            if in_ol:
                out.append("</ol>")
                in_ol = False
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{_inline_md(stripped[2:])}</li>")
            continue

        # Numbered list
        num_m = re.match(r"^(\d+)\.\s+(.+)", stripped)
        if num_m:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if not in_ol:
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{_inline_md(num_m.group(2))}</li>")
            continue

        flush_list()

        if not stripped:
            out.append("<br>")
            continue

        # Plain paragraph
        out.append(f"<p>{_inline_md(stripped)}</p>")

    flush_list()
    flush_table()
    return "\n".join(out)


# ══════════════════════════════════════════════════════════════════════════════
# PDF DOWNLOAD HELPER
# ══════════════════════════════════════════════════════════════════════════════

def _make_pdf_bytes(summary: str, filename: str) -> bytes | None:
    """Generate PDF bytes via fpdf2 if available, else return None."""
    try:
        from fpdf import FPDF  # type: ignore
    except ImportError:
        return None

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, "Medical Report Summary", ln=True, align="C")

    # Sub-title
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 116, 139)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    pdf.cell(0, 6, f"AI Health Assistant  |  {filename}  |  {ts}", ln=True, align="C")
    pdf.ln(4)
    pdf.set_draw_color(59, 130, 246)
    pdf.set_line_width(0.8)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(30, 41, 59)
    pdf.set_line_width(0.2)
    pdf.set_draw_color(100, 116, 139)

    for line in summary.splitlines():
        s = line.strip()
        if not s:
            pdf.ln(3)
            continue
        if re.match(r"^#{1,3}\s+", s):
            heading = re.sub(r"^#{1,3}\s+", "", s)
            # Strip emoji for PDF (fpdf2 core fonts don't support them)
            heading_clean = re.sub(
                r"[\U00010000-\U0010ffff]|[\u2600-\u27BF]", "", heading
            ).strip()
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(37, 99, 235)
            pdf.multi_cell(0, 7, heading_clean)
            pdf.set_font("Helvetica", "", 11)
            pdf.set_text_color(30, 41, 59)
        elif s.startswith("- ") or s.startswith("* "):
            bullet = re.sub(r"\*\*(.+?)\*\*", r"\1", s[2:])
            bullet = re.sub(r"\*(.+?)\*", r"\1", bullet)
            pdf.multi_cell(0, 6, f"  \u2022 {bullet}")
        elif re.match(r"^---+$", s):
            pdf.set_draw_color(100, 116, 139)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)
        elif "|" in s and s.startswith("|"):
            # Minimal table row rendering
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(re.match(r"^:?-+:?$", c) for c in cells if c):
                continue
            row_text = "  |  ".join(cells)
            clean = re.sub(r"\*\*(.+?)\*\*", r"\1", row_text)
            pdf.multi_cell(0, 6, clean)
        else:
            clean = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
            clean = re.sub(r"\*(.+?)\*",     r"\1", clean)
            pdf.multi_cell(0, 6, clean)

    return bytes(pdf.output())


# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY CARD RENDERER
# ══════════════════════════════════════════════════════════════════════════════

def _render_summary_card(summary: str, filename: str) -> None:
    """
    Parse the LLM summary (markdown with ## headings) and render it
    as a styled dark-theme sectioned card, then show Copy / Download
    action buttons underneath.
    """
    st.markdown(_REPORT_CSS, unsafe_allow_html=True)

    # ── Split on ## or ### headings ───────────────────────────────────────
    heading_re = re.compile(r"(?m)^#{1,3}\s+(.+)")
    headings   = heading_re.findall(summary)
    parts      = heading_re.split(summary)
    # parts[0] is any text before the first heading (usually empty)
    # then alternates: heading_text, body_text, heading_text, body_text …

    sections_html = ""

    if headings and len(parts) >= 3:
        # parts layout: [pre, h1, body1, h2, body2, ...]
        body_parts = parts[2::2]   # every other part starting at index 2
        for heading, body in zip(headings, body_parts):
            css_cls, emoji, label = _classify(heading)
            body_html = _md_body_to_html(body.strip())
            sections_html += f"""
            <div class="rs-section">
              <div class="rs-heading {css_cls}">{emoji}&nbsp;{label}</div>
              <div class="rs-body">{body_html}</div>
            </div>"""
    else:
        # Fallback: no headings detected — render everything as one body
        sections_html = (
            f'<div class="rs-section">'
            f'<div class="rs-body">{_md_body_to_html(summary)}</div>'
            f"</div>"
        )

    fn_display = filename or "report.pdf"
    card_html = f"""
    <div class="rs-card">
      <div class="rs-card-title">
        <span style="font-size:1.3rem;">📋</span>
        <span class="rs-card-title-text">AI Medical Report Summary</span>
        <span class="rs-card-filename">📄 {fn_display}</span>
      </div>
      {sections_html}
    </div>"""

    st.markdown(card_html, unsafe_allow_html=True)

    # ── Action buttons ────────────────────────────────────────────────────
    st.markdown('<div class="rs-actions">', unsafe_allow_html=True)
    btn_copy, btn_txt, btn_pdf, _ = st.columns([1.3, 1.5, 1.6, 3])

    with btn_copy:
        if st.button("📋 Copy", key="rs_copy_btn", use_container_width=True,
                     help="Copy summary to clipboard"):
            escaped = summary.replace("`", "\\`").replace("$", "\\$")
            st.components.v1.html(
                f"<script>navigator.clipboard.writeText(`{escaped}`)"
                f".then(()=>{{console.log('copied')}});"
                f"</script>",
                height=0,
            )
            st.toast("✅ Summary copied to clipboard!", icon="📋")

    with btn_txt:
        ts   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sep  = "=" * 60
        txt_content = (
            f"MEDICAL REPORT SUMMARY\n{sep}\n"
            f"File      : {fn_display}\n"
            f"Generated : {ts}\n"
            f"{sep}\n\n"
            f"{summary}"
        )
        st.download_button(
            label="📄 Download TXT",
            data=txt_content.encode("utf-8"),
            file_name=fn_display.replace(".pdf", "_summary.txt"),
            mime="text/plain",
            key="rs_dl_txt",
            use_container_width=True,
            help="Download as plain text file",
        )

    with btn_pdf:
        pdf_bytes = _make_pdf_bytes(summary, fn_display)
        if pdf_bytes:
            st.download_button(
                label="📥 Download PDF",
                data=pdf_bytes,
                file_name=fn_display.replace(".pdf", "_summary.pdf"),
                mime="application/pdf",
                key="rs_dl_pdf",
                use_container_width=True,
                help="Download formatted PDF summary",
            )
        else:
            st.markdown(
                "<small style='color:#6B7280;font-size:0.75rem;line-height:2.2;'>"
                "💡 Install <code>fpdf2</code> for PDF export</small>",
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DOMAIN HELPERS  (unchanged logic, kept here for self-containment)
# ══════════════════════════════════════════════════════════════════════════════

def _truncate_for_llm(text: str) -> tuple[str, bool]:
    if len(text) <= MAX_TEXT_CHARS:
        return text, False
    truncated = text[:MAX_TEXT_CHARS]
    last_period = truncated.rfind(".")
    if last_period > MAX_TEXT_CHARS * 0.8:
        truncated = truncated[: last_period + 1]
    return truncated + "\n\n[... Report truncated for processing ...]", True


def _build_patient_context(patient: dict) -> str:
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
            "\n\n*Note: The report was truncated due to length. "
            "Summary covers the first portion.*"
            if was_truncated else ""
        )
        system_prompt = constants.REPORT_SUMMARIZER_SYSTEM_PROMPT

    patient_ctx = _build_patient_context(patient)

    if language == "Tamil":
        patient_section = (
            f"\n\nநோயாளி விவரங்கள் (PATIENT CONTEXT):\n{patient_ctx}\n\n"
            "நோயாளியின் வயது, பாலினம் மற்றும் குறிப்புகளை கணக்கில் எடுத்து பகுப்பாய்வு செய்யவும்."
            if patient_ctx else ""
        )
        prompt = (
            "கீழே கொடுக்கப்பட்டுள்ள மருத்துவ அறிக்கையை பகுப்பாய்வு செய்து "
            "தமிழில் சுருக்கமாக வழங்கவும்."
            f"{patient_section}\n\n"
            f"அறிக்கை உரை (REPORT TEXT):\n---\n{text_for_llm}\n---"
        )
    else:
        patient_section = (
            f"\n\nPATIENT CONTEXT:\n{patient_ctx}\n\n"
            "Please tailor your analysis considering the patient's age, gender, "
            "and any notes provided."
            if patient_ctx else ""
        )
        prompt = (
            "Please analyze and summarize the following medical report text."
            f"{patient_section}\n\n"
            f"REPORT TEXT:\n---\n{text_for_llm}\n---"
        )

    return simple_query(system_prompt, prompt) + truncation_note


def _create_download_text(
    filename: str, extracted_text: str, summary: str,
    patient: dict, language: str = "Tamil",
) -> str:
    ts  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sep = "=" * 60
    patient_ctx   = _build_patient_context(patient)
    patient_block = f"\nPATIENT DETAILS\n{sep}\n{patient_ctx}\n\n" if patient_ctx else ""
    disclaimer = (
        constants.REPORT_DISCLAIMER_TAMIL if language == "Tamil"
        else constants.REPORT_DISCLAIMER
    )
    summary_label    = "AI சுருக்கம் (AI SUMMARY)" if language == "Tamil" else "AI SUMMARY"
    disclaimer_label = "முன்னெச்சரிக்கை (DISCLAIMER)" if language == "Tamil" else "DISCLAIMER"
    raw_label        = (
        "எடுக்கப்பட்ட உரை — அசல் (EXTRACTED TEXT — Original)"
        if language == "Tamil" else "EXTRACTED TEXT (Original)"
    )
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


def _share_with_caregiver() -> None:
    """Share the current AI summary with all caregivers linked to the patient."""
    p       = st.session_state.get("report_patient") or {}
    summary = st.session_state.get("report_summary") or ""
    patient_name = p.get("name", "").strip()

    if not patient_name:
        st.warning("⚠️ No patient name found. Please fill in Patient Name before sharing.")
        return
    if not summary:
        st.warning("⚠️ No summary available. Please analyse a report first.")
        return

    report_date = str(p.get("report_date", datetime.datetime.now().strftime("%Y-%m-%d")))
    doctor_name = p.get("doctor", "")

    key_findings = ""
    followup     = ""
    for line in summary.splitlines():
        stripped = line.strip()
        if re.search(r"key findings|முக்கிய", stripped, re.I):
            key_findings = ""
        elif re.search(r"recommendations|பரிந்துரை", stripped, re.I):
            followup = ""
        elif key_findings is not None and stripped.startswith("- "):
            key_findings += stripped + "\n"
        elif followup is not None and stripped.startswith("- "):
            followup += stripped + "\n"

    with st.spinner("📤 Sending report to caregivers…"):
        results = share_report_with_caregivers(
            patient_name=patient_name,
            report_date=report_date,
            doctor_name=doctor_name,
            ai_summary=summary,
            key_findings=key_findings.strip(),
            followup=followup.strip(),
        )

    if not results:
        st.info(
            f"ℹ️ No active caregivers found for **{patient_name}**. "
            "Add a caregiver in 👨‍👩‍👧 Caregiver Management."
        )
        return

    all_ok        = all(r["success"] for r in results)
    banner_color  = "rgba(16,185,129,0.12)" if all_ok else "rgba(245,158,11,0.12)"
    banner_border = "#10B981" if all_ok else "#F59E0B"
    banner_icon   = "✅" if all_ok else "⚠️"
    st.markdown(
        f"<div style='background:{banner_color};border-left:4px solid {banner_border};"
        f"border-radius:10px;padding:0.85rem 1.1rem;font-size:0.88rem;"
        f"color:#F1F5F9;margin-top:0.5rem;'>"
        f"<b>{banner_icon} Report shared with {len(results)} caregiver(s)</b></div>",
        unsafe_allow_html=True,
    )
    for r in results:
        icon = "✅" if r["success"] else "❌"
        st.markdown(
            f"<div style='font-size:0.82rem;color:#6B7280;margin-top:0.3rem;'>"
            f"{icon} <b>{r['caregiver_name']}</b> — {r['email']}: {r['message']}</div>",
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER
# ══════════════════════════════════════════════════════════════════════════════

def _save_summary_to_ehr(
    summary: str,
    raw_text: str,
    filename: str,
    patient: dict,
    language: str = "English",
) -> None:
    """Save an AI-generated report summary directly to the EHR Patient Records."""
    try:
        from database import database as db
        from authentication.session import get_current_user

        user = get_current_user()
        if not user:
            st.warning("⚠️ You must be logged in to save to Patient Records.")
            return

        uid = user.get("id")
        ehr_patient = db.get_patient_by_user(uid)
        if not ehr_patient:
            pid = db.create_patient(
                full_name=patient.get("name") or user.get("full_name", "Patient"),
                user_id=uid,
                email=user.get("email", ""),
                blood_group=user.get("blood_group", ""),
                age=patient.get("age"),
                gender=patient.get("gender", ""),
            )
        else:
            pid = ehr_patient["id"]

        report_type = patient.get("report_type", "Other") or "Other"
        if report_type in ("Select report type…", ""):
            report_type = "Other"

        report_id = db.create_ehr_report(
            patient_id=pid,
            patient_name=patient.get("name") or user.get("full_name", "Patient"),
            report_type=report_type,
            report_date=str(patient.get("report_date", "")),
            lab_name=patient.get("lab", ""),
            doctor_name=patient.get("doctor", ""),
            file_name=filename,
            ai_summary=summary,
            raw_text=raw_text,
            diagnosis="",
            risk_level="Normal",
            is_normal=True,
            tags=f"language:{language}",
        )

        st.success(
            f"✅ Report saved to **📁 Patient Records** (ID #{report_id}). "
            "Go to **Patient Records → Reports** tab to view it."
        )
        st.session_state["ehr_jump_to_records"] = True

    except Exception as exc:
        st.error(f"Failed to save to Patient Records: {exc}")


def render() -> None:
    lang = get_lang(st.session_state)
    st.markdown(_REPORT_CSS, unsafe_allow_html=True)

    # ── Page header ───────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="page-header">
        <div style="display:flex; align-items:center; gap:1rem;">
            <span style="font-size:2.2rem;">📄</span>
            <div>
                <h1 style="margin:0;">{t("report_title", lang)}</h1>
                <p style="margin:0;color:#6B7280;">{t("report_subtitle", lang)}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Session state ─────────────────────────────────────────────────────────
    for key in ("report_summary", "report_extracted_text",
                "report_filename", "report_patient", "report_language"):
        if key not in st.session_state:
            st.session_state[key] = None

    # ── Language selector ─────────────────────────────────────────────────────
    lang_col, _ = st.columns([2, 3])
    with lang_col:
        lang_choice = st.radio(
            f"🌐 {t('output_language', lang)} / வெளியீட்டு மொழி",
            options=["Tamil (தமிழ்)", "English"],
            index=0,
            horizontal=True,
            key="lang_selector",
        )
    language = "Tamil" if lang_choice.startswith("Tamil") else "English"

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── Disclaimer ────────────────────────────────────────────────────────────
    if language == "Tamil":
        st.markdown("""
        <div style="background:rgba(245,158,11,0.10);border-left:4px solid #F59E0B;
                    border-radius:10px;padding:0.85rem 1.1rem;margin-bottom:1.5rem;
                    font-size:0.85rem;color:#FCD34D;">
            <strong>⚠️ முன்னெச்சரிக்கை:</strong> இந்த AI சுருக்கம் தகவல் நோக்கங்களுக்காக மட்டுமே.
            இது தொழில்முறை மருத்துவ விளக்கத்திற்கு மாற்றாகாது. உங்கள் மருத்துவரிடம் விவாதிக்கவும்.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background:#FFFBEB;border-left:4px solid #D97706;
                    border-radius:10px;padding:0.85rem 1.1rem;margin-bottom:1.5rem;
                    font-size:0.85rem;color:#92400E;">
            {t("medical_disclaimer", lang)}
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — Patient Details
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.75rem;">
        <span style="background:#3B82F6;color:#fff;border-radius:50%;width:24px;height:24px;
                     display:flex;align-items:center;justify-content:center;
                     font-size:0.75rem;font-weight:700;flex-shrink:0;">1</span>
        <span style="font-weight:700;font-size:1rem;color:#F1F5F9;">{t("patient_details", lang)}</span>
        <span style="font-size:0.78rem;color:#6B7280;margin-left:0.25rem;">
            ({t("patient_details_hint", lang)})</span>
    </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        r1c1, r1c2, r1c3 = st.columns(3)
        with r1c1:
            patient_name = st.text_input(
                t("patient_name", lang),
                placeholder=t("patient_name_placeholder", lang),
                key="pt_name",
            )
        with r1c2:
            patient_age = st.number_input(
                t("age_years", lang),
                min_value=0, max_value=120, value=0, step=1,
                key="pt_age",
            )
        with r1c3:
            patient_gender = st.selectbox(
                t("gender", lang), GENDERS, key="pt_gender",
            )

        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1:
            report_type = st.selectbox(
                t("report_type", lang), REPORT_TYPES, key="pt_report_type",
            )
        with r2c2:
            report_date = st.date_input(
                t("report_date", lang),
                value=date.today(), max_value=date.today(),
                key="pt_report_date",
            )
        with r2c3:
            referring_doctor = st.text_input(
                t("referring_doctor", lang),
                placeholder=t("doctor_name_placeholder", lang),
                key="pt_doctor",
            )

        r3c1, r3c2 = st.columns(2)
        with r3c1:
            lab_name = st.text_input(
                t("lab_hospital", lang),
                placeholder=t("lab_placeholder", lang),
                key="pt_lab",
            )
        with r3c2:
            patient_notes = st.text_input(
                t("symptoms_notes", lang),
                placeholder="e.g. fatigue, high BP, follow-up after 3 months",
                key="pt_notes",
            )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — Upload Report
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.75rem;">
        <span style="background:#3B82F6;color:#fff;border-radius:50%;width:24px;height:24px;
                     display:flex;align-items:center;justify-content:center;
                     font-size:0.75rem;font-weight:700;flex-shrink:0;">2</span>
        <span style="font-weight:700;font-size:1rem;color:#F1F5F9;">{t("upload_report", lang)}</span>
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
            <div style="text-align:center;padding:0.4rem 0 0.75rem;
                        color:#6B7280;font-size:0.83rem;">
                📎 Drag &amp; drop a PDF here, or click above to browse
            </div>
            """, unsafe_allow_html=True)

        action_col, clear_col = st.columns([3, 1])
        with action_col:
            summarize_btn = st.button(
                t("analyse_report", lang),
                type="primary",
                disabled=uploaded_file is None,
                use_container_width=True,
            )
        with clear_col:
            if st.button(t("clear", lang), use_container_width=True,
                         key="clear_report"):
                for k in ("report_summary", "report_extracted_text",
                          "report_filename", "report_patient", "report_language"):
                    st.session_state[k] = None
                st.rerun()

    with tips_col:
        st.markdown("""
        <div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;
                    padding:1.1rem 1.4rem;height:100%;">
            <div class="section-label">Works best with</div>
            <div style="font-size:0.83rem;color:#6B7280;line-height:1.9;">
                ✅ Lab test reports (CBC, LFT, KFT)<br>
                ✅ Discharge summaries<br>
                ✅ Radiology reports (X-ray, MRI, CT)<br>
                ✅ Doctor consultation notes<br>
                ✅ Prescription documents
            </div>
            <div class="section-label" style="margin-top:0.85rem;">Limitations</div>
            <div style="font-size:0.83rem;color:#6B7280;line-height:1.9;">
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
        <div style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.25);
                    border-radius:8px;padding:0.6rem 1rem;font-size:0.85rem;
                    color:#34D399;margin:0.75rem 0;">
            ✅ Extracted <strong>{char_count:,}</strong> characters from
            <strong>{page_estimate}</strong> page(s) — ready for AI analysis
        </div>
        """, unsafe_allow_html=True)

        # Typing / progress animation while AI works
        prog_placeholder = st.empty()
        with prog_placeholder.container():
            st.markdown("""
            <div style="display:flex;align-items:center;gap:0.75rem;
                        background:#FFFFFF;border:1px solid #E5E7EB;
                        border-radius:10px;padding:1rem 1.25rem;margin:0.5rem 0;">
              <div style="display:inline-flex;gap:5px;">
                <span style="width:8px;height:8px;border-radius:50%;background:#3B82F6;
                             animation:typingBounce 1.2s infinite ease-in-out;
                             display:inline-block;"></span>
                <span style="width:8px;height:8px;border-radius:50%;background:#3B82F6;
                             animation:typingBounce 1.2s 0.2s infinite ease-in-out;
                             display:inline-block;"></span>
                <span style="width:8px;height:8px;border-radius:50%;background:#3B82F6;
                             animation:typingBounce 1.2s 0.4s infinite ease-in-out;
                             display:inline-block;"></span>
              </div>
              <span style="font-size:0.92rem;color:#6B7280;font-style:italic;">
                🤖 Analyzing medical report…</span>
            </div>
            <style>
            @keyframes typingBounce {
              0%,60%,100%{transform:translateY(0);opacity:0.5;}
              30%{transform:translateY(-7px);background:#60A5FA;opacity:1;}
            }
            </style>
            """, unsafe_allow_html=True)

        with st.spinner(""):
            summary = _generate_summary(extracted_text, patient, language)

        prog_placeholder.empty()

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
        st.markdown(
            "<hr style='border:none;border-top:1px solid #FFFFFF;margin:1.5rem 0;'>",
            unsafe_allow_html=True,
        )

        # ── Section heading ───────────────────────────────────────────────
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:1rem;">
            <span style="background:#10B981;color:#fff;border-radius:50%;width:24px;height:24px;
                         display:flex;align-items:center;justify-content:center;
                         font-size:0.75rem;font-weight:700;flex-shrink:0;">3</span>
            <span style="font-weight:700;font-size:1rem;color:#F1F5F9;">
                {t("analysis_results", lang)}</span>
        </div>
        """, unsafe_allow_html=True)

        # ── Patient info pills — DARK THEME ───────────────────────────────
        p = st.session_state.report_patient or {}
        pill_fields = []
        if p.get("name"):
            pill_fields.append(("👤 Patient",  p["name"]))
        if p.get("age"):
            pill_fields.append(("🎂 Age",       f"{p['age']} yrs"))
        if p.get("gender") not in (None, "Select…", ""):
            pill_fields.append(("⚧ Gender",    p["gender"]))
        if p.get("report_type") not in (None, "Select report type…", ""):
            pill_fields.append(("🧪 Report",    p["report_type"]))
        if p.get("report_date"):
            pill_fields.append(("📅 Date",      str(p["report_date"])))
        if p.get("doctor"):
            pill_fields.append(("🩺 Doctor",    p["doctor"]))
        if p.get("lab"):
            pill_fields.append(("🏥 Lab",       p["lab"]))
        if p.get("notes"):
            pill_fields.append(("📝 Notes",     p["notes"]))

        if pill_fields:
            pills_html = "".join(
                f"""<div class="rs-pill">
                      <span class="rs-pill-label">{label}</span>
                      <span class="rs-pill-value">{value}</span>
                    </div>"""
                for label, value in pill_fields
            )
            st.markdown(
                f'<div style="display:flex;flex-wrap:wrap;gap:0.6rem;'
                f'margin-bottom:1.25rem;">{pills_html}</div>',
                unsafe_allow_html=True,
            )

        # ── Styled summary card with sections ─────────────────────────────
        _render_summary_card(
            st.session_state.report_summary,
            st.session_state.report_filename or "report.pdf",
        )

        # ── Share with caregiver button ───────────────────────────────────
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        # ── Action row: Share + Save to EHR ──────────────────────────────
        act_col1, act_col2 = st.columns([1, 1])
        with act_col1:
            if st.button(t("share_with_caregiver", lang),
                         use_container_width=True, key="share_caregiver_btn"):
                _share_with_caregiver()

        with act_col2:
            if st.button("📁 Save to Patient Records",
                         use_container_width=True, key="save_to_ehr_btn",
                         help="Save this report to your Electronic Health Record (not in AI chat)"):
                _save_summary_to_ehr(
                    summary=st.session_state.report_summary,
                    raw_text=st.session_state.report_extracted_text or "",
                    filename=st.session_state.report_filename or "report.pdf",
                    patient=st.session_state.report_patient or {},
                    language=st.session_state.get("report_language") or "English",
                )

    # ── Raw text viewer ───────────────────────────────────────────────────────
    if st.session_state.report_extracted_text:
        with st.expander(t("view_raw_text", lang), expanded=False):
            st.text_area(
                "raw",
                value=st.session_state.report_extracted_text,
                height=300,
                disabled=True,
                label_visibility="collapsed",
            )
