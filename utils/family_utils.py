"""
Family Management Utilities — Healthcare AI Assistant
Constants, display helpers, validators, and AI prompt builders.
"""

from __future__ import annotations
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════

RELATIONSHIP_OPTIONS = [
    "Father", "Mother", "Son", "Daughter", "Spouse / Partner",
    "Brother", "Sister", "Grandfather", "Grandmother",
    "Uncle", "Aunt", "Nephew", "Niece", "Cousin",
    "Father-in-law", "Mother-in-law", "Guardian", "Other",
]

GENDER_OPTIONS = ["Male", "Female", "Non-binary", "Prefer not to say"]

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"]

REPORT_TYPES = [
    "Blood Test", "Urine Test", "X-Ray", "MRI Scan", "CT Scan",
    "Ultrasound", "ECG / EKG", "Echo Cardiogram", "Lipid Profile",
    "Thyroid Panel", "Diabetes Panel", "Liver Function Test",
    "Kidney Function Test", "Complete Blood Count (CBC)",
    "COVID-19 Test", "Allergy Test", "Genetic Test", "Other",
]

SPECIALIZATIONS = [
    "Cardiology", "Dermatology", "ENT", "General Medicine",
    "Gynecology", "Neurology", "Ophthalmology", "Orthopedics",
    "Pediatrics", "Psychiatry", "Pulmonology", "Urology",
    "Endocrinology", "Gastroenterology", "Oncology", "Other",
]

FREQUENCY_OPTIONS = [
    "Once daily", "Twice daily", "Three times daily",
    "Every 6 hours", "Every 8 hours", "Every 12 hours",
    "Weekly", "Fortnightly", "Monthly", "As needed",
]

APPOINTMENT_STATUSES = ["scheduled", "completed", "cancelled", "rescheduled", "missed"]

# Priority labels for emergency contacts
PRIORITY_LABELS = {1: "🥇 Primary", 2: "🥈 Secondary", 3: "🥉 Tertiary"}

# Emoji avatars mapped to relationship
RELATIONSHIP_EMOJIS: Dict[str, str] = {
    "Father":           "👨",
    "Mother":           "👩",
    "Son":              "👦",
    "Daughter":         "👧",
    "Spouse / Partner": "💑",
    "Brother":          "🧑",
    "Sister":           "👩",
    "Grandfather":      "👴",
    "Grandmother":      "👵",
    "Uncle":            "👨",
    "Aunt":             "👩",
    "Nephew":           "👦",
    "Niece":            "👧",
    "Cousin":           "🧑",
    "Father-in-law":    "👨",
    "Mother-in-law":    "👩",
    "Guardian":         "🛡️",
    "Other":            "👤",
}

# Member card accent colours (cycles by member ID)
MEMBER_CARD_COLORS = [
    {"bg": "rgba(59,130,246,0.12)",  "border": "rgba(59,130,246,0.25)",  "accent": "#60A5FA"},
    {"bg": "rgba(34,197,94,0.12)",   "border": "rgba(34,197,94,0.25)",   "accent": "#4ADE80"},
    {"bg": "rgba(168,85,247,0.12)",  "border": "rgba(168,85,247,0.25)",  "accent": "#C084FC"},
    {"bg": "rgba(245,158,11,0.12)",  "border": "rgba(245,158,11,0.25)",  "accent": "#FCD34D"},
    {"bg": "rgba(239,68,68,0.12)",   "border": "rgba(239,68,68,0.25)",   "accent": "#F87171"},
    {"bg": "rgba(6,182,212,0.12)",   "border": "rgba(6,182,212,0.25)",   "accent": "#67E8F9"},
]

STATUS_COLORS: Dict[str, str] = {
    "scheduled":   "#3B82F6",
    "completed":   "#22C55E",
    "cancelled":   "#EF4444",
    "rescheduled": "#F59E0B",
    "missed":      "#8B5CF6",
}

STATUS_EMOJIS: Dict[str, str] = {
    "scheduled":   "📅",
    "completed":   "✅",
    "cancelled":   "❌",
    "rescheduled": "🔄",
    "missed":      "⚠️",
}

HEALTH_GRADE_CONFIG = [
    (90, "Excellent", "#22C55E", "🏆"),
    (75, "Good",      "#3B82F6", "👍"),
    (60, "Fair",      "#F59E0B", "⚠️"),
    (40, "Poor",      "#EF4444", "🔴"),
    (0,  "Critical",  "#7F1D1D", "🚨"),
]

# ═══════════════════════════════════════════════════════
# DISPLAY HELPERS
# ═══════════════════════════════════════════════════════

def fmt_date(date_str: str) -> str:
    """YYYY-MM-DD → DD Mon YYYY"""
    try:
        return datetime.strptime(date_str[:10], "%Y-%m-%d").strftime("%d %b %Y")
    except Exception:
        return date_str or "—"


def fmt_time(time_str: str) -> str:
    """HH:MM → HH:MM AM/PM"""
    try:
        return datetime.strptime(time_str, "%H:%M").strftime("%I:%M %p")
    except Exception:
        return time_str or "—"


def age_from_dob(dob_str: str) -> Optional[int]:
    """Return age in years from a YYYY-MM-DD string, or None."""
    try:
        dob = datetime.strptime(dob_str[:10], "%Y-%m-%d").date()
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except Exception:
        return None


def member_card_color(member_id: int) -> Dict[str, str]:
    return MEMBER_CARD_COLORS[member_id % len(MEMBER_CARD_COLORS)]


def member_emoji(relationship: str) -> str:
    return RELATIONSHIP_EMOJIS.get(relationship, "👤")


def status_emoji(status: str) -> str:
    return STATUS_EMOJIS.get(status.lower(), "❓")


def status_color(status: str) -> str:
    return STATUS_COLORS.get(status.lower(), "#64748B")


def health_grade(score: int) -> Tuple[str, str, str]:
    """Return (label, hex_color, emoji) for a 0-100 score."""
    for threshold, label, color, emoji in HEALTH_GRADE_CONFIG:
        if score >= threshold:
            return label, color, emoji
    return "Critical", "#7F1D1D", "🚨"


def bmi_category(weight_kg: float, height_cm: float) -> Tuple[float, str, str]:
    """Return (bmi_value, category_label, hex_color)."""
    if height_cm <= 0:
        return 0.0, "N/A", "#64748B"
    bmi = weight_kg / ((height_cm / 100) ** 2)
    if bmi < 18.5:
        return round(bmi, 1), "Underweight", "#F59E0B"
    if bmi < 25:
        return round(bmi, 1), "Normal", "#22C55E"
    if bmi < 30:
        return round(bmi, 1), "Overweight", "#F97316"
    return round(bmi, 1), "Obese", "#EF4444"


def bp_category(systolic: int, diastolic: int) -> Tuple[str, str]:
    """Return (category_label, hex_color) for blood pressure."""
    if systolic < 90 or diastolic < 60:
        return "Low (Hypotension)", "#F59E0B"
    if systolic <= 120 and diastolic <= 80:
        return "Normal", "#22C55E"
    if systolic <= 130 and diastolic <= 80:
        return "Elevated", "#84CC16"
    if systolic <= 140 or diastolic <= 90:
        return "High Stage 1", "#F97316"
    return "High Stage 2", "#EF4444"

# ═══════════════════════════════════════════════════════
# DATA → DISPLAY ROW TRANSFORMERS
# ═══════════════════════════════════════════════════════

def members_to_rows(members: List[Dict]) -> List[Dict]:
    rows = []
    for m in members:
        rows.append({
            "ID":           m.get("id", ""),
            "Name":         m.get("full_name", ""),
            "Relationship": m.get("relationship", ""),
            "Age":          m.get("age") or (age_from_dob(m.get("date_of_birth", "")) or "—"),
            "Gender":       m.get("gender", "—") or "—",
            "Blood Group":  m.get("blood_group", "—") or "—",
            "Phone":        m.get("phone", "—") or "—",
            "Conditions":   m.get("medical_conditions", "—") or "—",
        })
    return rows


def appointments_to_rows(appts: List[Dict]) -> List[Dict]:
    rows = []
    for a in appts:
        rows.append({
            "ID":      a.get("id", ""),
            "Member":  a.get("member_name", ""),
            "Doctor":  a.get("doctor_name", ""),
            "Specialization": a.get("specialization", "—") or "—",
            "Date":    fmt_date(a.get("appointment_date", "")),
            "Time":    fmt_time(a.get("appointment_time", "")),
            "Hospital": a.get("hospital", "—") or "—",
            "Purpose": a.get("purpose", "—") or "—",
            "Status":  f"{status_emoji(a.get('status',''))} {a.get('status','').capitalize()}",
        })
    return rows


def medicines_to_rows(meds: List[Dict]) -> List[Dict]:
    rows = []
    for m in meds:
        rows.append({
            "ID":        m.get("id", ""),
            "Member":    m.get("member_name", ""),
            "Medicine":  m.get("medicine_name", ""),
            "Dosage":    m.get("dosage", ""),
            "Frequency": m.get("frequency", ""),
            "Time":      fmt_time(m.get("reminder_time", "")),
            "Prescribed By": m.get("prescribed_by", "—") or "—",
            "End Date":  fmt_date(m.get("end_date", "")) if m.get("end_date") else "Ongoing",
        })
    return rows


def reports_to_rows(reports: List[Dict]) -> List[Dict]:
    rows = []
    for r in reports:
        rows.append({
            "ID":      r.get("id", ""),
            "Member":  r.get("member_name", ""),
            "Type":    r.get("report_type", ""),
            "Date":    fmt_date(r.get("report_date", "")),
            "Lab":     r.get("lab_name", "—") or "—",
            "Doctor":  r.get("doctor_name", "—") or "—",
            "Normal":  "✅ Yes" if r.get("is_normal") else "❌ No",
            "Has AI Summary": "✅" if r.get("ai_summary") else "—",
        })
    return rows


def vitals_to_rows(vitals: List[Dict]) -> List[Dict]:
    rows = []
    for v in vitals:
        bp = f"{v['bp_systolic']}/{v['bp_diastolic']}" if v.get("bp_systolic") else "—"
        rows.append({
            "Date":         fmt_date(v.get("recorded_date", "")),
            "Time":         v.get("recorded_time", "—"),
            "Member":       v.get("member_name", ""),
            "BP (mmHg)":    bp,
            "Heart Rate":   f"{v['heart_rate']} bpm" if v.get("heart_rate") else "—",
            "Temp (°C)":    v.get("temperature") or "—",
            "Weight (kg)":  v.get("weight_kg") or "—",
            "SpO2 (%)":     v.get("spo2") or "—",
            "Glucose (mg/dL)": v.get("blood_glucose") or "—",
        })
    return rows


# ═══════════════════════════════════════════════════════
# VALIDATORS
# ═══════════════════════════════════════════════════════

def validate_member_name(name: str) -> Tuple[bool, str]:
    name = name.strip()
    if not name:
        return False, "Name is required."
    if len(name) < 2:
        return False, "Name must be at least 2 characters."
    if len(name) > 80:
        return False, "Name must be 80 characters or fewer."
    return True, ""


def validate_phone(phone: str) -> Tuple[bool, str]:
    phone = phone.strip()
    if not phone:
        return True, ""   # optional in family context
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 7:
        return False, "Phone number must have at least 7 digits."
    return True, ""


def validate_age(age: Any) -> Tuple[bool, str]:
    try:
        a = int(age)
        if a < 0 or a > 130:
            return False, "Age must be between 0 and 130."
        return True, ""
    except (TypeError, ValueError):
        return True, ""   # age is optional


# ═══════════════════════════════════════════════════════
# AI PROMPT BUILDERS
# ═══════════════════════════════════════════════════════

def build_health_summary_prompt(member: Dict, vitals: List[Dict],
                                 medicines: List[Dict], reports: List[Dict]) -> str:
    name = member.get("full_name", "the family member")
    age  = member.get("age") or age_from_dob(member.get("date_of_birth", "")) or "unknown"
    gender = member.get("gender", "")
    conditions = member.get("medical_conditions", "") or "None recorded"
    allergies  = member.get("allergies", "") or "None recorded"

    med_list = ", ".join(m["medicine_name"] for m in medicines[:8]) if medicines else "None"
    report_types = ", ".join(r["report_type"] for r in reports[:5]) if reports else "None"

    vitals_str = "No recent vitals."
    if vitals:
        v = vitals[0]
        bp = f"{v.get('bp_systolic','?')}/{v.get('bp_diastolic','?')} mmHg" if v.get("bp_systolic") else "N/A"
        vitals_str = (
            f"BP: {bp} | HR: {v.get('heart_rate','N/A')} bpm | "
            f"Temp: {v.get('temperature','N/A')} °C | SpO2: {v.get('spo2','N/A')}% | "
            f"Weight: {v.get('weight_kg','N/A')} kg | Glucose: {v.get('blood_glucose','N/A')} mg/dL"
        )

    return f"""You are an empathetic AI health assistant. Provide a concise health summary for a family member.

Member: {name} | Age: {age} | Gender: {gender}
Known Conditions: {conditions}
Allergies: {allergies}
Current Medications: {med_list}
Recent Reports: {report_types}
Latest Vitals: {vitals_str}

Please provide:
1. **Overall Health Assessment** (2-3 sentences)
2. **Key Observations** (bullet points)
3. **Recommended Actions** (bullet points)
4. **Lifestyle Tips** tailored to their conditions

Keep the response friendly, clear, and actionable. End with a disclaimer that this is AI-generated
and not a substitute for professional medical advice."""


def build_recommendations_prompt(members: List[Dict]) -> str:
    if not members:
        return "No family members found. Please add family members first."
    summaries = []
    for m in members[:5]:
        age = m.get("age") or age_from_dob(m.get("date_of_birth", "")) or "?"
        summaries.append(
            f"- {m['full_name']} ({m['relationship']}, age {age}): "
            f"conditions: {m.get('medical_conditions','none') or 'none'}"
        )
    members_text = "\n".join(summaries)
    return f"""You are a family health advisor. Based on the following family profiles, provide
personalised health recommendations for the entire family.

Family Members:
{members_text}

Provide:
1. **Family-Wide Recommendations** (applicable to all)
2. **Individual Tips** for each member (brief, bullet-pointed)
3. **Preventive Screenings** to schedule based on ages and conditions
4. **Nutrition & Exercise** suggestions appropriate for the family

Be warm, practical, and specific. Add disclaimer at end."""


def build_ask_ai_prompt(member: Dict, question: str, context: Dict) -> str:
    name = member.get("full_name", "the family member")
    age  = member.get("age") or age_from_dob(member.get("date_of_birth", "")) or "unknown"
    conditions = member.get("medical_conditions", "") or "None"
    allergies  = member.get("allergies", "") or "None"
    meds = context.get("medicines", [])
    med_list = ", ".join(m["medicine_name"] for m in meds[:5]) if meds else "None"

    return f"""You are a knowledgeable and caring AI health assistant.

Context about the family member:
Name: {name} | Age: {age}
Medical Conditions: {conditions}
Allergies: {allergies}
Current Medications: {med_list}

User's Question: {question}

Answer clearly and compassionately. If the question requires professional evaluation, say so.
Always end with: "⚠️ This is AI-generated information. Please consult a qualified doctor for
medical decisions." """
