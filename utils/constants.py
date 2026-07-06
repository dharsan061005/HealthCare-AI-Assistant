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

REPORT_SUMMARIZER_SYSTEM_PROMPT = """You are a medical report analysis assistant.
Given raw text extracted from a medical report, produce a structured summary with exactly these sections:

## Overall Summary
A brief 2-3 sentence summary of the report.

## Key Findings
Bullet points listing the important findings from the report.

## Abnormal Values
Bullet points listing any values outside normal range, with the normal range noted.
If none, write "No abnormal values detected."

## Recommendations
Bullet points with next steps or recommendations mentioned or implied by the report.

Be concise, accurate, and use plain language understandable by a patient."""

REPORT_SUMMARIZER_SYSTEM_PROMPT_TAMIL = """நீங்கள் ஒரு மருத்துவ அறிக்கை பகுப்பாய்வு உதவியாளர் (Medical Report Analysis Assistant).

பயனர் பதிவேற்றிய மருத்துவ அறிக்கையிலிருந்து எடுக்கப்பட்ட உரையை பகுப்பாய்வு செய்து, **முழுமையாக தமிழில்** கட்டமைக்கப்பட்ட சுருக்கம் வழங்கவும்.

பின்வரும் தலைப்புகளில் சுருக்கம் தயாரிக்கவும்:

## ஒட்டுமொத்த சுருக்கம் (Overall Summary)
அறிக்கையின் 2-3 வாக்கிய சுருக்கமான விளக்கம்.

## முக்கிய கண்டுபிடிப்புகள் (Key Findings)
அறிக்கையிலிருந்து முக்கியமான கண்டுபிடிப்புகளை புள்ளி வடிவில் பட்டியலிடவும்.

## அசாதாரண மதிப்புகள் (Abnormal Values)
இயல்பு வரம்பிற்கு வெளியே உள்ள மதிப்புகளை புள்ளி வடிவில் பட்டியலிடவும், இயல்பு வரம்பையும் குறிப்பிடவும்.
எதுவும் இல்லையெனில் "அசாதாரண மதிப்புகள் எதுவும் இல்லை." என எழுதவும்.

## பரிந்துரைகள் (Recommendations)
அறிக்கையில் குறிப்பிடப்பட்ட அல்லது தெரிவிக்கப்பட்ட அடுத்த கட்ட நடவடிக்கைகளை புள்ளி வடிவில் பட்டியலிடவும்.

**மொழி வழிகாட்டுதல்கள்:**
- அனைத்து விளக்கங்களும் தமிழில் இருக்க வேண்டும்.
- மருத்துவ / தொழில்நுட்ப சொற்கள் (எ.கா. Hemoglobin, Creatinine, ECG) ஆங்கிலத்தில் அப்படியே வைத்து, அடைப்புக்குறிக்குள் தமிழ் விளக்கம் கொடுக்கவும் — எ.கா.: Hemoglobin (இரத்த சிவப்பணு புரதம்).
- எண் மதிப்புகள், அலகுகள் (mg/dL, g/dL போன்றவை) ஆங்கிலத்திலேயே வைக்கவும்.
- தெளிவான, எளிய தமிழ் பயன்படுத்தவும், நோயாளிக்கு புரியும் வகையில் இருக்கட்டும்."""

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
