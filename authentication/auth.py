"""
Authentication Core — Healthcare AI Assistant
Handles password hashing, verification, OTP generation, and login logic.
"""

import bcrypt
import random
import string
import logging
from typing import Optional, Tuple, Dict

from authentication.auth_db import (
    get_user_by_email,
    create_user,
    update_last_login,
    update_password,
    email_exists,
    store_otp,
    verify_otp,
)

logger = logging.getLogger(__name__)


# ─── Password helpers ────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Hash a plain-text password with bcrypt (work factor 12)."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def check_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception as exc:
        logger.error("Password check failed: %s", exc)
        return False


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Enforce strong password rules:
      - At least 8 characters
      - At least one uppercase letter
      - At least one lowercase letter
      - At least one digit
      - At least one special character
    Returns (ok, error_message).
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number."
    special = set("!@#$%^&*()_+-=[]{}|;':\",./<>?")
    if not any(c in special for c in password):
        return False, "Password must contain at least one special character (!@#$%^&* …)."
    return True, ""


def password_strength_label(password: str) -> Tuple[str, str]:
    """
    Returns (label, colour) for a password strength indicator.
    label:  'Weak' | 'Fair' | 'Good' | 'Strong'
    colour: hex string
    """
    score = 0
    if len(password) >= 8:    score += 1
    if len(password) >= 12:   score += 1
    if any(c.isupper() for c in password): score += 1
    if any(c.islower() for c in password): score += 1
    if any(c.isdigit() for c in password): score += 1
    special = set("!@#$%^&*()_+-=[]{}|;':\",./<>?")
    if any(c in special for c in password): score += 1

    if score <= 2:   return "Weak",   "#EF4444"
    if score <= 3:   return "Fair",   "#F59E0B"
    if score <= 4:   return "Good",   "#0EA5E9"
    return               "Strong", "#10B981"


# ─── OTP helpers ─────────────────────────────────────────────────────────────

def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP of the given length."""
    return "".join(random.choices(string.digits, k=length))


def send_otp(email: str) -> Tuple[bool, str]:
    """
    Generate and persist an OTP for the email.
    In production, plug in a real email service here.
    Returns (success, otp_code).  The caller decides what to show.
    """
    if not email_exists(email):
        # Don't reveal whether the email is registered
        return False, ""
    otp = generate_otp()
    store_otp(email, otp, ttl_minutes=10)
    logger.info("OTP stored for %s (not emailed — demo mode)", email)
    return True, otp


def confirm_otp(email: str, otp_code: str) -> bool:
    """Validate the OTP the user typed."""
    return verify_otp(email, otp_code.strip())


# ─── Login / Register logic ──────────────────────────────────────────────────

def attempt_login(email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    """
    Verify credentials.
    Returns (success, message, user_dict).
    """
    if not email or not password:
        return False, "Please enter your email and password.", None

    user = get_user_by_email(email.strip())
    if not user:
        return False, "No account found with that email address.", None

    if not check_password(password, user["password_hash"]):
        return False, "Incorrect password. Please try again.", None

    update_last_login(user["id"])
    return True, "Login successful!", dict(user)


def attempt_register(
    full_name: str,
    email: str,
    phone: str,
    age: Optional[int],
    gender: str,
    blood_group: str,
    password: str,
    confirm_password: str,
) -> Tuple[bool, str]:
    """
    Validate inputs and create a new account.
    Returns (success, message).
    """
    # Basic field checks
    if not full_name.strip():
        return False, "Full name is required."
    if len(full_name.strip()) < 2:
        return False, "Full name must be at least 2 characters."

    from utils.validators import validate_email_address, validate_phone_number
    ok, msg = validate_email_address(email)
    if not ok:
        return False, msg

    if phone:
        ok, msg = validate_phone_number(phone)
        if not ok:
            return False, msg

    if age is not None and (age < 1 or age > 120):
        return False, "Please enter a valid age (1–120)."

    ok, msg = validate_password_strength(password)
    if not ok:
        return False, msg

    if password != confirm_password:
        return False, "Passwords do not match."

    if email_exists(email):
        return False, "An account with this email already exists. Please log in."

    try:
        pw_hash = hash_password(password)
        create_user(
            full_name=full_name.strip(),
            email=email.strip().lower(),
            password_hash=pw_hash,
            phone=phone.strip(),
            age=age,
            gender=gender,
            blood_group=blood_group,
        )
        return True, "Account created successfully! Please log in."
    except Exception as exc:
        logger.error("Registration error: %s", exc)
        return False, "Registration failed. Please try again."


def reset_password_with_otp(
    email: str, otp_code: str, new_password: str, confirm_password: str
) -> Tuple[bool, str]:
    """
    Validate OTP and reset password.
    Returns (success, message).
    """
    if new_password != confirm_password:
        return False, "Passwords do not match."

    ok, msg = validate_password_strength(new_password)
    if not ok:
        return False, msg

    if not confirm_otp(email, otp_code):
        return False, "Invalid or expired OTP. Please request a new one."

    new_hash = hash_password(new_password)
    if update_password(email, new_hash):
        return True, "Password reset successfully! You can now log in."
    return False, "Failed to update password. Please try again."
