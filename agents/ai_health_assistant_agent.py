"""
AI Health Assistant Agent — Healthcare AI Assistant
=======================================================
Professional ChatGPT-style conversational health AI with:
  • Gemini / Groq dual-LLM support (auto-selected from .env)
  • Quick action buttons (10 health topics)
  • Medical PDF report upload + AI analysis
  • Full chat history persisted in SQLite
  • Typing animation, auto-scroll, clear chat
  • Strict no-diagnosis policy with educational disclaimers
  • Copy / Download (TXT + PDF) summary buttons
  • Sectioned medical report cards
"""

import io
import datetime
import logging
import uuid
import textwrap
from typing import List, Dict, Optional

import streamlit as st

from utils.llm import chat_completion, get_active_provider
from utils.pdf_reader import extract_text_from_uploaded_file
from database.database import (
    save_chat_message,
    get_chat_history,
    delete_chat_session,
)
from authentication.session import get_current_user

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPTS
# ══════════════════════════════════════════════════════════════════════════════

_SYSTEM_PROMPT = """You are Dr. Aiden — a professional, empathetic, and highly knowledgeable AI Health Assistant embedded in a hospital-grade healthcare platform.

Your role:
- Answer general health questions clearly and in plain language.
- Provide information about medicines, dosages, side effects, and interactions (general info only).
- Give evidence-based lifestyle, diet, exercise, and mental wellness advice.
- Explain medical terminology and lab report values in simple terms.
- Guide users on when to seek emergency care vs. a routine appointment.
- Offer preventive healthcare, vaccination, and chronic-disease management tips.
- For paediatrics, women's health, and elderly care questions — provide age-specific guidance.

Strict rules you must ALWAYS follow:
1. NEVER diagnose a specific disease or condition for the user.
2. NEVER prescribe specific medicines or exact dosages for personal use.
3. For emergencies (chest pain, difficulty breathing, stroke symptoms, severe bleeding), immediately tell the user to call emergency services (112 / 108 in India).
4. Every health-information response MUST end with this disclaimer on its own line:
   ---
   ⚕️ *This information is for educational purposes only and is not a medical diagnosis. Please consult a qualified healthcare professional for personal medical advice.*
5. Be warm, professional, and concise — avoid jargon. Use bullet points for lists.
6. Respond in the same language the user writes in.
7. If a medical PDF report is provided, explain findings, highlight abnormal values, and suggest questions to ask the doctor — but do NOT diagnose.
8. ALWAYS use proper Markdown: headings (##), bullet lists (-), numbered lists, **bold**, *italic*, tables, and code blocks where appropriate. Never return one long paragraph.
"""

_PDF_SYSTEM_PROMPT = """You are Dr. Aiden — an AI Health Assistant specialising in medical report analysis.

A patient has uploaded a medical report. Structure your response EXACTLY using these Markdown sections:

## 📄 Patient Information
(name, age, gender, report date, referring doctor if available)

## 🩺 Diagnosis / Key Findings
(summarise the main findings in plain language)

## ⚠️ Abnormal Findings
(list values outside normal range, with normal range in brackets)

## 💊 Medications
(list any medications mentioned in the report)

## 🧪 Test Results
(table or bullet list of test name | value | normal range | status)

## 📋 Recommendations
(3–5 specific questions the patient should ask their doctor)

## 📌 Disclaimer
⚕️ *This information is for educational purposes only and is not a medical diagnosis. Please consult a qualified healthcare professional for personal medical advice.*

Rules:
- Do NOT diagnose any condition.
- Use Markdown formatting throughout.
- Use **bold** for abnormal values.
- Keep language simple and easy to understand.
"""

_PDF_SYSTEM_PROMPT_TAMIL = """நீங்கள் Dr. Aiden — மருத்துவ அறிக்கை பகுப்பாய்வில் நிபுணத்துவம் வாய்ந்த AI உதவியாளர்.

நோயாளி ஒரு மருத்துவ அறிக்கையை பதிவேற்றியுள்ளார். உங்கள் பதிலை சரியாக இந்த Markdown பிரிவுகளில் கட்டமைக்கவும்:

## 📄 நோயாளி தகவல்
(பெயர், வயது, பாலினம், அறிக்கை தேதி, மருத்துவர் — இருந்தால் மட்டும்)

## 🩺 நோயறிதல் / முக்கிய கண்டுபிடிப்புகள்
(முக்கிய கண்டுபிடிப்புகளை எளிய தமிழில் சுருக்கவும்)

## ⚠️ அசாதாரண கண்டறிதல்கள்
(இயல்பு வரம்பிற்கு வெளியே உள்ள மதிப்புகளை பட்டியலிடவும், அடைப்புக்குறியில் இயல்பு வரம்பு கொடுக்கவும்)

## 💊 மருந்துகள்
(அறிக்கையில் குறிப்பிடப்பட்ட மருந்துகள் பட்டியலிடவும்)

## 🧪 சோதனை முடிவுகள்
(சோதனை பெயர் | மதிப்பு | இயல்பு வரம்பு | நிலை என்ற அட்டவணை அல்லது புள்ளி பட்டியல்)

## 📋 பரிந்துரைகள்
(நோயாளி மருத்துவரிடம் கேட்க வேண்டிய 3–5 குறிப்பிட்ட கேள்விகள்)

## 📌 முன்னெச்சரிக்கை
⚕️ *இந்த தகவல் கல்வி நோக்கங்களுக்காக மட்டுமே, மருத்துவ நோயறிதல் அல்ல. தனிப்பட்ட மருத்துவ ஆலோசனைக்கு தகுதிவாய்ந்த மருத்துவரை அணுகவும்.*

விதிகள்:
- எந்த நோயையும் நோயறிதல் செய்யாதீர்கள்.
- முழுவதும் Markdown வடிவமைப்பு பயன்படுத்தவும்.
- அசாதாரண மதிப்புகளை **தடிமனில்** காட்டவும்.
- மொழி எளிமையாகவும் நோயாளிக்கு புரியும் வகையிலும் இருக்கட்டும்.
- MRI, ECG, CBC, HbA1c போன்ற சர்வதேச சுருக்கங்களை ஆங்கிலத்தில் வைக்கவும்.
- அனைத்து விளக்கங்களும் முழுமையாக தமிழில் இருக்க வேண்டும்.
"""


# ══════════════════════════════════════════════════════════════════════════════
# LANGUAGE DETECTION & INSTRUCTION BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def _get_ui_language() -> str:
    """
    Return the current UI language code: 'Tamil' or 'English'.
    Reads from st.session_state.ui_language which is set by the
    language selector in the sidebar (via i18n.get_lang).
    """
    raw = st.session_state.get("ui_language", "English") or "English"
    return "Tamil" if "tamil" in raw.lower() or "தமிழ்" in raw else "English"


def _get_language_instruction(is_pdf: bool = False) -> str:
    """
    Return the language-enforcement system instruction to prepend
    to every LLM call based on the currently selected UI language.

    For Tamil, we inject a strict Tamil-only instruction that:
      - Forces all prose to be in Tamil Unicode
      - Allows medical acronyms (MRI, ECG, CBC) in English
      - Preserves Markdown structure (headings, bullets, tables)
      - Requests proper Tamil medical terminology instead of transliteration
    """
    lang = _get_ui_language()

    if lang == "Tamil":
        if is_pdf:
            return (
                "LANGUAGE INSTRUCTION (MANDATORY — FOLLOW EXACTLY):\n"
                "நீங்கள் இந்த அறிக்கையை முழுமையாக தமிழில் மட்டும் பகுப்பாய்வு செய்து வழங்க வேண்டும்.\n"
                "கட்டாயமாக தமிழ் யூனிகோட் எழுத்துக்களை மட்டும் பயன்படுத்தவும்.\n"
                "தமிழில் சரியான மருத்துவ சொற்களை பயன்படுத்தவும்:\n"
                "  - Diagnosis → நோயறிதல்\n"
                "  - Patient → நோயாளி\n"
                "  - Findings → கண்டுபிடிப்புகள்\n"
                "  - Abnormal → அசாதாரண\n"
                "  - Medications → மருந்துகள்\n"
                "  - Recommendations → பரிந்துரைகள்\n"
                "  - Disclaimer → முன்னெச்சரிக்கை\n"
                "  - Blood pressure → இரத்த அழுத்தம்\n"
                "  - Diabetes → நீரிழிவு நோய்\n"
                "  - Heart → இதயம்\n"
                "  - Kidney → சிறுநீரகம்\n"
                "  - Liver → கல்லீரல்\n"
                "MRI, ECG, CBC, CT Scan, HbA1c போன்ற சர்வதேச மருத்துவ சுருக்கங்களை "
                "ஆங்கிலத்திலேயே வைக்கவும், அடைப்புக்குறிக்குள் தமிழ் விளக்கம் கொடுக்கவும்.\n"
                "ஆங்கிலம் மற்றும் தமிழ் கலவையான வாக்கியங்கள் (Tanglish) கூடாது.\n"
                "Markdown தலைப்புகள் (##), புள்ளி பட்டியல்கள் (-), அட்டவணைகள் தொடர்ந்து பயன்படுத்தவும்.\n"
                "---\n"
            )
        else:
            return (
                "LANGUAGE INSTRUCTION (MANDATORY — FOLLOW EXACTLY):\n"
                "நீங்கள் Dr. Aiden — ஒரு தொழில்முறை AI சுகாதார உதவியாளர்.\n"
                "இந்த உரையாடலில் ONLY தமிழ் மொழியில் மட்டும் பதில் அளிக்கவும்.\n"
                "தமிழில் சரியான சொற்களை பயன்படுத்தவும்:\n"
                "  - Diabetes → நீரிழிவு நோய் (Diabetes என்று மட்டும் எழுத வேண்டாம்)\n"
                "  - Blood pressure → இரத்த அழுத்தம்\n"
                "  - Heart disease → இதய நோய்\n"
                "  - Cancer → புற்றுநோய்\n"
                "  - Fever → காய்ச்சல்\n"
                "  - Headache → தலைவலி\n"
                "  - Medicine → மருந்து\n"
                "  - Doctor → மருத்துவர்\n"
                "  - Hospital → மருத்துவமனை\n"
                "MRI, ECG, CT Scan, CBC போன்ற சர்வதேச சுருக்கங்களை ஆங்கிலத்தில் வைக்கவும்.\n"
                "ஆங்கிலம்-தமிழ் கலவை (Tanglish) கூடாது.\n"
                "Markdown: ## தலைப்புகள், - புள்ளி பட்டியல்கள், **தடிமன்** சொற்கள் பயன்படுத்தவும்.\n"
                "ஒவ்வொரு பதிலிலும் இந்த disclaimer சேர்க்கவும்:\n"
                "---\n"
                "⚕️ *இந்த தகவல் கல்வி நோக்கங்களுக்காக மட்டுமே, மருத்துவ நோயறிதல் அல்ல. "
                "தனிப்பட்ட மருத்துவ ஆலோசனைக்கு தகுதிவாய்ந்த மருத்துவரை அணுகவும்.*\n"
                "---\n"
            )
    # English — no extra instruction needed (system prompt already handles it)
    return ""


# ══════════════════════════════════════════════════════════════════════════════
# QUICK ACTION BUTTONS
# ══════════════════════════════════════════════════════════════════════════════

# English quick actions
QUICK_ACTIONS: List[Dict[str, str]] = [
    {"icon": "📋", "label": "Explain My Report",   "prompt": "Can you explain what a typical blood test report includes and what the common values mean?"},
    {"icon": "🥗", "label": "Healthy Diet",         "prompt": "What does a balanced, healthy diet look like? Give me practical tips for everyday meals."},
    {"icon": "🏃", "label": "Exercise Plan",         "prompt": "Create a beginner-friendly weekly exercise plan for general fitness and health."},
    {"icon": "💊", "label": "Medicine Info",         "prompt": "What are the general guidelines for taking medicines safely, including checking for interactions?"},
    {"icon": "🚑", "label": "First Aid",             "prompt": "What are the basic first aid steps I should know for common emergencies at home?"},
    {"icon": "🩺", "label": "Diabetes Care",         "prompt": "What lifestyle habits and diet changes help manage Type 2 diabetes effectively?"},
    {"icon": "❤️", "label": "Blood Pressure",        "prompt": "What are natural ways to manage high blood pressure alongside medical treatment?"},
    {"icon": "🧠", "label": "Mental Wellness",       "prompt": "What are practical daily habits that improve mental health and reduce stress and anxiety?"},
    {"icon": "👶", "label": "Child Care",            "prompt": "What are the key health milestones and vaccination schedule for children from 0 to 5 years?"},
    {"icon": "🌸", "label": "Women's Health",        "prompt": "What preventive health screenings and wellness practices are recommended for women at different life stages?"},
]

# Tamil quick actions — same prompts but labels and prompts are in Tamil
QUICK_ACTIONS_TAMIL: List[Dict[str, str]] = [
    {"icon": "📋", "label": "அறிக்கை விளக்கம்",
     "prompt": "ஒரு வழக்கமான இரத்த பரிசோதனை அறிக்கையில் என்ன இருக்கும், பொதுவான மதிப்புகள் என்ன என்று விளக்கவும்?"},
    {"icon": "🥗", "label": "ஆரோக்கியமான உணவு",
     "prompt": "சமச்சீரான ஆரோக்கியமான உணவு எப்படி இருக்கும்? அன்றாட உணவுக்கு நடைமுறை ஆலோசனைகள் கொடுங்கள்."},
    {"icon": "🏃", "label": "உடற்பயிற்சி திட்டம்",
     "prompt": "பொது ஆரோக்கியத்திற்காக தொடக்கநிலை வாராந்திர உடற்பயிற்சி திட்டம் தயாரித்துத் தாருங்கள்."},
    {"icon": "💊", "label": "மருந்து தகவல்",
     "prompt": "மருந்துகளை பாதுகாப்பாக எடுத்துக்கொள்வதற்கான பொதுவான வழிகாட்டுதல்கள் என்ன? மருந்து இடைவினைகளை எப்படி சரிபார்ப்பது?"},
    {"icon": "🚑", "label": "முதலுதவி",
     "prompt": "வீட்டில் பொதுவான அவசர நிலைகளில் அறிந்திருக்க வேண்டிய அடிப்படை முதலுதவி நடவடிக்கைகள் என்ன?"},
    {"icon": "🩺", "label": "நீரிழிவு பராமரிப்பு",
     "prompt": "வகை 2 நீரிழிவு நோயை திறம்படவாக நிர்வகிக்க உதவும் வாழ்க்கை முறை பழக்கங்கள் மற்றும் உணவு மாற்றங்கள் என்ன?"},
    {"icon": "❤️", "label": "இரத்த அழுத்தம்",
     "prompt": "மருத்துவ சிகிச்சையுடன் இணைந்து உயர் இரத்த அழுத்தத்தை இயற்கையான முறையில் கட்டுப்படுத்த என்ன வழிகள் உள்ளன?"},
    {"icon": "🧠", "label": "மனநலம்",
     "prompt": "மன ஆரோக்கியத்தை மேம்படுத்தவும் மன அழுத்தம் மற்றும் பதற்றத்தை குறைக்கவும் உதவும் அன்றாட நடைமுறை பழக்கங்கள் என்ன?"},
    {"icon": "👶", "label": "குழந்தை பராமரிப்பு",
     "prompt": "0 முதல் 5 வயது குழந்தைகளுக்கான முக்கிய ஆரோக்கிய மைல்கற்கள் மற்றும் தடுப்பூசி அட்டவணை என்ன?"},
    {"icon": "🌸", "label": "பெண்கள் நலம்",
     "prompt": "வெவ்வேறு வாழ்க்கை நிலைகளில் பெண்களுக்கு பரிந்துரைக்கப்படும் தடுப்பு ஆரோக்கிய பரிசோதனைகள் மற்றும் நல்வாழ்வு நடைமுறைகள் என்ன?"},
]


# ══════════════════════════════════════════════════════════════════════════════
# PAGE CSS
# ══════════════════════════════════════════════════════════════════════════════

_CSS = """
<style>
/* ── Widen the main content block ───────────────────────── */
.main .block-container {
  max-width: 92% !important;
  padding-left: 2rem !important;
  padding-right: 2rem !important;
}

/* ── Streamlit native chat message bubbles ───────────────── */
[data-testid="stChatMessage"] {
  padding: 0.6rem 1.4rem !important;
  max-width: 100% !important;
}

/* User message container */
[data-testid="stChatMessage"][data-testid*="user"],
[data-testid="stChatMessageContent"] {
  width: 100% !important;
}

/* ── User bubble ─────────────────────────────────────────── */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) .stMarkdown,
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) p {
  color: #FFFFFF !important;
}

div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
  border-radius: 18px 18px 4px 18px !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(37,99,235,0.35) !important;
  padding: 1rem 1.4rem !important;
}

/* ── AI bubble — modern card ─────────────────────────────── */
div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) {
  background: #1E293B !important;
  border-radius: 4px 18px 18px 18px !important;
  border: 1px solid #334155 !important;
  box-shadow: 0 4px 20px rgba(0,0,0,0.45), 0 1px 4px rgba(0,0,0,0.3) !important;
  padding: 1.25rem 1.5rem !important;
  margin-bottom: 0.75rem !important;
}

/* ── Typography inside chat messages ─────────────────────── */
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] td,
[data-testid="stChatMessage"] th {
  font-size: 16px !important;
  line-height: 1.75 !important;
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  color: #F1F5F9 !important;
}

[data-testid="stChatMessage"] h1,
[data-testid="stChatMessage"] h2,
[data-testid="stChatMessage"] h3,
[data-testid="stChatMessage"] h4 {
  color: #F8FAFC !important;
  margin-top: 1.1rem !important;
  margin-bottom: 0.45rem !important;
  font-weight: 700 !important;
  line-height: 1.35 !important;
}

[data-testid="stChatMessage"] h2 { font-size: 1.1rem !important; color: #60A5FA !important; }
[data-testid="stChatMessage"] h3 { font-size: 1rem !important;   color: #7DD3FC !important; }

[data-testid="stChatMessage"] strong { color: #FCD34D !important; }
[data-testid="stChatMessage"] em     { color: #A5B4FC !important; }

/* ── Bullet and numbered lists ───────────────────────────── */
[data-testid="stChatMessage"] ul,
[data-testid="stChatMessage"] ol {
  padding-left: 1.4rem !important;
  margin: 0.4rem 0 0.75rem !important;
}

[data-testid="stChatMessage"] li {
  margin-bottom: 0.35rem !important;
}

/* ── Tables inside chat ──────────────────────────────────── */
[data-testid="stChatMessage"] table {
  border-collapse: collapse !important;
  width: 100% !important;
  margin: 0.75rem 0 !important;
  font-size: 14px !important;
}

[data-testid="stChatMessage"] th {
  background: #0F172A !important;
  color: #60A5FA !important;
  padding: 0.5rem 0.75rem !important;
  text-align: left !important;
  font-weight: 700 !important;
  border: 1px solid #334155 !important;
}

[data-testid="stChatMessage"] td {
  padding: 0.45rem 0.75rem !important;
  border: 1px solid #334155 !important;
  color: #CBD5E1 !important;
  background: #1E293B !important;
}

[data-testid="stChatMessage"] tr:nth-child(even) td {
  background: #263345 !important;
}

/* ── Code blocks ─────────────────────────────────────────── */
[data-testid="stChatMessage"] code {
  background: #0F172A !important;
  color: #34D399 !important;
  padding: 0.15rem 0.4rem !important;
  border-radius: 4px !important;
  font-size: 0.88rem !important;
}

[data-testid="stChatMessage"] pre {
  background: #0F172A !important;
  border: 1px solid #334155 !important;
  border-radius: 8px !important;
  padding: 1rem !important;
  overflow-x: auto !important;
}

/* ── Horizontal rule (divider) inside chat ───────────────── */
[data-testid="stChatMessage"] hr {
  border: none !important;
  border-top: 1px solid #334155 !important;
  margin: 0.85rem 0 !important;
}

/* ── Blockquote (used for disclaimers) ───────────────────── */
[data-testid="stChatMessage"] blockquote {
  border-left: 3px solid #F59E0B !important;
  background: rgba(245,158,11,0.08) !important;
  padding: 0.5rem 0.9rem !important;
  border-radius: 0 8px 8px 0 !important;
  margin: 0.6rem 0 !important;
  color: #FCD34D !important;
  font-size: 0.88rem !important;
}
</style>
"""


# ══════════════════════════════════════════════════════════════════════════════
# REPORT SUMMARY CSS (injected separately for report cards)
# ══════════════════════════════════════════════════════════════════════════════

_REPORT_CSS = """
<style>
/* ── Medical report summary card ─────────────────────────── */
.report-summary-card {
  background: #0F172A;
  border-left: 5px solid #3B82F6;
  border-radius: 0 12px 12px 0;
  padding: 1.5rem 1.75rem;
  margin: 0.75rem 0 1rem 0;
  box-shadow: 0 6px 24px rgba(0,0,0,0.5);
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.report-section {
  margin-bottom: 1.25rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #1E293B;
}

.report-section:last-child { border-bottom: none; margin-bottom: 0; }

.report-section-title {
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 0.55rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  letter-spacing: 0.01em;
}

.report-section-body {
  font-size: 15px;
  line-height: 1.75;
  color: #CBD5E1;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.report-section-body ul { padding-left: 1.2rem; margin: 0.3rem 0; }
.report-section-body li { margin-bottom: 0.3rem; }

/* Section heading colours */
.rs-patient   { color: #60A5FA; }   /* blue   */
.rs-diagnosis { color: #34D399; }   /* green  */
.rs-abnormal  { color: #F87171; }   /* red    */
.rs-meds      { color: #A78BFA; }   /* purple */
.rs-tests     { color: #FBBF24; }   /* amber  */
.rs-recs      { color: #38BDF8; }   /* sky    */
.rs-disclaimer{ color: #94A3B8; }   /* slate  */

/* ── Download / Copy button row ──────────────────────────── */
.report-action-row {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
  margin-top: 1rem;
  padding-top: 0.85rem;
  border-top: 1px solid #1E293B;
}

/* ── Provider badge ─────────────────────────────────────────── */
.provider-badge {
  display: inline-flex; align-items: center; gap: 0.3rem;
  border-radius: 99px; padding: 0.18rem 0.7rem;
  font-size: 0.7rem; font-weight: 700;
  letter-spacing: 0.03em;
}
.provider-groq   { background:rgba(59,130,246,0.15); color:#93C5FD; border:1px solid rgba(59,130,246,0.3); }
.provider-gemini { background:rgba(239,68,68,0.12);  color:#FCA5A5; border:1px solid rgba(239,68,68,0.25); }

/* ── PDF badge ──────────────────────────────────────────── */
.pdf-badge {
  display: inline-flex; align-items: center; gap: 0.35rem;
  background: rgba(34,197,94,0.12);
  border: 1px solid rgba(34,197,94,0.25);
  border-radius: 99px; padding: 0.2rem 0.75rem;
  font-size: 0.74rem; font-weight: 600; color: #86EFAC;
  margin-bottom: 0.7rem;
}

/* ── Empty state ────────────────────────────────────────── */
.empty-chat {
  text-align: center;
  padding: 2.5rem 1rem;
  color: #475569;
}
.empty-chat-icon { font-size: 3.2rem; margin-bottom: 0.75rem; display: block; }
.empty-chat h3   { color: #64748B; font-size: 1.02rem; margin: 0 0 0.35rem; }
.empty-chat p    { font-size: 0.88rem; margin: 0; color: #475569; }

/* ── Typing animation ───────────────────────────────────── */
.typing-wrapper {
  display: flex; align-items: center; gap: 0.75rem;
  padding: 0.4rem 0.2rem;
}
.typing-label {
  font-size: 0.88rem; color: #64748B; font-style: italic;
}
.typing-dots { display: inline-flex; gap: 5px; }
.typing-dots span {
  width: 8px; height: 8px; border-radius: 50%;
  background: #475569;
  animation: typingBounce 1.2s infinite ease-in-out;
}
.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes typingBounce {
  0%,60%,100% { transform: translateY(0); opacity: 0.6; }
  30% { transform: translateY(-8px); background: #3B82F6; opacity: 1; }
}

/* ── Progress bar animation ─────────────────────────────── */
.analysis-progress {
  width: 100%; height: 3px;
  background: #1E293B;
  border-radius: 99px;
  margin-top: 0.5rem;
  overflow: hidden;
}
.analysis-progress-bar {
  height: 100%; width: 0%;
  background: linear-gradient(90deg, #3B82F6, #60A5FA, #3B82F6);
  background-size: 200% 100%;
  border-radius: 99px;
  animation: progressAnim 2s ease-in-out infinite;
}
@keyframes progressAnim {
  0%   { width: 0%;   background-position: 0% 50%; }
  50%  { width: 75%;  background-position: 100% 50%; }
  100% { width: 100%; background-position: 0% 50%; }
}

/* ── Responsive ─────────────────────────────────────────── */
@media (max-width: 768px) {
  .main .block-container {
    padding-left: 0.75rem !important;
    padding-right: 0.75rem !important;
    max-width: 100% !important;
  }
  [data-testid="stChatMessage"] p,
  [data-testid="stChatMessage"] li {
    font-size: 15px !important;
  }
  .report-summary-card { padding: 1rem 1rem; }
}

@media (max-width: 480px) {
  [data-testid="stChatMessage"] p,
  [data-testid="stChatMessage"] li {
    font-size: 14px !important;
    line-height: 1.65 !important;
  }
  .report-action-row { flex-direction: column; }
}
</style>
"""


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _init_session() -> None:
    """Initialise session-state keys used by this page."""
    defaults = {
        "aha_messages":   [],
        "aha_session_id": str(uuid.uuid4()),
        "aha_pdf_text":   "",
        "aha_pdf_name":   "",
        "aha_prefill":    "",
        "aha_thinking":   False,
        # Tracks which message indices are PDF report responses
        "aha_pdf_responses": set(),
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _get_user_id() -> Optional[int]:
    user = get_current_user()
    return user.get("id") if user else None


def _persist(role: str, content: str, has_pdf: bool = False) -> None:
    try:
        save_chat_message(
            session_id=st.session_state.aha_session_id,
            role=role,
            content=content,
            user_id=_get_user_id(),
            provider=get_active_provider().lower(),
            has_pdf=has_pdf,
        )
    except Exception as exc:
        logger.warning("Failed to persist chat message: %s", exc)


def _call_llm(user_text: str) -> str:
    """
    Send the conversation to the LLM and return the reply.
    Language instruction is prepended to every system prompt so the
    LLM responds ONLY in the currently selected UI language (Tamil or English).
    """
    pdf_text  = st.session_state.aha_pdf_text
    lang_instr = _get_language_instruction(is_pdf=bool(pdf_text))

    # ── Build system prompt ───────────────────────────────────────────────
    lang = _get_ui_language()
    if pdf_text:
        base_system = _PDF_SYSTEM_PROMPT_TAMIL if lang == "Tamil" else _PDF_SYSTEM_PROMPT
    else:
        base_system = _SYSTEM_PROMPT

    # When Tamil is active, the language instruction is injected at the very
    # top of the system prompt so the LLM sees it before any other rules.
    if lang_instr:
        system_content = lang_instr + "\n\n" + base_system
    else:
        system_content = base_system

    # ── Build user message ────────────────────────────────────────────────
    if pdf_text:
        if lang == "Tamil":
            full_user = (
                f"நான் பதிவேற்றிய மருத்துவ அறிக்கை இங்கே:\n\n"
                f"```\n{pdf_text[:6000]}\n```\n\n"
                f"என் கேள்வி: {user_text}"
            )
        else:
            full_user = (
                f"Here is the medical report I uploaded:\n\n"
                f"```\n{pdf_text[:6000]}\n```\n\n"
                f"My question: {user_text}"
            )
    else:
        full_user = user_text

    # ── Assemble message list ─────────────────────────────────────────────
    msgs = [{"role": "system", "content": system_content}]
    # Include last 20 turns for context (skip the very last — it's the current user msg)
    for m in st.session_state.aha_messages[:-1]:
        msgs.append({"role": m["role"], "content": m["content"]})
    msgs.append({"role": "user", "content": full_user})

    return chat_completion(msgs)

# ══════════════════════════════════════════════════════════════════════════════
# DOWNLOAD HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _make_txt_download(content: str, filename: str) -> bytes:
    """Return UTF-8 bytes for a plain-text download."""
    header = (
        "=" * 60 + "\n"
        "MEDICAL REPORT SUMMARY — AI Health Assistant\n"
        f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        "=" * 60 + "\n\n"
    )
    return (header + content).encode("utf-8")


def _make_pdf_download(content: str, filename: str) -> Optional[bytes]:
    """
    Return PDF bytes using fpdf2 if available, else None.
    Falls back gracefully so the UI never crashes.
    """
    try:
        from fpdf import FPDF  # type: ignore
    except ImportError:
        return None

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Medical Report Summary", ln=True, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6,
             f"AI Health Assistant  |  Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
             ln=True, align="C")
    pdf.ln(6)
    pdf.set_text_color(30, 41, 59)
    pdf.set_draw_color(51, 65, 85)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(203, 213, 225)

    for line in content.splitlines():
        line = line.strip()
        if not line:
            pdf.ln(3)
            continue
        # Markdown heading → bold larger text
        if line.startswith("## "):
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(96, 165, 250)
            pdf.multi_cell(0, 7, line[3:])
            pdf.set_font("Helvetica", "", 11)
            pdf.set_text_color(203, 213, 225)
        elif line.startswith("### "):
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(125, 211, 252)
            pdf.multi_cell(0, 6, line[4:])
            pdf.set_font("Helvetica", "", 11)
            pdf.set_text_color(203, 213, 225)
        elif line.startswith("**") and line.endswith("**"):
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(0, 6, line.strip("*"))
            pdf.set_font("Helvetica", "", 11)
        elif line.startswith("- ") or line.startswith("* "):
            pdf.multi_cell(0, 6, "  \u2022 " + line[2:])
        elif line.startswith("---"):
            pdf.set_draw_color(51, 65, 85)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)
        else:
            # Strip simple inline markdown (* and _)
            clean = line.replace("**", "").replace("__", "").replace("*", "").replace("_", "")
            pdf.multi_cell(0, 6, clean)

    return bytes(pdf.output())


# ══════════════════════════════════════════════════════════════════════════════
# REPORT SUMMARY CARD RENDERER
# ══════════════════════════════════════════════════════════════════════════════

# Maps section heading keywords → (css_class, emoji, label)
_SECTION_MAP = [
    (["patient information", "patient info"],            "rs-patient",   "📄", "Patient Information"),
    (["diagnosis", "key findings", "diagnosis / key"],   "rs-diagnosis", "🩺", "Diagnosis / Key Findings"),
    (["abnormal findings", "abnormal"],                  "rs-abnormal",  "⚠️", "Abnormal Findings"),
    (["medications", "medication"],                      "rs-meds",      "💊", "Medications"),
    (["test results", "tests"],                          "rs-tests",     "🧪", "Test Results"),
    (["recommendations", "follow-up", "questions"],      "rs-recs",      "📋", "Recommendations"),
    (["disclaimer"],                                     "rs-disclaimer","📌", "Disclaimer"),
]


def _classify_section(heading: str) -> tuple:
    """Return (css_class, emoji, label) for a heading string."""
    h = heading.lower().strip()
    for keywords, css_cls, emoji, label in _SECTION_MAP:
        if any(kw in h for kw in keywords):
            return css_cls, emoji, label
    return "rs-patient", "📋", heading.strip("# ").strip()


def _render_report_summary_card(response: str, msg_index: int) -> None:
    """
    Parse the LLM markdown response and render it as a styled
    sectioned card with Copy / Download TXT / Download PDF buttons.
    """
    st.markdown(_REPORT_CSS, unsafe_allow_html=True)

    # ── Split response into sections by ## headings ───────────────────────
    import re
    parts = re.split(r"(?m)^#{1,3}\s+", response)
    headings = re.findall(r"(?m)^#{1,3}\s+(.+)", response)

    sections_html = ""
    if headings and len(parts) > 1:
        for heading, body in zip(headings, parts[1:]):
            css_cls, emoji, label = _classify_section(heading)
            # Convert body markdown bullets to HTML list items
            body_html = _md_to_simple_html(body.strip())
            sections_html += f"""
            <div class="report-section">
              <div class="report-section-title {css_cls}">{emoji} {label}</div>
              <div class="report-section-body">{body_html}</div>
            </div>"""
    else:
        # Fallback: render the whole response as a single section body
        sections_html = f"""
        <div class="report-section">
          <div class="report-section-body">{_md_to_simple_html(response)}</div>
        </div>"""

    st.markdown(
        f'<div class="report-summary-card">{sections_html}</div>',
        unsafe_allow_html=True,
    )

    # ── Action buttons ────────────────────────────────────────────────────
    st.markdown('<div class="report-action-row">', unsafe_allow_html=True)
    btn_col1, btn_col2, btn_col3, _ = st.columns([1.4, 1.6, 1.7, 3])

    with btn_col1:
        if st.button("📋 Copy Summary", key=f"copy_btn_{msg_index}",
                     use_container_width=True, help="Copy summary text to clipboard"):
            # Inject JS clipboard copy
            escaped = response.replace("`", "\\`").replace("$", "\\$")
            st.components.v1.html(
                f"""<script>navigator.clipboard.writeText(`{escaped}`)
                .then(()=>{{console.log('copied')}})
                .catch(e=>console.error(e));</script>""",
                height=0,
            )
            st.toast("✅ Summary copied to clipboard!", icon="📋")

    with btn_col2:
        txt_bytes = _make_txt_download(response, "report_summary.txt")
        st.download_button(
            label="📄 Download TXT",
            data=txt_bytes,
            file_name=f"report_summary_{msg_index}.txt",
            mime="text/plain",
            key=f"dl_txt_{msg_index}",
            use_container_width=True,
            help="Download as plain text file",
        )

    with btn_col3:
        pdf_bytes = _make_pdf_download(response, "report_summary.pdf")
        if pdf_bytes:
            st.download_button(
                label="📥 Download PDF",
                data=pdf_bytes,
                file_name=f"report_summary_{msg_index}.pdf",
                mime="application/pdf",
                key=f"dl_pdf_{msg_index}",
                use_container_width=True,
                help="Download as PDF file",
            )
        else:
            st.markdown(
                "<small style='color:#475569;font-size:0.75rem;'>"
                "💡 Install <code>fpdf2</code> for PDF export</small>",
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)


def _md_to_simple_html(text: str) -> str:
    """
    Convert a subset of Markdown to safe HTML for display inside
    the report card (bullet lists, bold, italic, horizontal rules).
    Tables are left as-is so Streamlit markdown can handle them later.
    """
    import re
    lines = text.splitlines()
    out = []
    in_list = False

    for line in lines:
        stripped = line.strip()

        # Horizontal rule
        if stripped in ("---", "***", "___"):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append('<hr style="border:none;border-top:1px solid #334155;margin:0.6rem 0;">')
            continue

        # Bullet list item
        if stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            item = stripped[2:]
            item = _inline_md(item)
            out.append(f"<li>{item}</li>")
            continue

        # Numbered list item
        num_match = re.match(r"^(\d+)\.\s+(.+)", stripped)
        if num_match:
            if in_list:
                out.append("</ul>")
                in_list = False
            item = _inline_md(num_match.group(2))
            out.append(f"<li>{item}</li>")
            continue

        if in_list:
            out.append("</ul>")
            in_list = False

        if not stripped:
            out.append("<br>")
        else:
            out.append(f"<p style='margin:0.3rem 0;'>{_inline_md(stripped)}</p>")

    if in_list:
        out.append("</ul>")

    return "\n".join(out)


def _inline_md(text: str) -> str:
    """Apply inline bold, italic, and code markdown to a string."""
    import re
    # Bold **text** or __text__
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong style='color:#FCD34D;'>\1</strong>", text)
    text = re.sub(r"__(.+?)__",     r"<strong style='color:#FCD34D;'>\1</strong>", text)
    # Italic *text* or _text_
    text = re.sub(r"\*(.+?)\*",     r"<em style='color:#A5B4FC;'>\1</em>", text)
    text = re.sub(r"_(.+?)_",       r"<em style='color:#A5B4FC;'>\1</em>", text)
    # Inline code `text`
    text = re.sub(r"`(.+?)`",
                  r"<code style='background:#0F172A;color:#34D399;padding:0.1rem 0.35rem;"
                  r"border-radius:4px;font-size:0.87em;'>\1</code>", text)
    return text


# ══════════════════════════════════════════════════════════════════════════════
# AUTO-SCROLL JS
# ══════════════════════════════════════════════════════════════════════════════

_AUTOSCROLL_JS = """
<script>
(function() {
  // Scroll the Streamlit main content to the bottom after a short delay
  // so the latest chat message is always visible.
  function scrollToBottom() {
    const main = window.parent.document.querySelector('section.main');
    if (main) { main.scrollTop = main.scrollHeight; }
  }
  setTimeout(scrollToBottom, 120);
})();
</script>
"""


def _inject_autoscroll() -> None:
    st.components.v1.html(_AUTOSCROLL_JS, height=0)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER
# ══════════════════════════════════════════════════════════════════════════════

def render() -> None:
    """Entry point called by the agent router."""
    # Inject both CSS blocks
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown(_REPORT_CSS, unsafe_allow_html=True)
    _init_session()

    provider     = get_active_provider()
    provider_cls  = "provider-gemini" if provider == "Gemini" else "provider-groq"
    provider_icon = "✨" if provider == "Gemini" else "⚡"
    is_pdf_mode   = bool(st.session_state.aha_pdf_text)
    lang          = _get_ui_language()           # "Tamil" | "English"
    is_tamil      = lang == "Tamil"

    # ── Localised string helpers ──────────────────────────────────────────
    _str = {
        "title":       "AI சுகாதார உதவியாளர்"     if is_tamil else "AI Health Assistant",
        "subtitle":    "Dr. Aiden — உங்கள் தனிப்பட்ட சுகாதார நண்பர்"
                       if is_tamil else "Dr. Aiden — Your personal healthcare companion",
        "disclaimer":  (
            "⚠️ <strong>மருத்துவ முன்னெச்சரிக்கை:</strong> Dr. Aiden சுகாதார "
            "<em>தகவல்களை</em> மட்டுமே வழங்குகிறார் — மருத்துவ ஆலோசனை, நோயறிதல் "
            "அல்லது மருந்து சீட்டு அல்ல. தனிப்பட்ட மருத்துவ முடிவுகளுக்கு "
            "எப்போதும் தகுதிவாய்ந்த மருத்துவரை அணுகவும்."
        ) if is_tamil else (
            "⚠️ <strong>Medical Disclaimer:</strong> Dr. Aiden provides health "
            "<em>information</em> only — not medical advice, diagnoses, or prescriptions. "
            "Always consult a qualified healthcare professional for personal medical decisions."
        ),
        "clear_chat":  "🗑️ அரட்டை அழி"          if is_tamil else "🗑️ Clear Chat",
        "attach_pdf":  "📎 அறிக்கை PDF இணைக்க"   if is_tamil else "📎 Attach Report PDF",
        "upload_hint": "மருத்துவ அறிக்கை (PDF) பதிவேற்றவும்"
                       if is_tamil else "Upload a medical report (PDF) for AI analysis",
        "remove_pdf":  "❌ PDF அகற்று"            if is_tamil else "❌ Remove PDF",
        "reading_pdf": "📖 PDF படிக்கிறது…"        if is_tamil else "📖 Reading PDF…",
        "empty_title": "வணக்கம்! நான் Dr. Aiden, உங்கள் AI சுகாதார உதவியாளர்."
                       if is_tamil else "Hello! I'm Dr. Aiden, your AI Health Assistant.",
        "empty_body":  ("ஆரோக்கியம், மருந்துகள், உணவு அல்லது உடற்பயிற்சி பற்றி "
                        "எதையும் கேளுங்கள் — அல்லது விரிவான AI பகுப்பாய்வுக்கு "
                        "மருத்துவ அறிக்கை PDF பதிவேற்றுங்கள்.")
                       if is_tamil else (
                        "Ask me anything about health, medicines, diet, or exercise — "
                        "or upload a medical report PDF for a detailed AI analysis."
                       ),
        "quick_label": "⚡ விரைவு செயல்கள்"        if is_tamil else "⚡ Quick Actions",
        "typing_pdf":  "மருத்துவ அறிக்கையை பகுப்பாய்வு செய்கிறது…"
                       if is_tamil else "Analyzing medical report…",
        "typing_chat": "Dr. Aiden யோசிக்கிறார்…"  if is_tamil else "Dr. Aiden is thinking…",
        "chat_input":  "Dr. Aiden ஐ கேளுங்கள்…"   if is_tamil else "Ask Dr. Aiden anything about your health…",
        "short_warn":  "கூடுதல் விவரமான கேள்வியை உள்ளிடவும்."
                       if is_tamil else "Please enter a more detailed question.",
        "msg_count":   lambda n: (
            f"💬 இந்த அமர்வில் {n} செய்தி{'கள்' if n != 1 else ''}"
            if is_tamil else
            f"💬 {n} message{'s' if n != 1 else ''} in this session"
        ),
    }

    # ── Page header ───────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div class="page-header">
          <div style="display:flex;align-items:center;justify-content:space-between;
                      flex-wrap:wrap;gap:0.5rem;">
            <div style="display:flex;align-items:center;gap:1rem;">
              <span style="font-size:2.4rem;">🤖</span>
              <div>
                <h1 style="margin:0;">{_str["title"]}</h1>
                <p style="margin:0;font-size:0.9rem;color:#94A3B8;">
                  {_str["subtitle"]}</p>
              </div>
            </div>
            <span class="provider-badge {provider_cls}">{provider_icon} {provider}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Disclaimer banner ─────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="background:#FFFBEB;border-left:4px solid #D97706;
                    border-radius:10px;padding:0.75rem 1rem;margin-bottom:1rem;
                    font-size:0.84rem;color:#92400E;">
          {_str["disclaimer"]}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Top controls row ──────────────────────────────────────────────────
    col_count, col_clear, col_pdf_toggle = st.columns([3, 1.2, 1.5])

    with col_count:
        n = len(st.session_state.aha_messages)
        st.markdown(
            f"<div style='padding-top:0.5rem;font-size:0.82rem;color:#64748B;'>"
            f"{_str['msg_count'](n)}</div>",
            unsafe_allow_html=True,
        )

    with col_clear:
        if st.button(_str["clear_chat"], key="btn_clear_aha", use_container_width=True):
            st.session_state.aha_messages      = []
            st.session_state.aha_pdf_text      = ""
            st.session_state.aha_pdf_name      = ""
            st.session_state.aha_pdf_responses = set()
            try:
                delete_chat_session(st.session_state.aha_session_id)
            except Exception:
                pass
            st.session_state.aha_session_id = str(uuid.uuid4())
            st.rerun()

    with col_pdf_toggle:
        show_pdf = st.toggle(_str["attach_pdf"], key="aha_show_pdf_uploader")

    # ── PDF uploader ──────────────────────────────────────────────────────
    if show_pdf:
        uploaded_pdf = st.file_uploader(
            _str["upload_hint"],
            type=["pdf"],
            key="aha_pdf_uploader",
            label_visibility="collapsed",
        )
        if uploaded_pdf:
            if uploaded_pdf.name != st.session_state.aha_pdf_name:
                with st.spinner(_str["reading_pdf"]):
                    extracted = extract_text_from_uploaded_file(uploaded_pdf)
                if extracted.startswith("⚠️"):
                    st.error(extracted)
                else:
                    st.session_state.aha_pdf_text = extracted
                    st.session_state.aha_pdf_name = uploaded_pdf.name
                    char_msg = (
                        f"✅ **{uploaded_pdf.name}** ஏற்றப்பட்டது — {len(extracted):,} எழுத்துகள் படிக்கப்பட்டன."
                        if is_tamil else
                        f"✅ **{uploaded_pdf.name}** loaded — {len(extracted):,} characters extracted."
                    )
                    st.success(char_msg)

        if st.session_state.aha_pdf_name:
            st.markdown(
                f'<div class="pdf-badge">📄 {st.session_state.aha_pdf_name} — '
                f'{"இணைக்கப்பட்டது" if is_tamil else "attached"}</div>',
                unsafe_allow_html=True,
            )
            if st.button(_str["remove_pdf"], key="btn_remove_pdf"):
                st.session_state.aha_pdf_text = ""
                st.session_state.aha_pdf_name = ""
                st.rerun()

    is_pdf_mode = bool(st.session_state.aha_pdf_text)
    st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)

    # ── Empty state + Quick Actions ───────────────────────────────────────
    if not st.session_state.aha_messages:
        st.markdown(
            f"""
            <div class="empty-chat">
              <span class="empty-chat-icon">🤖</span>
              <h3>{_str["empty_title"]}</h3>
              <p>{_str["empty_body"]}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"<p style='font-size:0.78rem;font-weight:700;color:#94A3B8;"
        f"letter-spacing:0.07em;text-transform:uppercase;margin-bottom:0.5rem;'>"
        f"{_str['quick_label']}</p>",
        unsafe_allow_html=True,
    )

    # Pick Tamil or English action set
    actions = QUICK_ACTIONS_TAMIL if is_tamil else QUICK_ACTIONS

    qa_cols1 = st.columns(5)
    for col, action in zip(qa_cols1, actions[:5]):
        with col:
            if st.button(f"{action['icon']} {action['label']}",
                         key=f"qa_{action['label']}", use_container_width=True):
                st.session_state.aha_prefill = action["prompt"]
                st.rerun()

    qa_cols2 = st.columns(5)
    for col, action in zip(qa_cols2, actions[5:]):
        with col:
            if st.button(f"{action['icon']} {action['label']}",
                         key=f"qa_{action['label']}", use_container_width=True):
                st.session_state.aha_prefill = action["prompt"]
                st.rerun()

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── Chat history display ──────────────────────────────────────────────
    pdf_responses: set = st.session_state.aha_pdf_responses

    if st.session_state.aha_messages:
        for i, msg in enumerate(st.session_state.aha_messages):
            role    = msg["role"]
            content = msg["content"]
            ts      = msg.get("ts", "")

            if role == "user":
                with st.chat_message("user", avatar="👤"):
                    st.markdown(content)
                    if ts:
                        st.markdown(
                            f"<div style='font-size:0.68rem;color:#475569;"
                            f"text-align:right;margin-top:0.15rem;'>{ts}</div>",
                            unsafe_allow_html=True,
                        )
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    # If this response was generated while a PDF was attached,
                    # render it as a sectioned report card with action buttons.
                    if i in pdf_responses:
                        _render_report_summary_card(content, i)
                    else:
                        st.markdown(content)
                    if ts:
                        st.markdown(
                            f"<div style='font-size:0.68rem;color:#475569;"
                            f"margin-top:0.3rem;'>{ts}</div>",
                            unsafe_allow_html=True,
                        )

    # ── Typing animation placeholder ──────────────────────────────────────
    typing_placeholder = st.empty()

    # ── Chat input ────────────────────────────────────────────────────────
    prefill    = st.session_state.pop("aha_prefill", "")
    user_input = st.chat_input(
        _str["chat_input"],
        key="aha_chat_input",
    )
    if not user_input and prefill:
        user_input = prefill

    if user_input:
        user_input = user_input.strip()
        if len(user_input) < 2:
            st.warning(_str["short_warn"])
            return

        ts_now = datetime.datetime.now().strftime("%H:%M")

        # Add and show user message immediately
        st.session_state.aha_messages.append(
            {"role": "user", "content": user_input, "ts": ts_now}
        )
        _persist("user", user_input, has_pdf=is_pdf_mode)

        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)
            st.markdown(
                f"<div style='font-size:0.68rem;color:#475569;"
                f"text-align:right;margin-top:0.15rem;'>{ts_now}</div>",
                unsafe_allow_html=True,
            )

        # ── Typing / progress animation ───────────────────────────────────
        if is_pdf_mode:
            with typing_placeholder.container():
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(
                        f"""
                        <div class="typing-wrapper">
                          <div class="typing-dots">
                            <span></span><span></span><span></span>
                          </div>
                          <span class="typing-label">{_str["typing_pdf"]}</span>
                        </div>
                        <div class="analysis-progress">
                          <div class="analysis-progress-bar"></div>
                        </div>
                        <div style="font-size:0.75rem;color:#475569;margin-top:0.5rem;
                                    font-style:italic;">
                          💡 To save this report permanently, use
                          <b style="color:#60A5FA;">📁 Patient Records → Reports</b>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            with typing_placeholder.container():
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(
                        f"""
                        <div class="typing-wrapper">
                          <div class="typing-dots">
                            <span></span><span></span><span></span>
                          </div>
                          <span class="typing-label">{_str["typing_chat"]}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        # ── LLM call ──────────────────────────────────────────────────────
        with st.spinner(""):
            response = _call_llm(user_input)

        typing_placeholder.empty()

        # Track this as a PDF response if PDF was active during the call
        new_idx = len(st.session_state.aha_messages)   # index of the new assistant msg
        if is_pdf_mode:
            st.session_state.aha_pdf_responses.add(new_idx)

        st.session_state.aha_messages.append(
            {"role": "assistant", "content": response, "ts": ts_now}
        )
        _persist("assistant", response)

        # Show the new assistant message immediately
        with st.chat_message("assistant", avatar="🤖"):
            if is_pdf_mode:
                _render_report_summary_card(response, new_idx)
            else:
                st.markdown(response)
            st.markdown(
                f"<div style='font-size:0.68rem;color:#475569;"
                f"margin-top:0.3rem;'>{ts_now}</div>",
                unsafe_allow_html=True,
            )

        # Auto-scroll to the latest message
        _inject_autoscroll()

        st.rerun()
