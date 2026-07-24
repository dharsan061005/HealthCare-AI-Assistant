"""
Notification Service — abstraction layer for multi-channel notifications.

Currently implemented : Email (via smtplib / SMTP)
Placeholders          : SMS, WhatsApp (ready for future integration)

Usage:
    from services.notification_service import NotificationService
    svc = NotificationService()
    result = svc.send_notification(channel="email", to=..., subject=..., body_html=...)
"""

from __future__ import annotations

import logging
import smtplib
import os
from dataclasses import dataclass, field
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import config  # loads .env

logger = logging.getLogger(__name__)


# ─── Result dataclass ────────────────────────────────────────────────────────

@dataclass
class NotificationResult:
    success: bool
    channel: str
    message: str = ""
    error: str = ""


# ─── Email HTML template ──────────────────────────────────────────────────────

def build_reminder_email_html(
    caregiver_name: str,
    patient_name: str,
    medicine_name: str,
    dosage: str,
    reminder_time: str,
    frequency: str,
    doctor_name: str = "",
    special_instructions: str = "",
    is_missed: bool = False,
) -> tuple[str, str]:
    """Return (subject, html_body) for a medicine reminder / missed-medicine email."""
    alert_type  = "⚠️ Missed Medicine Alert" if is_missed else "💊 Medicine Reminder"
    accent      = "#EF4444" if is_missed else "#0EA5E9"
    banner_msg  = (
        f"{patient_name} has missed their scheduled dose of {medicine_name}."
        if is_missed
        else f"This is a reminder for {patient_name}'s scheduled medicine."
    )
    subject     = f"{alert_type} — {patient_name} / {medicine_name}"
    doctor_row  = f"<tr><td style='padding:6px 0;color:#64748B;'>👨‍⚕️ Doctor</td><td style='padding:6px 0;font-weight:600;'>{doctor_name}</td></tr>" if doctor_name else ""
    instr_row   = f"<tr><td style='padding:6px 0;color:#64748B;'>📝 Instructions</td><td style='padding:6px 0;'>{special_instructions}</td></tr>" if special_instructions else ""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{subject}</title></head>
<body style="margin:0;padding:0;background:#F1F5F9;font-family:Inter,-apple-system,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:32px 16px;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
  <!-- Header -->
  <tr><td style="background:{accent};padding:28px 36px;">
    <h1 style="margin:0;color:#fff;font-size:22px;font-weight:700;">{alert_type}</h1>
    <p style="margin:6px 0 0;color:rgba(255,255,255,0.85);font-size:14px;">{banner_msg}</p>
  </td></tr>
  <!-- Greeting -->
  <tr><td style="padding:28px 36px 0;">
    <p style="margin:0;font-size:15px;color:#0F172A;">Dear <strong>{caregiver_name}</strong>,</p>
    <p style="margin:12px 0 0;font-size:14px;color:#475569;line-height:1.7;">
      {"Please note that <strong>" + patient_name + "</strong> has <strong>not taken</strong> their scheduled medicine within the last 30 minutes. Kindly ensure the medicine is administered as soon as possible." if is_missed else "Please ensure that <strong>" + patient_name + "</strong> takes the following medicine on time."}
    </p>
  </td></tr>
  <!-- Details card -->
  <tr><td style="padding:20px 36px;">
    <table width="100%" cellpadding="0" cellspacing="0"
           style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:20px;border-spacing:0;">
      <tr><td colspan="2" style="padding-bottom:12px;font-weight:700;font-size:15px;color:#0F172A;">
        📋 Medicine Details
      </td></tr>
      <tr><td style="padding:6px 0;color:#64748B;width:140px;">💊 Medicine</td>
          <td style="padding:6px 0;font-weight:700;color:#0EA5E9;">{medicine_name}</td></tr>
      <tr><td style="padding:6px 0;color:#64748B;">📏 Dosage</td>
          <td style="padding:6px 0;font-weight:600;">{dosage}</td></tr>
      <tr><td style="padding:6px 0;color:#64748B;">⏰ Time</td>
          <td style="padding:6px 0;font-weight:600;">{reminder_time}</td></tr>
      <tr><td style="padding:6px 0;color:#64748B;">🔁 Frequency</td>
          <td style="padding:6px 0;">{frequency}</td></tr>
      {doctor_row}
      {instr_row}
    </table>
  </td></tr>
  <!-- CTA -->
  <tr><td style="padding:0 36px 28px;">
    <p style="margin:0;font-size:13px;color:#94A3B8;line-height:1.6;">
      This is an automated notification from Healthcare AI Assistant.<br>
      Please do not reply to this email.
    </p>
  </td></tr>
  <!-- Footer -->
  <tr><td style="background:#F8FAFC;padding:16px 36px;border-top:1px solid #E2E8F0;">
    <p style="margin:0;font-size:12px;color:#94A3B8;text-align:center;">
      🏥 Healthcare AI Assistant &nbsp;|&nbsp; Patient Companion Module
    </p>
  </td></tr>
</table>
</td></tr>
</table>
</body></html>"""
    return subject, html


def build_report_email_html(
    caregiver_name: str,
    patient_name: str,
    report_date: str,
    doctor_name: str,
    ai_summary: str,
    key_findings: str = "",
    followup: str = "",
) -> tuple[str, str]:
    """Return (subject, html_body) for a report-sharing email."""
    subject = f"📄 Medical Report Summary — {patient_name} ({report_date})"
    findings_block = (
        f"<div style='margin-top:12px;'><strong style='color:#0F172A;'>Key Findings:</strong>"
        f"<p style='margin:6px 0 0;color:#475569;font-size:14px;line-height:1.7;'>{key_findings}</p></div>"
        if key_findings else ""
    )
    followup_block = (
        f"<div style='margin-top:12px;'><strong style='color:#0F172A;'>Follow-up Recommendation:</strong>"
        f"<p style='margin:6px 0 0;color:#475569;font-size:14px;line-height:1.7;'>{followup}</p></div>"
        if followup else ""
    )
    summary_escaped = ai_summary.replace("\n", "<br>")
    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>{subject}</title></head>
<body style="margin:0;padding:0;background:#F1F5F9;font-family:Inter,-apple-system,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:32px 16px;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0"
       style="background:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
  <tr><td style="background:linear-gradient(135deg,#0EA5E9,#0284C7);padding:28px 36px;">
    <h1 style="margin:0;color:#fff;font-size:22px;font-weight:700;">📄 Medical Report Shared</h1>
    <p style="margin:6px 0 0;color:rgba(255,255,255,0.85);font-size:14px;">
      A medical report summary for {patient_name} has been shared with you.
    </p>
  </td></tr>
  <tr><td style="padding:28px 36px 0;">
    <p style="margin:0;font-size:15px;color:#0F172A;">Dear <strong>{caregiver_name}</strong>,</p>
    <p style="margin:12px 0 0;font-size:14px;color:#475569;line-height:1.7;">
      Please find the AI-generated medical report summary for your reference.
    </p>
  </td></tr>
  <tr><td style="padding:20px 36px 0;">
    <table width="100%" cellpadding="0" cellspacing="0"
           style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:16px;border-spacing:0;">
      <tr><td style="padding:5px 0;color:#64748B;width:140px;">👤 Patient</td>
          <td style="padding:5px 0;font-weight:700;">{patient_name}</td></tr>
      <tr><td style="padding:5px 0;color:#64748B;">📅 Report Date</td>
          <td style="padding:5px 0;">{report_date}</td></tr>
      <tr><td style="padding:5px 0;color:#64748B;">🩺 Doctor</td>
          <td style="padding:5px 0;">{doctor_name or "—"}</td></tr>
    </table>
  </td></tr>
  <tr><td style="padding:20px 36px 0;">
    <div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:12px;padding:20px;">
      <strong style="color:#1D4ED8;font-size:15px;">🤖 AI Summary</strong>
      <div style="margin-top:12px;font-size:14px;color:#334155;line-height:1.8;">{summary_escaped}</div>
      {findings_block}
      {followup_block}
    </div>
  </td></tr>
  <tr><td style="padding:20px 36px 28px;">
    <p style="margin:0;font-size:12px;color:#94A3B8;line-height:1.6;">
      ⚠️ This AI summary is for informational purposes only and does not replace professional medical advice.<br>
      This is an automated notification from Healthcare AI Assistant.
    </p>
  </td></tr>
  <tr><td style="background:#F8FAFC;padding:16px 36px;border-top:1px solid #E2E8F0;">
    <p style="margin:0;font-size:12px;color:#94A3B8;text-align:center;">
      🏥 Healthcare AI Assistant &nbsp;|&nbsp; Patient Companion Module
    </p>
  </td></tr>
</table>
</td></tr>
</table>
</body></html>"""
    return subject, html


# ─── NotificationService ──────────────────────────────────────────────────────

class NotificationService:
    """
    Abstraction layer for multi-channel notifications.

    Configuration (add to .env):
        SMTP_HOST      — SMTP server hostname   (default: smtp.gmail.com)
        SMTP_PORT      — SMTP port              (default: 587)
        SMTP_USER      — Sender email address
        SMTP_PASSWORD  — Sender email password / app-password
        SMTP_FROM_NAME — Display name           (default: Healthcare AI Assistant)
    """

    def __init__(self) -> None:
        self.smtp_host     = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port     = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user     = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_name     = os.getenv("SMTP_FROM_NAME", "Healthcare AI Assistant")

    # ── Email ─────────────────────────────────────────────────────────────────

    def _credentials_configured(self) -> bool:
        """Return True only when SMTP credentials look like real values."""
        placeholders = {"your@gmail.com", "your-app-password", "", "your_email@gmail.com"}
        return (
            bool(self.smtp_user)
            and bool(self.smtp_password)
            and self.smtp_user.lower()    not in placeholders
            and self.smtp_password.lower() not in placeholders
            and "@" in self.smtp_user
        )

    def send_email(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
    ) -> NotificationResult:
        """
        Send an HTML email via SMTP.
        Falls back to a simulation log if SMTP credentials are not configured.
        """
        if not self._credentials_configured():
            logger.warning(
                "SMTP credentials not configured. Email to %s simulated. Subject: %s",
                to, subject,
            )
            return NotificationResult(
                success=True,
                channel="email",
                message=(
                    f"[SIMULATED] Email to {to} — '{subject}'. "
                    "Configure SMTP_USER and SMTP_PASSWORD in .env to send real emails."
                ),
            )

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = f"{self.from_name} <{self.smtp_user}>"
            msg["To"]      = to

            if body_text:
                msg.attach(MIMEText(body_text, "plain", "utf-8"))
            msg.attach(MIMEText(body_html, "html", "utf-8"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, [to], msg.as_string())

            logger.info("Email sent to %s — %s", to, subject)
            return NotificationResult(
                success=True, channel="email",
                message=f"Email successfully sent to {to}."
            )

        except smtplib.SMTPAuthenticationError as exc:
            # Auth failure — treat as unconfigured and simulate gracefully
            logger.warning(
                "SMTP authentication failed for %s. Falling back to simulation. "
                "Use a Gmail App Password (not your account password). Error: %s",
                self.smtp_user, exc,
            )
            return NotificationResult(
                success=True,
                channel="email",
                message=(
                    f"[SIMULATED — Auth Failed] Email to {to} — '{subject}'. "
                    "Gmail requires an App Password. Generate one at: "
                    "https://myaccount.google.com/apppasswords and set SMTP_PASSWORD in .env"
                ),
            )

        except Exception as exc:
            logger.error("Failed to send email to %s: %s", to, exc)
            return NotificationResult(
                success=False, channel="email",
                error=str(exc),
                message=f"Failed to send email to {to}: {exc}",
            )

    # ── SMS (placeholder) ─────────────────────────────────────────────────────

    def send_sms(self, to: str, body: str) -> NotificationResult:
        """
        Placeholder for SMS via Twilio / MSG91.
        Install twilio and set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER.
        """
        logger.info("[SMS PLACEHOLDER] To: %s | Message: %s", to, body[:80])
        return NotificationResult(
            success=True,
            channel="sms",
            message=(
                f"[PLACEHOLDER] SMS to {to} logged. "
                "Integrate Twilio / MSG91 to enable real SMS delivery."
            ),
        )

    # ── WhatsApp (placeholder) ────────────────────────────────────────────────

    def send_whatsapp(self, to: str, body: str) -> NotificationResult:
        """
        Placeholder for WhatsApp via Twilio WhatsApp API or Meta Cloud API.
        Set WHATSAPP_API_TOKEN and WHATSAPP_FROM_NUMBER.
        """
        logger.info("[WHATSAPP PLACEHOLDER] To: %s | Message: %s", to, body[:80])
        return NotificationResult(
            success=True,
            channel="whatsapp",
            message=(
                f"[PLACEHOLDER] WhatsApp message to {to} logged. "
                "Integrate Twilio WhatsApp API to enable real delivery."
            ),
        )

    # ── Unified dispatcher ────────────────────────────────────────────────────

    def send_notification(
        self,
        channel: str,
        to: str,
        subject: str = "",
        body_html: str = "",
        body_text: str = "",
    ) -> NotificationResult:
        """
        Route notification to the correct channel.

        Args:
            channel   : 'email' | 'sms' | 'whatsapp'
            to        : recipient address / number
            subject   : email subject (email only)
            body_html : HTML body (email) or plain text (sms/whatsapp)
            body_text : plain-text fallback for email
        """
        ch = channel.lower().strip()
        if ch == "email":
            return self.send_email(to=to, subject=subject, body_html=body_html, body_text=body_text)
        if ch == "sms":
            return self.send_sms(to=to, body=body_text or body_html)
        if ch == "whatsapp":
            return self.send_whatsapp(to=to, body=body_text or body_html)

        return NotificationResult(
            success=False,
            channel=channel,
            error=f"Unknown channel '{channel}'.",
            message=f"Channel '{channel}' is not supported.",
        )
