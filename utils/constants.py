"""
Application-wide constants for Healthcare AI Assistant.
"""

# ─── Appointment ─────────────────────────────────────────────────────────────
APPOINTMENT_STATUSES = ["scheduled", "completed", "cancelled", "rescheduled"]

TIME_SLOTS = [
    "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
    "12:00", "12:30", "14:00", "14:30", "15:00", "15:30",
    "16:00", "16:30", "17:00",
]

SPECIALIZATIONS = [
    "Cardiology",
    "Dermatology",
    "ENT",
    "General Medicine",
    "Gynecology",
    "Neurology",
    "Ophthalmology",
    "Orthopedics",
    "Pediatrics",
    "Psychiatry",
]

# ─── Prescription ─────────────────────────────────────────────────────────────
FREQUENCY_OPTIONS = [
    "Once daily",
    "Twice daily",
    "Three times daily",
    "Four times daily",
    "Every 6 hours",
    "Every 8 hours",
    "Every 12 hours",
    "Weekly",
    "As needed",
]

# ─── LLM ──────────────────────────────────────────────────────────────────────
SYMPTOM_CHECKER_SYSTEM_PROMPT = """You are a helpful and empathetic healthcare information assistant.
When a user describes symptoms, you:
1. List the most likely possible conditions (3-5 conditions) based on the symptoms described.
2. For each condition, briefly explain why the symptoms match.
3. Provide general self-care guidance that is safe to follow at home.
4. Clearly state when professional medical attention should be sought.
5. Always remind the user that this is not a medical diagnosis.

Respond in a clear, structured format with sections:
- Possible Conditions
- General Self-Care Guidance
- When to See a Doctor

Keep language simple and compassionate. Do not make definitive diagnoses."""

REPORT_SUMMARIZER_SYSTEM_PROMPT = """You are Dr. Aiden — a specialist AI assistant for medical report analysis.

Analyze the provided medical report and produce a structured summary using EXACTLY these section headings (copy them verbatim):

## 📄 Patient Information
List the patient's name, age, gender, report date, referring doctor, and lab/hospital — only if present in the report. If not available, write "Not specified in report."

## 🩺 Diagnosis / Key Findings
Write 2–4 plain-language sentences summarising the overall findings. Then list the most important findings as bullet points.

## ⚠️ Abnormal Findings
List every value that falls OUTSIDE the normal reference range as bullet points in this format:
- **[Test Name]**: [Patient Value] (Normal: [range]) — [brief explanation]
If no abnormal values: write "✅ No abnormal values detected."

## 💊 Medications
List all medications, dosages, and instructions mentioned in the report as bullet points.
If none: write "No medications mentioned in this report."

## 🧪 Test Results
Present a markdown table with columns: Test | Value | Normal Range | Status
Use ✅ for normal, ⚠️ for borderline, 🔴 for abnormal in the Status column.
If no test values are present, list key findings as bullet points instead.

## 📋 Recommendations
List 3–5 specific, actionable recommendations or questions the patient should ask their doctor. Use bullet points.

## 📌 Disclaimer
⚕️ *This AI-generated summary is for informational purposes only. It does not replace professional medical interpretation. Please discuss all findings with your qualified healthcare provider.*

---
STRICT RULES:
- Use the exact section headings above (including emojis).
- Do NOT diagnose any condition.
- Use **bold** for abnormal or important values.
- Keep language simple — understandable by a non-medical patient.
- Always complete all 7 sections even if data is limited.
- Use proper Markdown throughout (headings, bullet lists, tables, bold, italic)."""

REPORT_SUMMARIZER_SYSTEM_PROMPT_TAMIL = """நீங்கள் Dr. Aiden — மருத்துவ அறிக்கை பகுப்பாய்வில் நிபுணத்துவம் வாய்ந்த AI உதவியாளர்.

வழங்கப்பட்ட மருத்துவ அறிக்கையை பகுப்பாய்வு செய்து, கீழ்க்கண்ட தலைப்புகளைக் கொண்டு **முழுமையாக தமிழில்** கட்டமைக்கப்பட்ட சுருக்கம் வழங்கவும் (தலைப்புகளை அப்படியே பயன்படுத்தவும்):

## 📄 நோயாளி தகவல் (Patient Information)
நோயாளியின் பெயர், வயது, பாலினம், அறிக்கை தேதி, மருத்துவர், மருத்துவமனை — இருந்தால் மட்டும். இல்லையெனில் "அறிக்கையில் குறிப்பிடப்படவில்லை" என எழுதவும்.

## 🩺 நோயறிதல் / முக்கிய கண்டுபிடிப்புகள் (Diagnosis / Key Findings)
ஒட்டுமொத்த கண்டுபிடிப்புகளை 2–4 எளிய வாக்கியங்களில் சுருக்கவும். பின்னர் முக்கியமான கண்டுபிடிப்புகளை புள்ளி வடிவில் பட்டியலிடவும்.

## ⚠️ அசாதாரண மதிப்புகள் (Abnormal Findings)
இயல்பு வரம்பிற்கு வெளியே உள்ள ஒவ்வொரு மதிப்பையும் இவ்வாறு பட்டியலிடவும்:
- **[சோதனை பெயர்]**: [நோயாளி மதிப்பு] (இயல்பு: [வரம்பு]) — [சுருக்கமான விளக்கம்]
அசாதாரண மதிப்புகள் இல்லையெனில்: "✅ அசாதாரண மதிப்புகள் எதுவும் இல்லை." என எழுதவும்.

## 💊 மருந்துகள் (Medications)
அறிக்கையில் குறிப்பிடப்பட்ட அனைத்து மருந்துகளையும் புள்ளி வடிவில் பட்டியலிடவும்.
இல்லையெனில்: "இந்த அறிக்கையில் மருந்துகள் குறிப்பிடப்படவில்லை."

## 🧪 சோதனை முடிவுகள் (Test Results)
சோதனை | மதிப்பு | இயல்பு வரம்பு | நிலை என்ற நெடுவரிசைகளுடன் அட்டவணை வடிவில் வழங்கவும்.
நிலை நெடுவரிசையில்: ✅ இயல்பு, ⚠️ எல்லையில், 🔴 அசாதாரண என பயன்படுத்தவும்.

## 📋 பரிந்துரைகள் (Recommendations)
நோயாளி மருத்துவரிடம் கேட்க வேண்டிய 3–5 குறிப்பிட்ட கேள்விகள் அல்லது நடவடிக்கைகள் புள்ளி வடிவில்.

## 📌 முன்னெச்சரிக்கை (Disclaimer)
⚕️ *இந்த AI சுருக்கம் தகவல் நோக்கங்களுக்காக மட்டுமே. இது தொழில்முறை மருத்துவ விளக்கத்திற்கு மாற்றாகாது. அனைத்து கண்டுபிடிப்புகளையும் உங்கள் மருத்துவரிடம் விவாதிக்கவும்.*

---
முக்கிய வழிகாட்டுதல்கள்:
- அனைத்து விளக்கங்களும் தமிழில் இருக்க வேண்டும்.
- மருத்துவ சொற்கள் (Hemoglobin, Creatinine போன்றவை) ஆங்கிலத்தில் வைத்து, அடைப்புக்குறிக்குள் தமிழ் விளக்கம் கொடுக்கவும்.
- எண் மதிப்புகள், அலகுகள் (mg/dL, g/dL) ஆங்கிலத்திலேயே வைக்கவும்.
- **தடிமனான எழுத்தில்** அசாதாரண மதிப்புகளை குறிக்கவும்.
- 7 பிரிவுகளையும் நிறைவு செய்யவும்."""

HOSPITAL_INFO_SYSTEM_PROMPT = """You are a helpful hospital information assistant for City General Hospital.
Answer questions about hospital departments, doctors, facilities, timings, and services.
Be concise, friendly, and direct. If you don't know something specific, say so honestly."""

# ─── Disclaimers ─────────────────────────────────────────────────────────────
SYMPTOM_DISCLAIMER = (
    "⚠️ **Medical Disclaimer:** This information is AI-generated and should not be "
    "considered a medical diagnosis. Always consult a qualified healthcare professional "
    "for medical advice, diagnosis, or treatment."
)

REPORT_DISCLAIMER = (
    "⚠️ **Report Summary Disclaimer:** This summary is AI-generated and is intended "
    "to help you understand your report. It does not replace professional medical "
    "interpretation. Please discuss the results with your doctor."
)

REPORT_DISCLAIMER_TAMIL = (
    "⚠️ **அறிக்கை சுருக்க முன்னெச்சரிக்கை:** இந்த சுருக்கம் செயற்கை நுண்ணறிவு (AI) மூலம் "
    "உருவாக்கப்பட்டது. இது உங்கள் அறிக்கையை புரிந்துகொள்ள உதவும் நோக்கத்திற்காக மட்டுமே. "
    "இது தொழில்முறை மருத்துவ விளக்கத்திற்கு மாற்றாகாது. "
    "தயவுசெய்து உங்கள் மருத்துவரிடம் முடிவுகளை விவாதிக்கவும்."
)


# ─── Caregiver / Patient Companion ────────────────────────────────────────────

RELATIONSHIP_OPTIONS = [
    "Father",
    "Mother",
    "Brother",
    "Sister",
    "Spouse",
    "Son",
    "Daughter",
    "Friend",
    "Guardian",
    "Other",
]

NOTIFICATION_METHODS = [
    "Email",
    "SMS",
    "WhatsApp",
    "All",
]

CAREGIVER_COLORS = [
    ("linear-gradient(135deg,#EFF6FF,#DBEAFE)", "1px solid #BFDBFE", "#1D4ED8"),
    ("linear-gradient(135deg,#F0FDF4,#DCFCE7)", "1px solid #BBF7D0", "#15803D"),
    ("linear-gradient(135deg,#FFF7ED,#FED7AA)", "1px solid #FDBA74", "#C2410C"),
    ("linear-gradient(135deg,#FDF4FF,#F5D0FE)", "1px solid #E879F9", "#7E22CE"),
    ("linear-gradient(135deg,#F0F9FF,#BAE6FD)", "1px solid #7DD3FC", "#0369A1"),
    ("linear-gradient(135deg,#FFF1F2,#FECDD3)", "1px solid #FDA4AF", "#BE123C"),
]

RELATIONSHIP_ICONS = {
    "Father":   "👨",
    "Mother":   "👩",
    "Brother":  "👦",
    "Sister":   "👧",
    "Spouse":   "💑",
    "Son":      "🧒",
    "Daughter": "👧",
    "Friend":   "🤝",
    "Guardian": "🛡️",
    "Other":    "👤",
}

NOTIFICATION_CHANNEL_ICONS = {
    "Email":    "📧",
    "SMS":      "📱",
    "WhatsApp": "💬",
    "All":      "🔔",
}
