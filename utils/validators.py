"""
Input validation utilities for Healthcare AI Assistant.
"""

import re
from datetime import date, datetime
from typing import Optional, Tuple


def validate_patient_name(name: str) -> Tuple[bool, str]:
    """Validate that a patient name is non-empty and contains only valid characters."""
    name = name.strip()
    if not name:
        return False, "Patient name cannot be empty."
    if len(name) < 2:
        return False, "Patient name must be at least 2 characters."
    if len(name) > 100:
        return False, "Patient name must be under 100 characters."
    if not re.match(r"^[A-Za-z\s\.\-']+$", name):
        return False, "Patient name can only contain letters, spaces, hyphens, apostrophes, and periods."
    return True, ""


def validate_appointment_date(appointment_date: date) -> Tuple[bool, str]:
    """Validate that the appointment date is today or in the future."""
    today = date.today()
    if appointment_date < today:
        return False, "Appointment date cannot be in the past."
    # Don't allow booking more than 1 year ahead
    max_date = date(today.year + 1, today.month, today.day)
    if appointment_date > max_date:
        return False, "Appointment cannot be booked more than 1 year in advance."
    return True, ""


def validate_appointment_time(time_str: str) -> Tuple[bool, str]:
    """Validate time string in HH:MM format."""
    try:
        datetime.strptime(time_str, "%H:%M")
        return True, ""
    except ValueError:
        return False, f"Invalid time format '{time_str}'. Expected HH:MM (e.g., 09:00)."


def validate_medicine_name(name: str) -> Tuple[bool, str]:
    """Validate medicine name."""
    name = name.strip()
    if not name:
        return False, "Medicine name cannot be empty."
    if len(name) < 2:
        return False, "Medicine name must be at least 2 characters."
    if len(name) > 200:
        return False, "Medicine name must be under 200 characters."
    return True, ""


def validate_dosage(dosage: str) -> Tuple[bool, str]:
    """Validate dosage string."""
    dosage = dosage.strip()
    if not dosage:
        return False, "Dosage cannot be empty."
    if len(dosage) > 100:
        return False, "Dosage description too long (max 100 chars)."
    return True, ""


def validate_reminder_time(time_str: str) -> Tuple[bool, str]:
    """Validate reminder time in HH:MM format."""
    try:
        datetime.strptime(time_str, "%H:%M")
        return True, ""
    except ValueError:
        return False, f"Invalid time format '{time_str}'. Expected HH:MM (e.g., 08:30)."


def validate_symptoms_input(text: str) -> Tuple[bool, str]:
    """Validate that symptom input has meaningful content."""
    text = text.strip()
    if not text:
        return False, "Please describe your symptoms."
    if len(text) < 5:
        return False, "Please provide more detail about your symptoms."
    if len(text) > 2000:
        return False, "Symptom description too long. Please limit to 2000 characters."
    return True, ""
