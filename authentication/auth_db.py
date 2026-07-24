"""
Authentication Database Module — Healthcare AI Assistant
Handles users table creation, CRUD operations, and OTP storage.
All queries use parameterized statements to prevent SQL injection.
"""

import sqlite3
import logging
import os
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

# Reuse the same DB file as the rest of the project
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_BASE_DIR)
DB_PATH = os.path.join(_PROJECT_DIR, "database", "healthcare.db")


# ─── Schema ──────────────────────────────────────────────────────────────────

USERS_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name     TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    phone         TEXT,
    age           INTEGER,
    gender        TEXT,
    blood_group   TEXT    DEFAULT '',
    password_hash TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    last_login    TEXT
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

CREATE TABLE IF NOT EXISTS otp_tokens (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    email      TEXT    NOT NULL COLLATE NOCASE,
    otp_code   TEXT    NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT    NOT NULL,
    used       INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_otp_email ON otp_tokens(email);
"""


def _get_conn() -> sqlite3.Connection:
    """Return a SQLite connection with row_factory set."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_auth_tables() -> None:
    """Create users and otp_tokens tables if they do not yet exist."""
    try:
        with _get_conn() as conn:
            conn.executescript(USERS_SCHEMA)
        logger.info("Auth tables initialised.")
    except Exception as exc:
        logger.error("Failed to initialise auth tables: %s", exc)
        raise


# ─── User CRUD ────────────────────────────────────────────────────────────────

def create_user(
    full_name: str,
    email: str,
    password_hash: str,
    phone: str = "",
    age: Optional[int] = None,
    gender: str = "",
    blood_group: str = "",
) -> int:
    """
    Insert a new user row. Returns the new user ID.
    Raises sqlite3.IntegrityError if the email already exists.
    """
    sql = """
        INSERT INTO users (full_name, email, phone, age, gender, blood_group, password_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    with _get_conn() as conn:
        cur = conn.execute(sql, (full_name, email.strip().lower(),
                                  phone, age, gender, blood_group, password_hash))
        return cur.lastrowid


def get_user_by_email(email: str) -> Optional[Dict]:
    """Fetch a user row by email (case-insensitive). Returns None if not found."""
    sql = "SELECT * FROM users WHERE LOWER(email) = LOWER(?)"
    with _get_conn() as conn:
        row = conn.execute(sql, (email.strip(),)).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Fetch a user row by primary key."""
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def email_exists(email: str) -> bool:
    """Return True if the email is already registered."""
    sql = "SELECT 1 FROM users WHERE LOWER(email) = LOWER(?)"
    with _get_conn() as conn:
        return conn.execute(sql, (email.strip(),)).fetchone() is not None


def update_last_login(user_id: int) -> None:
    """Stamp last_login with the current UTC datetime."""
    sql = "UPDATE users SET last_login = datetime('now') WHERE id = ?"
    with _get_conn() as conn:
        conn.execute(sql, (user_id,))


def update_password(email: str, new_hash: str) -> bool:
    """Update a user's password hash. Returns True on success."""
    sql = "UPDATE users SET password_hash = ? WHERE LOWER(email) = LOWER(?)"
    with _get_conn() as conn:
        cur = conn.execute(sql, (new_hash, email.strip()))
        return cur.rowcount > 0


def update_profile(
    user_id: int,
    full_name: str,
    phone: str,
    age: Optional[int],
    gender: str,
    blood_group: str,
) -> bool:
    """Update editable profile fields. Returns True on success."""
    sql = """
        UPDATE users
        SET full_name = ?, phone = ?, age = ?, gender = ?, blood_group = ?
        WHERE id = ?
    """
    with _get_conn() as conn:
        cur = conn.execute(sql, (full_name, phone, age, gender, blood_group, user_id))
        return cur.rowcount > 0


# ─── OTP CRUD ─────────────────────────────────────────────────────────────────

def store_otp(email: str, otp_code: str, ttl_minutes: int = 10) -> None:
    """
    Persist a new OTP for the given email.
    Invalidates any previous unused OTPs for that email first.
    """
    invalidate_sql = "UPDATE otp_tokens SET used = 1 WHERE LOWER(email) = LOWER(?) AND used = 0"
    insert_sql = """
        INSERT INTO otp_tokens (email, otp_code, expires_at)
        VALUES (?, ?,
            datetime('now', '+{} minutes'))
    """.format(ttl_minutes)  # ttl_minutes is an int — no injection risk

    with _get_conn() as conn:
        conn.execute(invalidate_sql, (email.strip(),))
        conn.execute(insert_sql, (email.strip().lower(), otp_code))


def verify_otp(email: str, otp_code: str) -> bool:
    """
    Check that the OTP matches, is unused, and has not expired.
    Marks the token as used on success.
    Returns True if valid.
    """
    sql = """
        SELECT id FROM otp_tokens
        WHERE LOWER(email) = LOWER(?)
          AND otp_code      = ?
          AND used          = 0
          AND expires_at    > datetime('now')
        ORDER BY id DESC
        LIMIT 1
    """
    with _get_conn() as conn:
        row = conn.execute(sql, (email.strip(), otp_code)).fetchone()
        if row:
            conn.execute("UPDATE otp_tokens SET used = 1 WHERE id = ?", (row["id"],))
            return True
    return False


def cleanup_expired_otps() -> None:
    """Delete OTP rows that are older than 30 minutes (housekeeping)."""
    sql = "DELETE FROM otp_tokens WHERE created_at < datetime('now', '-30 minutes')"
    with _get_conn() as conn:
        conn.execute(sql)
