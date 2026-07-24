"""
Agent Router
Maps sidebar navigation choices to the correct agent render function.

Navigation groups:
  👨‍⚕️ PATIENT SERVICES — Appointments, reminders, caregivers, family
  🤖 AI HEALTH TOOLS  — Conversational AI
  ⚙️ SETTINGS
"""

import logging
from typing import Callable

logger = logging.getLogger(__name__)

# ── Patient Services ──────────────────────────────────────────────────────────
PATIENT_SERVICES = [
    "nav_family",
    "nav_appointment",
    "nav_symptom",
    "nav_report",
    "nav_reminders",
    "nav_caregivers",
]

# ── AI Health Tools ───────────────────────────────────────────────────────────
AI_HEALTH_TOOLS = [
    "nav_ai_assistant",
    "nav_medicine_info",
    "nav_dictionary",
    "nav_emergency",
]

# ── Settings ──────────────────────────────────────────────────────────────────
SETTINGS_PAGES = [
    "nav_settings",
]

# All nav items flat (used for index look-up)
NAV_ITEMS = PATIENT_SERVICES + AI_HEALTH_TOOLS + SETTINGS_PAGES

# Default landing page
DEFAULT_PAGE = "nav_appointment"


def get_agent_renderer(page: str) -> Callable:
    """
    Return the render() function for the selected page.
    """
    # ── Family Management ─────────────────────────────────────────────────────
    if page == "nav_family":
        from agents.family_management import render
        return render

    # ── Patient Services ──────────────────────────────────────────────────────
    if page == "nav_appointment":
        from agents.appointment_agent import render
        return render

    if page == "nav_symptom":
        from agents.symptom_checker_agent import render
        return render

    if page == "nav_report":
        from agents.report_summarizer_agent import render
        return render

    if page == "nav_reminders":
        from agents.prescription_reminder_agent import render
        return render

    if page == "nav_caregivers":
        from agents.caregiver_agent import render
        return render

    # ── AI Health Tools ───────────────────────────────────────────────────────
    if page == "nav_ai_assistant":
        from agents.ai_health_assistant_agent import render
        return render

    if page == "nav_medicine_info":
        from agents.medicine_info_agent import render
        return render

    if page == "nav_dictionary":
        from agents.medical_dictionary_agent import render
        return render

    if page == "nav_emergency":
        from agents.emergency_help_agent import render
        return render

    # ── Settings ──────────────────────────────────────────────────────────────
    if page == "nav_settings":
        from agents.settings_agent import render
        return render

    logger.error("Unknown page requested: %s", page)
    raise ValueError(f"Unknown page: '{page}'. Valid pages: {NAV_ITEMS}")

