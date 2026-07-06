"""
General helper utilities for Healthcare AI Assistant.
"""

import logging
from datetime import datetime, date
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def format_date(date_str: str) -> str:
    """Convert YYYY-MM-DD string to DD Mon YYYY display format."""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return d.strftime("%d %b %Y")
    except ValueError:
        return date_str


def format_time_12h(time_str: str) -> str:
    """Convert HH:MM (24h) to 12-hour format with AM/PM."""
    try:
        t = datetime.strptime(time_str, "%H:%M")
        return t.strftime("%I:%M %p")
    except ValueError:
        return time_str


def date_to_str(d: date) -> str:
    """Convert a date object to YYYY-MM-DD string."""
    return d.strftime("%Y-%m-%d")


def str_to_date(date_str: str) -> Optional[date]:
    """Parse a YYYY-MM-DD string into a date object, or None on failure."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def get_status_emoji(status: str) -> str:
    """Return an emoji representing appointment/reminder status."""
    mapping = {
        "scheduled": "📅",
        "completed": "✅",
        "cancelled": "❌",
        "rescheduled": "🔄",
        "active": "🟢",
        "inactive": "⚫",
    }
    return mapping.get(status.lower(), "❓")


def truncate_text(text: str, max_len: int = 80) -> str:
    """Truncate text to max_len characters, appending ellipsis if needed."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


def safe_get(data: Dict, key: str, default: Any = "") -> Any:
    """Safely get a value from a dict with a default."""
    return data.get(key, default)


def group_by_key(items: List[Dict], key: str) -> Dict[str, List[Dict]]:
    """Group a list of dicts by a given key value."""
    result: Dict[str, List[Dict]] = {}
    for item in items:
        k = str(item.get(key, "Unknown"))
        result.setdefault(k, []).append(item)
    return result


def appointments_to_display_rows(appointments: List[Dict]) -> List[Dict]:
    """Transform raw appointment dicts into display-friendly format."""
    rows = []
    for apt in appointments:
        rows.append({
            "ID": apt.get("id", ""),
            "Patient": apt.get("patient_name", ""),
            "Doctor": apt.get("doctor_name", ""),
            "Specialization": apt.get("specialization", ""),
            "Date": format_date(apt.get("appointment_date", "")),
            "Time": format_time_12h(apt.get("appointment_time", "")),
            "Status": f"{get_status_emoji(apt.get('status', ''))} {apt.get('status', '').capitalize()}",
        })
    return rows


def reminders_to_display_rows(reminders: List[Dict]) -> List[Dict]:
    """Transform raw reminder dicts into display-friendly format."""
    rows = []
    for r in reminders:
        rows.append({
            "ID": r.get("id", ""),
            "Medicine": r.get("medicine_name", ""),
            "Dosage": r.get("dosage", ""),
            "Time": format_time_12h(r.get("reminder_time", "")),
            "Frequency": r.get("frequency", ""),
            "Patient": r.get("patient_name", "") or "—",
            "Notes": truncate_text(r.get("notes", "") or "—"),
        })
    return rows
