"""
Caregiver Service — business-logic layer.

Bridges the database layer (caregivers / notification_log) with the
NotificationService to build, send, and log notifications in one call.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from database import database as db
from services.notification_service import (
    NotificationService,
    NotificationResult,
    build_reminder_email_html,
    build_report_email_html,
)
from utils.helpers import format_time_12h

logger = logging.getLogger(__name__)

_svc = NotificationService()   # single shared instance


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _channels_for_preference(preference: str) -> List[str]:
    """Expand a notification preference into a list of channel strings."""
    mapping = {
        "Email":     ["email"],
        "SMS":       ["sms"],
        "WhatsApp":  ["whatsapp"],
        "All":       ["email", "sms", "whatsapp"],
    }
    return mapping.get(preference, ["email"])


# ─── Reminder notifications ───────────────────────────────────────────────────

def notify_caregivers_for_reminder(
    patient_name: str,
    medicine_name: str,
    dosage: str,
    reminder_time: str,
    frequency: str,
    doctor_name: str = "",
    special_instructions: str = "",
    is_missed: bool = False,
) -> List[Dict]:
    """
    Find all active caregivers for the patient and send them a reminder
    (or missed-medicine alert) through their preferred channels.

    Returns a list of result dicts with keys: caregiver_id, caregiver_name,
    channel, success, message.
    """
    caregivers = db.get_caregivers_for_patient(patient_name)
    if not caregivers:
        logger.info("No active caregivers found for patient '%s'.", patient_name)
        return []

    time_display = format_time_12h(reminder_time)
    results: List[Dict] = []

    for cg in caregivers:
        channels = _channels_for_preference(cg["notification_preference"])
        subject, html = build_reminder_email_html(
            caregiver_name=cg["caregiver_name"],
            patient_name=patient_name,
            medicine_name=medicine_name,
            dosage=dosage,
            reminder_time=time_display,
            frequency=frequency,
            doctor_name=doctor_name,
            special_instructions=special_instructions,
            is_missed=is_missed,
        )
        plain = (
            f"{'MISSED MEDICINE ALERT' if is_missed else 'Medicine Reminder'}\n\n"
            f"Dear {cg['caregiver_name']},\n\n"
            f"{'ALERT: ' + patient_name + ' has missed their scheduled dose.' if is_missed else ''}"
            f"{patient_name} should take {medicine_name} {dosage} at {time_display}.\n"
            f"Frequency: {frequency}\n"
            + (f"Doctor: {doctor_name}\n" if doctor_name else "")
            + (f"Instructions: {special_instructions}\n" if special_instructions else "")
            + "\nPlease ensure the medicine is taken on time.\n"
              "\n-- Healthcare AI Assistant"
        )
        notif_type = "missed_medicine" if is_missed else "reminder"

        for ch in channels:
            if ch == "email":
                result = _svc.send_email(
                    to=cg["email"], subject=subject,
                    body_html=html, body_text=plain,
                )
            elif ch == "sms":
                result = _svc.send_sms(to=cg["mobile_number"], body=plain)
            else:
                result = _svc.send_whatsapp(to=cg["mobile_number"], body=plain)

            status = "sent" if result.success else "failed"
            db.log_notification(
                caregiver_id=cg["id"],
                patient_name=patient_name,
                notification_type=notif_type,
                channel=ch,
                subject=subject,
                body=plain[:500],
                status=status,
            )
            results.append({
                "caregiver_id":   cg["id"],
                "caregiver_name": cg["caregiver_name"],
                "channel":        ch,
                "success":        result.success,
                "message":        result.message,
            })

    return results


# ─── Report sharing ───────────────────────────────────────────────────────────

def share_report_with_caregivers(
    patient_name: str,
    report_date: str,
    doctor_name: str,
    ai_summary: str,
    key_findings: str = "",
    followup: str = "",
) -> List[Dict]:
    """
    Send the AI report summary to all active caregivers of the patient.
    Only uses email channel regardless of preference (report sharing is email-only).
    """
    caregivers = db.get_caregivers_for_patient(patient_name)
    if not caregivers:
        return []

    results: List[Dict] = []

    for cg in caregivers:
        subject, html = build_report_email_html(
            caregiver_name=cg["caregiver_name"],
            patient_name=patient_name,
            report_date=report_date,
            doctor_name=doctor_name,
            ai_summary=ai_summary,
            key_findings=key_findings,
            followup=followup,
        )
        result = _svc.send_email(
            to=cg["email"], subject=subject, body_html=html,
        )
        status = "sent" if result.success else "failed"
        db.log_notification(
            caregiver_id=cg["id"],
            patient_name=patient_name,
            notification_type="report",
            channel="email",
            subject=subject,
            body=ai_summary[:500],
            status=status,
        )
        results.append({
            "caregiver_id":   cg["id"],
            "caregiver_name": cg["caregiver_name"],
            "email":          cg["email"],
            "success":        result.success,
            "message":        result.message,
        })

    return results


# ─── Dashboard stats ──────────────────────────────────────────────────────────

def get_dashboard_stats() -> Dict:
    """Return caregiver-related stats for the dashboard card."""
    return {
        "total_caregivers":   db.count_caregivers(active_only=True),
        "todays_reminders":   db.count_notifications_today(),
        "reports_shared":     db.count_notifications_by_type("report"),
        "missed_alerts":      db.count_notifications_by_type("missed_medicine"),
    }
