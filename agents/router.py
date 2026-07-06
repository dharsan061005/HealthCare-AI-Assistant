"""
Agent Router
Maps sidebar navigation choices to the correct agent render function.
"""

import logging
from typing import Callable, Dict

logger = logging.getLogger(__name__)

# Navigation labels in display order
NAV_ITEMS = [
    "🏥 Hospital Information",
    "📅 Appointment Scheduling",
    "🩺 Symptom Checker",
    "📄 Report Summarizer",
    "💊 Prescription Reminders",
]

# Default landing page
DEFAULT_PAGE = "🏥 Hospital Information"


def get_agent_renderer(page: str) -> Callable:
    """
    Return the render() function for the selected page.

    Args:
        page: The navigation label string.

    Returns:
        A callable render() function from the corresponding agent module.

    Raises:
        ValueError: If the page name is not recognized.
    """
    # Lazy imports to keep startup fast and avoid circular imports
    if page == "🏥 Hospital Information":
        from agents.hospital_information_agent import render
        return render

    if page == "📅 Appointment Scheduling":
        from agents.appointment_agent import render
        return render

    if page == "🩺 Symptom Checker":
        from agents.symptom_checker_agent import render
        return render

    if page == "📄 Report Summarizer":
        from agents.report_summarizer_agent import render
        return render

    if page == "💊 Prescription Reminders":
        from agents.prescription_reminder_agent import render
        return render

    logger.error("Unknown page requested: %s", page)
    raise ValueError(f"Unknown page: '{page}'. Valid pages: {NAV_ITEMS}")
