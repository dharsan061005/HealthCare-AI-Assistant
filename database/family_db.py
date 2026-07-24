"""
Family Management Database Module — Healthcare AI Assistant
Handles a dedicated family.db (separate from healthcare.db) so the existing
schema is never touched.  All CRUD for:
  - family_members
  - family_appointments
  - family_medicines
  - family_reports
  - family_vitals
  - family_emergency_contacts
  - family_health_scores
"""

import sqlite3
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FAMILY_DB_PATH = os.path.join(_BASE_DIR, "family.db")


# ── Connection ────────────────────────────────────────────────────────────────

def get_family_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(FAMILY_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ── Schema bootstrap ──────────────────────────────────────────────────────────

_SCHEMA = """
CREATE TABLE IF NOT EXISTS family_members (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER,
    full_name     TEXT    NOT NULL,
    relationship  TEXT    NOT NULL,
    date_of_birth TEXT,
    age           INTEGER,
    gender        TEXT    NOT NULL DEFAULT '',
    blood_group   TEXT    NOT NULL DEFAULT '',
    phone         TEXT    NOT NULL DEFAULT '',
    email         TEXT    NOT NULL DEFAULT '',
    address       TEXT    NOT NULL DEFAULT '',
    medical_conditions TEXT NOT NULL DEFAULT '',
    allergies     TEXT    NOT NULL DEFAULT '',
    emergency_contact  TEXT NOT NULL DEFAULT '',
    photo_emoji   TEXT    NOT NULL DEFAULT '👤',
    alt_phone     TEXT    NOT NULL DEFAULT '',
    emergency_contact_number TEXT NOT NULL DEFAULT '',
    emergency_contact_relationship TEXT NOT NULL DEFAULT '',
    current_medications TEXT NOT NULL DEFAULT '',
    medical_history TEXT NOT NULL DEFAULT '',
    disability    INTEGER NOT NULL DEFAULT 0,
    health_insurance_provider TEXT NOT NULL DEFAULT '',
    insurance_number TEXT NOT NULL DEFAULT '',
    height        REAL    NOT NULL DEFAULT 0.0,
    weight        REAL    NOT NULL DEFAULT 0.0,
    bmi           REAL    NOT NULL DEFAULT 0.0,
    smoking       INTEGER NOT NULL DEFAULT 0,
    alcohol       INTEGER NOT NULL DEFAULT 0,
    notify_appointments INTEGER NOT NULL DEFAULT 1,
    notify_medicines    INTEGER NOT NULL DEFAULT 1,
    notify_health_alerts INTEGER NOT NULL DEFAULT 1,
    is_active     INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_fm_user     ON family_members(user_id);
CREATE INDEX IF NOT EXISTS idx_fm_active   ON family_members(is_active);
CREATE INDEX IF NOT EXISTS idx_fm_relation ON family_members(relationship);

-- ─── Appointments ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS family_appointments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id       INTEGER NOT NULL REFERENCES family_members(id),
    member_name     TEXT    NOT NULL,
    doctor_name     TEXT    NOT NULL,
    specialization  TEXT    NOT NULL DEFAULT '',
    appointment_date TEXT   NOT NULL,
    appointment_time TEXT   NOT NULL,
    hospital        TEXT    NOT NULL DEFAULT '',
    purpose         TEXT    NOT NULL DEFAULT '',
    status          TEXT    NOT NULL DEFAULT 'scheduled',
    notes           TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_fa_member  ON family_appointments(member_id);
CREATE INDEX IF NOT EXISTS idx_fa_date    ON family_appointments(appointment_date);
CREATE INDEX IF NOT EXISTS idx_fa_status  ON family_appointments(status);

-- ─── Medicines ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS family_medicines (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id      INTEGER NOT NULL REFERENCES family_members(id),
    member_name    TEXT    NOT NULL,
    medicine_name  TEXT    NOT NULL,
    dosage         TEXT    NOT NULL,
    frequency      TEXT    NOT NULL,
    reminder_time  TEXT    NOT NULL,
    start_date     TEXT    NOT NULL DEFAULT (date('now')),
    end_date       TEXT    NOT NULL DEFAULT '',
    prescribed_by  TEXT    NOT NULL DEFAULT '',
    notes          TEXT    NOT NULL DEFAULT '',
    is_active      INTEGER NOT NULL DEFAULT 1,
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_med_member ON family_medicines(member_id);
CREATE INDEX IF NOT EXISTS idx_med_active ON family_medicines(is_active);

-- ─── Missed medicines log ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS family_missed_medicines (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_id INTEGER NOT NULL REFERENCES family_medicines(id),
    member_name TEXT    NOT NULL,
    missed_date TEXT    NOT NULL DEFAULT (date('now')),
    reason      TEXT    NOT NULL DEFAULT '',
    noted_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_mm_med    ON family_missed_medicines(medicine_id);
CREATE INDEX IF NOT EXISTS idx_mm_member ON family_missed_medicines(member_name);

-- ─── Medical Reports ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS family_reports (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id    INTEGER NOT NULL REFERENCES family_members(id),
    member_name  TEXT    NOT NULL,
    report_type  TEXT    NOT NULL,
    report_date  TEXT    NOT NULL DEFAULT (date('now')),
    lab_name     TEXT    NOT NULL DEFAULT '',
    doctor_name  TEXT    NOT NULL DEFAULT '',
    file_name    TEXT    NOT NULL DEFAULT '',
    ai_summary   TEXT    NOT NULL DEFAULT '',
    raw_text     TEXT    NOT NULL DEFAULT '',
    tags         TEXT    NOT NULL DEFAULT '',
    is_normal    INTEGER NOT NULL DEFAULT 1,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_rep_member ON family_reports(member_id);
CREATE INDEX IF NOT EXISTS idx_rep_date   ON family_reports(report_date);
CREATE INDEX IF NOT EXISTS idx_rep_type   ON family_reports(report_type);

-- ─── Vitals ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS family_vitals (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id     INTEGER NOT NULL REFERENCES family_members(id),
    member_name   TEXT    NOT NULL,
    recorded_date TEXT    NOT NULL DEFAULT (date('now')),
    recorded_time TEXT    NOT NULL DEFAULT (time('now')),
    bp_systolic   INTEGER,
    bp_diastolic  INTEGER,
    heart_rate    INTEGER,
    temperature   REAL,
    weight_kg     REAL,
    height_cm     REAL,
    spo2          INTEGER,
    blood_glucose INTEGER,
    notes         TEXT    NOT NULL DEFAULT '',
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_vit_member ON family_vitals(member_id);
CREATE INDEX IF NOT EXISTS idx_vit_date   ON family_vitals(recorded_date);

-- ─── Health Scores ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS family_health_scores (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id   INTEGER NOT NULL REFERENCES family_members(id),
    member_name TEXT    NOT NULL,
    score       INTEGER NOT NULL DEFAULT 0,
    grade       TEXT    NOT NULL DEFAULT 'N/A',
    notes       TEXT    NOT NULL DEFAULT '',
    scored_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_hs_member ON family_health_scores(member_id);

-- ─── Emergency Contacts ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS family_emergency_contacts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id       INTEGER NOT NULL REFERENCES family_members(id),
    member_name     TEXT    NOT NULL,
    contact_name    TEXT    NOT NULL,
    relationship    TEXT    NOT NULL,
    phone           TEXT    NOT NULL,
    alt_phone       TEXT    NOT NULL DEFAULT '',
    email           TEXT    NOT NULL DEFAULT '',
    priority        INTEGER NOT NULL DEFAULT 1,
    notes           TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_ec_member   ON family_emergency_contacts(member_id);
CREATE INDEX IF NOT EXISTS idx_ec_priority ON family_emergency_contacts(priority);

-- ─── Family Preferences ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS family_preferences (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL UNIQUE,
    family_name     TEXT    NOT NULL DEFAULT 'My Family',
    language        TEXT    NOT NULL DEFAULT 'English',
    notify_email    INTEGER NOT NULL DEFAULT 1,
    notify_sms      INTEGER NOT NULL DEFAULT 0,
    reminder_advance_mins INTEGER NOT NULL DEFAULT 30,
    theme           TEXT    NOT NULL DEFAULT 'blue',
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""


def _migrate_family_db(conn: sqlite3.Connection) -> None:
    """Dynamically add missing columns to family_members table."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(family_members)")
    existing_cols = {row["name"] for row in cursor.fetchall()}

    columns_to_add = {
        "alt_phone": "TEXT NOT NULL DEFAULT ''",
        "emergency_contact_number": "TEXT NOT NULL DEFAULT ''",
        "emergency_contact_relationship": "TEXT NOT NULL DEFAULT ''",
        "current_medications": "TEXT NOT NULL DEFAULT ''",
        "medical_history": "TEXT NOT NULL DEFAULT ''",
        "disability": "INTEGER NOT NULL DEFAULT 0",
        "health_insurance_provider": "TEXT NOT NULL DEFAULT ''",
        "insurance_number": "TEXT NOT NULL DEFAULT ''",
        "height": "REAL NOT NULL DEFAULT 0.0",
        "weight": "REAL NOT NULL DEFAULT 0.0",
        "bmi": "REAL NOT NULL DEFAULT 0.0",
        "smoking": "INTEGER NOT NULL DEFAULT 0",
        "alcohol": "INTEGER NOT NULL DEFAULT 0",
        "notify_appointments": "INTEGER NOT NULL DEFAULT 1",
        "notify_medicines": "INTEGER NOT NULL DEFAULT 1",
        "notify_health_alerts": "INTEGER NOT NULL DEFAULT 1",
    }

    for col, defn in columns_to_add.items():
        if col not in existing_cols:
            try:
                cursor.execute(f"ALTER TABLE family_members ADD COLUMN {col} {defn}")
                logger.info("Added column %s to family_members table.", col)
            except Exception as e:
                logger.error("Failed to add column %s: %s", col, e)
    conn.commit()


def init_family_db() -> None:
    """Create all family tables if they do not exist."""
    try:
        with get_family_connection() as conn:
            conn.executescript(_SCHEMA)
            _migrate_family_db(conn)
        logger.info("Family DB initialized at %s", FAMILY_DB_PATH)
    except Exception as e:
        logger.error("Family DB init failed: %s", e)
        raise

# ═══════════════════════════════════════════════════════════════════════════════
# FAMILY MEMBERS
# ═══════════════════════════════════════════════════════════════════════════════

def create_family_member(
    full_name: str,
    relationship: str,
    date_of_birth: str = "",
    age: Optional[int] = None,
    gender: str = "",
    blood_group: str = "",
    phone: str = "",
    email: str = "",
    address: str = "",
    medical_conditions: str = "",
    allergies: str = "",
    emergency_contact: str = "",
    photo_emoji: str = "👤",
    user_id: Optional[int] = None,
    alt_phone: str = "",
    emergency_contact_number: str = "",
    emergency_contact_relationship: str = "",
    current_medications: str = "",
    medical_history: str = "",
    disability: int = 0,
    health_insurance_provider: str = "",
    insurance_number: str = "",
    height: float = 0.0,
    weight: float = 0.0,
    bmi: float = 0.0,
    smoking: int = 0,
    alcohol: int = 0,
    notify_appointments: int = 1,
    notify_medicines: int = 1,
    notify_health_alerts: int = 1,
) -> int:
    sql = """
        INSERT INTO family_members
            (user_id, full_name, relationship, date_of_birth, age, gender,
             blood_group, phone, email, address, medical_conditions,
             allergies, emergency_contact, photo_emoji, is_active,
             alt_phone, emergency_contact_number, emergency_contact_relationship,
             current_medications, medical_history, disability,
             health_insurance_provider, insurance_number,
             height, weight, bmi, smoking, alcohol,
             notify_appointments, notify_medicines, notify_health_alerts)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,1, ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """
    with get_family_connection() as conn:
        cur = conn.execute(sql, (
            user_id, full_name, relationship, date_of_birth, age, gender,
            blood_group, phone, email, address, medical_conditions,
            allergies, emergency_contact, photo_emoji,
            alt_phone, emergency_contact_number, emergency_contact_relationship,
            current_medications, medical_history, disability,
            health_insurance_provider, insurance_number,
            height, weight, bmi, smoking, alcohol,
            notify_appointments, notify_medicines, notify_health_alerts
        ))
        return cur.lastrowid


def get_family_members(user_id: Optional[int] = None, active_only: bool = True) -> List[Dict]:
    sql = "SELECT * FROM family_members WHERE 1=1"
    params: List[Any] = []
    if active_only:
        sql += " AND is_active=1"
    if user_id is not None:
        sql += " AND user_id=?"
        params.append(user_id)
    sql += " ORDER BY relationship, full_name"
    with get_family_connection() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_family_member_by_id(member_id: int) -> Optional[Dict]:
    with get_family_connection() as conn:
        row = conn.execute(
            "SELECT * FROM family_members WHERE id=?", (member_id,)
        ).fetchone()
        return dict(row) if row else None


def update_family_member(member_id: int, **fields) -> bool:
    allowed = {
        "full_name", "relationship", "date_of_birth", "age", "gender",
        "blood_group", "phone", "email", "address", "medical_conditions",
        "allergies", "emergency_contact", "photo_emoji",
        "alt_phone", "emergency_contact_number", "emergency_contact_relationship",
        "current_medications", "medical_history", "disability",
        "health_insurance_provider", "insurance_number",
        "height", "weight", "bmi", "smoking", "alcohol",
        "notify_appointments", "notify_medicines", "notify_health_alerts",
    }
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return False
    updates["updated_at"] = "datetime('now')"
    set_clause = ", ".join(
        f"{k}=datetime('now')" if k == "updated_at" else f"{k}=?"
        for k in updates
    )
    vals = [v for k, v in updates.items() if k != "updated_at"]
    vals.append(member_id)
    with get_family_connection() as conn:
        cur = conn.execute(
            f"UPDATE family_members SET {set_clause} WHERE id=?", vals
        )
        return cur.rowcount > 0


def delete_family_member(member_id: int) -> bool:
    with get_family_connection() as conn:
        cur = conn.execute(
            "UPDATE family_members SET is_active=0, updated_at=datetime('now') WHERE id=?",
            (member_id,),
        )
        return cur.rowcount > 0


def count_family_members(user_id: Optional[int] = None) -> int:
    sql = "SELECT COUNT(*) FROM family_members WHERE is_active=1"
    params: List[Any] = []
    if user_id is not None:
        sql += " AND user_id=?"
        params.append(user_id)
    with get_family_connection() as conn:
        return conn.execute(sql, params).fetchone()[0]


# ═══════════════════════════════════════════════════════════════════════════════
# FAMILY APPOINTMENTS
# ═══════════════════════════════════════════════════════════════════════════════

def create_family_appointment(
    member_id: int,
    member_name: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    specialization: str = "",
    hospital: str = "",
    purpose: str = "",
    notes: str = "",
) -> int:
    sql = """
        INSERT INTO family_appointments
            (member_id, member_name, doctor_name, specialization,
             appointment_date, appointment_time, hospital, purpose, status, notes)
        VALUES (?,?,?,?,?,?,?,?,'scheduled',?)
    """
    with get_family_connection() as conn:
        cur = conn.execute(sql, (
            member_id, member_name, doctor_name, specialization,
            appointment_date, appointment_time, hospital, purpose, notes,
        ))
        return cur.lastrowid


def get_family_appointments(
    member_id: Optional[int] = None,
    status: Optional[str] = None,
) -> List[Dict]:
    sql = "SELECT * FROM family_appointments WHERE 1=1"
    params: List[Any] = []
    if member_id:
        sql += " AND member_id=?"
        params.append(member_id)
    if status:
        sql += " AND status=?"
        params.append(status)
    sql += " ORDER BY appointment_date, appointment_time"
    with get_family_connection() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def update_appointment_status(appt_id: int, status: str) -> bool:
    with get_family_connection() as conn:
        cur = conn.execute(
            "UPDATE family_appointments SET status=? WHERE id=?", (status, appt_id)
        )
        return cur.rowcount > 0


def get_upcoming_appointments(days_ahead: int = 30) -> List[Dict]:
    sql = """
        SELECT * FROM family_appointments
        WHERE status='scheduled'
          AND appointment_date BETWEEN date('now') AND date('now', ?||' days')
        ORDER BY appointment_date, appointment_time
    """
    with get_family_connection() as conn:
        return [dict(r) for r in conn.execute(sql, (days_ahead,)).fetchall()]


# ═══════════════════════════════════════════════════════════════════════════════
# FAMILY MEDICINES
# ═══════════════════════════════════════════════════════════════════════════════

def create_family_medicine(
    member_id: int,
    member_name: str,
    medicine_name: str,
    dosage: str,
    frequency: str,
    reminder_time: str,
    start_date: str = "",
    end_date: str = "",
    prescribed_by: str = "",
    notes: str = "",
) -> int:
    sql = """
        INSERT INTO family_medicines
            (member_id, member_name, medicine_name, dosage, frequency,
             reminder_time, start_date, end_date, prescribed_by, notes, is_active)
        VALUES (?,?,?,?,?,?,?,?,?,?,1)
    """
    with get_family_connection() as conn:
        cur = conn.execute(sql, (
            member_id, member_name, medicine_name, dosage, frequency,
            reminder_time, start_date, end_date, prescribed_by, notes,
        ))
        return cur.lastrowid


def get_family_medicines(
    member_id: Optional[int] = None,
    active_only: bool = True,
) -> List[Dict]:
    sql = "SELECT * FROM family_medicines WHERE 1=1"
    params: List[Any] = []
    if active_only:
        sql += " AND is_active=1"
    if member_id:
        sql += " AND member_id=?"
        params.append(member_id)
    sql += " ORDER BY reminder_time, medicine_name"
    with get_family_connection() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def deactivate_family_medicine(medicine_id: int) -> bool:
    with get_family_connection() as conn:
        cur = conn.execute(
            "UPDATE family_medicines SET is_active=0 WHERE id=?", (medicine_id,)
        )
        return cur.rowcount > 0


def log_missed_medicine(medicine_id: int, member_name: str, reason: str = "") -> int:
    with get_family_connection() as conn:
        cur = conn.execute(
            "INSERT INTO family_missed_medicines (medicine_id, member_name, reason) VALUES (?,?,?)",
            (medicine_id, member_name, reason),
        )
        return cur.lastrowid


def get_missed_medicines(member_name: Optional[str] = None) -> List[Dict]:
    sql = """
        SELECT mm.*, fm.medicine_name, fm.dosage
        FROM family_missed_medicines mm
        JOIN family_medicines fm ON mm.medicine_id = fm.id
        WHERE 1=1
    """
    params: List[Any] = []
    if member_name:
        sql += " AND mm.member_name=?"
        params.append(member_name)
    sql += " ORDER BY mm.missed_date DESC LIMIT 50"
    with get_family_connection() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


# ═══════════════════════════════════════════════════════════════════════════════
# FAMILY REPORTS
# ═══════════════════════════════════════════════════════════════════════════════

def create_family_report(
    member_id: int,
    member_name: str,
    report_type: str,
    report_date: str,
    lab_name: str = "",
    doctor_name: str = "",
    file_name: str = "",
    ai_summary: str = "",
    raw_text: str = "",
    tags: str = "",
    is_normal: bool = True,
) -> int:
    sql = """
        INSERT INTO family_reports
            (member_id, member_name, report_type, report_date, lab_name,
             doctor_name, file_name, ai_summary, raw_text, tags, is_normal)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """
    with get_family_connection() as conn:
        cur = conn.execute(sql, (
            member_id, member_name, report_type, report_date, lab_name,
            doctor_name, file_name, ai_summary, raw_text, tags, int(is_normal),
        ))
        return cur.lastrowid


def get_family_reports(member_id: Optional[int] = None) -> List[Dict]:
    sql = "SELECT * FROM family_reports WHERE 1=1"
    params: List[Any] = []
    if member_id:
        sql += " AND member_id=?"
        params.append(member_id)
    sql += " ORDER BY report_date DESC"
    with get_family_connection() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def update_report_ai_summary(report_id: int, summary: str) -> bool:
    with get_family_connection() as conn:
        cur = conn.execute(
            "UPDATE family_reports SET ai_summary=? WHERE id=?", (summary, report_id)
        )
        return cur.rowcount > 0


def delete_family_report(report_id: int) -> bool:
    with get_family_connection() as conn:
        cur = conn.execute("DELETE FROM family_reports WHERE id=?", (report_id,))
        return cur.rowcount > 0


# ═══════════════════════════════════════════════════════════════════════════════
# VITALS
# ═══════════════════════════════════════════════════════════════════════════════

def record_vitals(
    member_id: int,
    member_name: str,
    recorded_date: str,
    recorded_time: str,
    bp_systolic: Optional[int] = None,
    bp_diastolic: Optional[int] = None,
    heart_rate: Optional[int] = None,
    temperature: Optional[float] = None,
    weight_kg: Optional[float] = None,
    height_cm: Optional[float] = None,
    spo2: Optional[int] = None,
    blood_glucose: Optional[int] = None,
    notes: str = "",
) -> int:
    sql = """
        INSERT INTO family_vitals
            (member_id, member_name, recorded_date, recorded_time,
             bp_systolic, bp_diastolic, heart_rate, temperature,
             weight_kg, height_cm, spo2, blood_glucose, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """
    with get_family_connection() as conn:
        cur = conn.execute(sql, (
            member_id, member_name, recorded_date, recorded_time,
            bp_systolic, bp_diastolic, heart_rate, temperature,
            weight_kg, height_cm, spo2, blood_glucose, notes,
        ))
        return cur.lastrowid


def get_vitals(
    member_id: Optional[int] = None,
    limit: int = 50,
) -> List[Dict]:
    sql = "SELECT * FROM family_vitals WHERE 1=1"
    params: List[Any] = []
    if member_id:
        sql += " AND member_id=?"
        params.append(member_id)
    sql += " ORDER BY recorded_date DESC, recorded_time DESC LIMIT ?"
    params.append(limit)
    with get_family_connection() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH SCORES
# ═══════════════════════════════════════════════════════════════════════════════

def save_health_score(member_id: int, member_name: str, score: int, grade: str, notes: str = "") -> int:
    with get_family_connection() as conn:
        cur = conn.execute(
            "INSERT INTO family_health_scores (member_id, member_name, score, grade, notes) VALUES (?,?,?,?,?)",
            (member_id, member_name, score, grade, notes),
        )
        return cur.lastrowid


def get_latest_health_score(member_id: int) -> Optional[Dict]:
    with get_family_connection() as conn:
        row = conn.execute(
            "SELECT * FROM family_health_scores WHERE member_id=? ORDER BY scored_at DESC LIMIT 1",
            (member_id,),
        ).fetchone()
        return dict(row) if row else None


# ═══════════════════════════════════════════════════════════════════════════════
# EMERGENCY CONTACTS
# ═══════════════════════════════════════════════════════════════════════════════

def create_emergency_contact(
    member_id: int,
    member_name: str,
    contact_name: str,
    relationship: str,
    phone: str,
    alt_phone: str = "",
    email: str = "",
    priority: int = 1,
    notes: str = "",
) -> int:
    sql = """
        INSERT INTO family_emergency_contacts
            (member_id, member_name, contact_name, relationship,
             phone, alt_phone, email, priority, notes)
        VALUES (?,?,?,?,?,?,?,?,?)
    """
    with get_family_connection() as conn:
        cur = conn.execute(sql, (
            member_id, member_name, contact_name, relationship,
            phone, alt_phone, email, priority, notes,
        ))
        return cur.lastrowid


def get_emergency_contacts(member_id: Optional[int] = None) -> List[Dict]:
    sql = "SELECT * FROM family_emergency_contacts WHERE 1=1"
    params: List[Any] = []
    if member_id:
        sql += " AND member_id=?"
        params.append(member_id)
    sql += " ORDER BY priority ASC"
    with get_family_connection() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def delete_emergency_contact(contact_id: int) -> bool:
    with get_family_connection() as conn:
        cur = conn.execute(
            "DELETE FROM family_emergency_contacts WHERE id=?", (contact_id,)
        )
        return cur.rowcount > 0


# ═══════════════════════════════════════════════════════════════════════════════
# PREFERENCES
# ═══════════════════════════════════════════════════════════════════════════════

def get_family_preferences(user_id: int) -> Dict:
    with get_family_connection() as conn:
        row = conn.execute(
            "SELECT * FROM family_preferences WHERE user_id=?", (user_id,)
        ).fetchone()
        if row:
            return dict(row)
        return {
            "user_id": user_id, "family_name": "My Family", "language": "English",
            "notify_email": 1, "notify_sms": 0, "reminder_advance_mins": 30, "theme": "blue",
        }


def save_family_preferences(user_id: int, family_name: str, notify_email: bool,
                             notify_sms: bool, reminder_advance_mins: int) -> None:
    with get_family_connection() as conn:
        conn.execute("""
            INSERT INTO family_preferences
                (user_id, family_name, notify_email, notify_sms, reminder_advance_mins)
            VALUES (?,?,?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET
                family_name=excluded.family_name,
                notify_email=excluded.notify_email,
                notify_sms=excluded.notify_sms,
                reminder_advance_mins=excluded.reminder_advance_mins,
                updated_at=datetime('now')
        """, (user_id, family_name, int(notify_email), int(notify_sms), reminder_advance_mins))


# ═══════════════════════════════════════════════════════════════════════════════
# AGGREGATE STATS
# ═══════════════════════════════════════════════════════════════════════════════

def get_family_dashboard_stats(user_id: Optional[int] = None) -> Dict:
    """Return all counts needed for the Family Dashboard overview cards."""
    try:
        members = get_family_members(user_id=user_id)
        member_ids = [m["id"] for m in members]

        def _count(table: str, where: str = "", params: tuple = ()) -> int:
            sql = f"SELECT COUNT(*) FROM {table}"
            if where:
                sql += f" WHERE {where}"
            with get_family_connection() as conn:
                return conn.execute(sql, params).fetchone()[0]

        upcoming = len(get_upcoming_appointments(days_ahead=7))
        active_meds = sum(
            _count("family_medicines", "member_id=? AND is_active=1", (mid,))
            for mid in member_ids
        ) if member_ids else 0
        missed = sum(
            len(get_missed_medicines(m["full_name"])) for m in members
        ) if members else 0
        reports = _count("family_reports")
        vitals_today = sum(
            _count("family_vitals", "member_id=? AND recorded_date=date('now')", (mid,))
            for mid in member_ids
        ) if member_ids else 0

        return {
            "total_members":   len(members),
            "upcoming_appts":  upcoming,
            "active_medicines": active_meds,
            "missed_medicines": missed,
            "total_reports":   reports,
            "vitals_today":    vitals_today,
        }
    except Exception as e:
        logger.error("Family dashboard stats error: %s", e)
        return {
            "total_members": 0, "upcoming_appts": 0, "active_medicines": 0,
            "missed_medicines": 0, "total_reports": 0, "vitals_today": 0,
        }
