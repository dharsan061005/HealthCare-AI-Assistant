"""
Database module for Healthcare AI Assistant.
Handles SQLite connection, initialization, and all CRUD operations.
"""

import sqlite3
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Resolve DB path relative to this file so it works from any cwd
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_BASE_DIR, "healthcare.db")
SCHEMA_PATH = os.path.join(_BASE_DIR, "schema.sql")


def get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with row_factory set."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _migrate_db(conn: sqlite3.Connection) -> None:
    """Run database migrations for schema updates."""
    try:
        # Check if new columns exist in appointments table
        cursor = conn.execute("PRAGMA table_info(appointments)")
        cols = [r["name"] for r in cursor.fetchall()]
        
        if "hospital_name" not in cols:
            logger.info("Migration: Adding 'hospital_name' column to 'appointments' table...")
            conn.execute("ALTER TABLE appointments ADD COLUMN hospital_name TEXT NOT NULL DEFAULT 'General Hospital'")
        
        if "age" not in cols:
            logger.info("Migration: Adding 'age' column...")
            conn.execute("ALTER TABLE appointments ADD COLUMN age INTEGER")
            
        if "gender" not in cols:
            logger.info("Migration: Adding 'gender' column...")
            conn.execute("ALTER TABLE appointments ADD COLUMN gender TEXT")
            
        if "mobile_number" not in cols:
            logger.info("Migration: Adding 'mobile_number' column...")
            conn.execute("ALTER TABLE appointments ADD COLUMN mobile_number TEXT")
            
        if "email" not in cols:
            logger.info("Migration: Adding 'email' column...")
            conn.execute("ALTER TABLE appointments ADD COLUMN email TEXT")
            
        if "reason_for_visit" not in cols:
            logger.info("Migration: Adding 'reason_for_visit' column...")
            conn.execute("ALTER TABLE appointments ADD COLUMN reason_for_visit TEXT")

        logger.info("Migrations completed successfully.")
    except Exception as e:
        logger.error("Database migration failed: %s", e)
        raise


def init_db() -> None:
    """Initialize the database by running schema.sql and seeding doctors."""
    try:
        with get_connection() as conn:
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
            _migrate_db(conn)
        _seed_doctors()
        logger.info("Database initialized successfully at %s", DB_PATH)
    except Exception as e:
        logger.error("Failed to initialize database: %s", e)
        raise


def _seed_doctors() -> None:
    """Seed the doctors table with default data if empty."""
    doctors = [
        ("Dr. Ananya Sharma", "Cardiology", "09:00,10:00,11:00,14:00,15:00,16:00"),
        ("Dr. Rajesh Kumar", "Neurology", "09:00,10:00,11:00,14:00,15:00"),
        ("Dr. Priya Menon", "Orthopedics", "10:00,11:00,14:00,15:00,16:00"),
        ("Dr. Suresh Patel", "General Medicine", "09:00,10:00,11:00,12:00,14:00,15:00,16:00"),
        ("Dr. Kavitha Nair", "Dermatology", "10:00,11:00,14:00,15:00"),
        ("Dr. Arjun Reddy", "Pediatrics", "09:00,10:00,11:00,14:00,15:00,16:00"),
        ("Dr. Meera Iyer", "Gynecology", "09:00,10:00,11:00,14:00,15:00"),
        ("Dr. Vikram Singh", "Ophthalmology", "10:00,11:00,14:00,15:00,16:00"),
        ("Dr. Nisha Verma", "ENT", "09:00,10:00,11:00,14:00,15:00"),
        ("Dr. Ramesh Babu", "Psychiatry", "10:00,11:00,14:00,15:00"),
    ]
    try:
        with get_connection() as conn:
            existing = conn.execute("SELECT COUNT(*) FROM doctors").fetchone()[0]
            if existing == 0:
                conn.executemany(
                    "INSERT INTO doctors (doctor_name, specialization, available_slots) VALUES (?, ?, ?)",
                    doctors,
                )
                logger.info("Seeded %d doctors into database.", len(doctors))
    except Exception as e:
        logger.error("Failed to seed doctors: %s", e)


# ─── Appointment CRUD ────────────────────────────────────────────────────────

def create_appointment(
    hospital_name: str,
    patient_name: str,
    age: int,
    gender: str,
    mobile_number: str,
    email: str,
    reason_for_visit: str,
    doctor_name: str,
    specialization: str,
    appointment_date: str,
    appointment_time: str,
    notes: str = "",
) -> int:
    """Insert a new appointment and return its ID."""
    sql = """
        INSERT INTO appointments
            (hospital_name, patient_name, age, gender, mobile_number, email, reason_for_visit, 
             doctor_name, specialization, appointment_date, appointment_time, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'scheduled', ?)
    """
    with get_connection() as conn:
        cursor = conn.execute(sql, (
            hospital_name, patient_name, age, gender, mobile_number, email, reason_for_visit,
            doctor_name, specialization, appointment_date, appointment_time, notes
        ))
        return cursor.lastrowid


def get_appointments(patient_name: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
    """Fetch appointments, optionally filtered by patient name and/or status."""
    sql = "SELECT * FROM appointments WHERE 1=1"
    params: List[Any] = []
    if patient_name:
        sql += " AND LOWER(patient_name) = LOWER(?)"
        params.append(patient_name)
    if status:
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY appointment_date, appointment_time"
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def get_appointment_by_id(appointment_id: int) -> Optional[Dict]:
    """Fetch a single appointment by ID."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,)).fetchone()
        return dict(row) if row else None


def update_appointment_status(appointment_id: int, status: str) -> bool:
    """Update appointment status. Returns True if a row was updated."""
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE appointments SET status = ? WHERE id = ?", (status, appointment_id)
        )
        return cursor.rowcount > 0


def reschedule_appointment(
    appointment_id: int, new_date: str, new_time: str
) -> bool:
    """Reschedule an appointment to a new date and time."""
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE appointments SET appointment_date = ?, appointment_time = ?, status = 'scheduled' WHERE id = ?",
            (new_date, new_time, appointment_id),
        )
        return cursor.rowcount > 0


def check_duplicate_appointment(
    hospital_name: str, doctor_name: str, appointment_date: str, appointment_time: str
) -> bool:
    """Return True if a scheduled appointment already exists for that slot (Hospital + Doctor + Date + Time)."""
    sql = """
        SELECT COUNT(*) FROM appointments
        WHERE LOWER(hospital_name) = LOWER(?)
          AND LOWER(doctor_name) = LOWER(?)
          AND appointment_date = ?
          AND appointment_time = ?
          AND status = 'scheduled'
    """
    with get_connection() as conn:
        count = conn.execute(sql, (hospital_name, doctor_name, appointment_date, appointment_time)).fetchone()[0]
        return count > 0


# ─── Doctor CRUD ─────────────────────────────────────────────────────────────

def get_all_doctors() -> List[Dict]:
    """Return all doctors."""
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM doctors ORDER BY specialization, doctor_name").fetchall()
        return [dict(r) for r in rows]


def get_doctors_by_specialization(specialization: str) -> List[Dict]:
    """Return doctors filtered by specialization (case-insensitive)."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM doctors WHERE LOWER(specialization) = LOWER(?)",
            (specialization,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_doctor_slots(doctor_name: str) -> List[str]:
    """Return available time slots for a doctor."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT available_slots FROM doctors WHERE LOWER(doctor_name) = LOWER(?)",
            (doctor_name,),
        ).fetchone()
        if row:
            return [s.strip() for s in row["available_slots"].split(",")]
        return []


# ─── Medicine Reminder CRUD ──────────────────────────────────────────────────

def create_reminder(
    medicine_name: str,
    dosage: str,
    reminder_time: str,
    frequency: str,
    patient_name: str = "",
    notes: str = "",
) -> int:
    """Insert a new medicine reminder and return its ID."""
    sql = """
        INSERT INTO medicine_reminders
            (medicine_name, dosage, reminder_time, frequency, patient_name, notes, is_active)
        VALUES (?, ?, ?, ?, ?, ?, 1)
    """
    with get_connection() as conn:
        cursor = conn.execute(sql, (medicine_name, dosage, reminder_time, frequency, patient_name, notes))
        return cursor.lastrowid


def get_reminders(patient_name: Optional[str] = None, active_only: bool = True) -> List[Dict]:
    """Fetch reminders, optionally filtered by patient and active status."""
    sql = "SELECT * FROM medicine_reminders WHERE 1=1"
    params: List[Any] = []
    if active_only:
        sql += " AND is_active = 1"
    if patient_name:
        sql += " AND LOWER(patient_name) = LOWER(?)"
        params.append(patient_name)
    sql += " ORDER BY reminder_time"
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def get_reminder_by_id(reminder_id: int) -> Optional[Dict]:
    """Fetch a single reminder by ID."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM medicine_reminders WHERE id = ?", (reminder_id,)
        ).fetchone()
        return dict(row) if row else None


def update_reminder(
    reminder_id: int,
    medicine_name: str,
    dosage: str,
    reminder_time: str,
    frequency: str,
    patient_name: str = "",
    notes: str = "",
) -> bool:
    """Update an existing reminder. Returns True if updated."""
    sql = """
        UPDATE medicine_reminders
        SET medicine_name=?, dosage=?, reminder_time=?, frequency=?, patient_name=?, notes=?
        WHERE id=?
    """
    with get_connection() as conn:
        cursor = conn.execute(sql, (medicine_name, dosage, reminder_time, frequency,
                                    patient_name, notes, reminder_id))
        return cursor.rowcount > 0


def delete_reminder(reminder_id: int) -> bool:
    """Soft-delete a reminder by setting is_active=0."""
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE medicine_reminders SET is_active = 0 WHERE id = ?", (reminder_id,)
        )
        return cursor.rowcount > 0


# ─── Caregiver CRUD ───────────────────────────────────────────────────────────

def create_caregiver(
    patient_name: str,
    caregiver_name: str,
    relationship: str,
    mobile_number: str,
    email: str,
    notification_preference: str = "Email",
) -> int:
    """Insert a new caregiver record and return its ID."""
    sql = """
        INSERT INTO caregivers
            (patient_name, caregiver_name, relationship, mobile_number, email,
             notification_preference, is_active)
        VALUES (?, ?, ?, ?, ?, ?, 1)
    """
    with get_connection() as conn:
        cursor = conn.execute(
            sql,
            (patient_name, caregiver_name, relationship, mobile_number, email,
             notification_preference),
        )
        return cursor.lastrowid


def get_caregivers(patient_name: Optional[str] = None, active_only: bool = True) -> List[Dict]:
    """Fetch caregivers, optionally filtered by patient name and active status."""
    sql = "SELECT * FROM caregivers WHERE 1=1"
    params: List[Any] = []
    if active_only:
        sql += " AND is_active = 1"
    if patient_name:
        sql += " AND LOWER(patient_name) = LOWER(?)"
        params.append(patient_name)
    sql += " ORDER BY created_at DESC"
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def get_caregiver_by_id(caregiver_id: int) -> Optional[Dict]:
    """Fetch a single caregiver by ID."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM caregivers WHERE id = ?", (caregiver_id,)
        ).fetchone()
        return dict(row) if row else None


def get_caregivers_for_patient(patient_name: str) -> List[Dict]:
    """Return all active caregivers linked to a given patient (case-insensitive)."""
    return get_caregivers(patient_name=patient_name, active_only=True)


def update_caregiver(
    caregiver_id: int,
    caregiver_name: str,
    relationship: str,
    mobile_number: str,
    email: str,
    notification_preference: str,
) -> bool:
    """Update caregiver details. Returns True if a row was updated."""
    sql = """
        UPDATE caregivers
        SET caregiver_name=?, relationship=?, mobile_number=?, email=?,
            notification_preference=?
        WHERE id=?
    """
    with get_connection() as conn:
        cursor = conn.execute(
            sql,
            (caregiver_name, relationship, mobile_number, email,
             notification_preference, caregiver_id),
        )
        return cursor.rowcount > 0


def delete_caregiver(caregiver_id: int) -> bool:
    """Soft-delete a caregiver by setting is_active=0."""
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE caregivers SET is_active = 0 WHERE id = ?", (caregiver_id,)
        )
        return cursor.rowcount > 0


def count_caregivers(active_only: bool = True) -> int:
    """Return total number of caregiver records."""
    sql = "SELECT COUNT(*) FROM caregivers"
    if active_only:
        sql += " WHERE is_active = 1"
    with get_connection() as conn:
        return conn.execute(sql).fetchone()[0]


# ─── Notification Log CRUD ────────────────────────────────────────────────────

def log_notification(
    caregiver_id: int,
    patient_name: str,
    notification_type: str,
    channel: str,
    subject: str = "",
    body: str = "",
    status: str = "sent",
) -> int:
    """Insert a notification log entry and return its ID."""
    sql = """
        INSERT INTO notification_log
            (caregiver_id, patient_name, notification_type, channel, subject, body, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    with get_connection() as conn:
        cursor = conn.execute(
            sql, (caregiver_id, patient_name, notification_type, channel, subject, body, status)
        )
        return cursor.lastrowid


def get_notification_logs(
    caregiver_id: Optional[int] = None,
    patient_name: Optional[str] = None,
    notification_type: Optional[str] = None,
    limit: int = 100,
) -> List[Dict]:
    """Fetch notification log entries with optional filters."""
    sql = "SELECT n.*, c.caregiver_name FROM notification_log n JOIN caregivers c ON n.caregiver_id = c.id WHERE 1=1"
    params: List[Any] = []
    if caregiver_id:
        sql += " AND n.caregiver_id = ?"
        params.append(caregiver_id)
    if patient_name:
        sql += " AND LOWER(n.patient_name) = LOWER(?)"
        params.append(patient_name)
    if notification_type:
        sql += " AND n.notification_type = ?"
        params.append(notification_type)
    sql += " ORDER BY n.sent_at DESC LIMIT ?"
    params.append(limit)
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def count_notifications_today() -> int:
    """Return count of notifications sent today."""
    sql = "SELECT COUNT(*) FROM notification_log WHERE date(sent_at) = date('now')"
    with get_connection() as conn:
        return conn.execute(sql).fetchone()[0]


def count_notifications_by_type(notification_type: str) -> int:
    """Return total count of notifications of a given type."""
    sql = "SELECT COUNT(*) FROM notification_log WHERE notification_type = ?"
    with get_connection() as conn:
        return conn.execute(sql, (notification_type,)).fetchone()[0]


# ─── Chat History CRUD ────────────────────────────────────────────────────────

def save_chat_message(
    session_id: str,
    role: str,
    content: str,
    user_id: Optional[int] = None,
    provider: str = "groq",
    has_pdf: bool = False,
) -> int:
    """
    Persist a single chat message (user or assistant) to the DB.

    Args:
        session_id: Browser-session UUID (groups messages per conversation).
        role:       'user' or 'assistant'.
        content:    The message text.
        user_id:    Logged-in user's DB id (None for guests).
        provider:   LLM provider used ('groq' | 'gemini').
        has_pdf:    True if a PDF was attached to this turn.

    Returns:
        The new row ID.
    """
    sql = """
        INSERT INTO chat_history
            (user_id, session_id, role, content, provider, has_pdf)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    with get_connection() as conn:
        cur = conn.execute(sql, (
            user_id, session_id, role, content, provider, int(has_pdf)
        ))
        return cur.lastrowid


def get_chat_history(
    session_id: str,
    limit: int = 100,
) -> List[Dict]:
    """
    Fetch all messages for a session, oldest first.

    Args:
        session_id: The session UUID to retrieve.
        limit:      Max rows to return (safety cap).

    Returns:
        List of row dicts with keys: id, role, content, provider, has_pdf, created_at.
    """
    sql = """
        SELECT id, role, content, provider, has_pdf, created_at
        FROM chat_history
        WHERE session_id = ?
        ORDER BY id ASC
        LIMIT ?
    """
    with get_connection() as conn:
        rows = conn.execute(sql, (session_id, limit)).fetchall()
        return [dict(r) for r in rows]


def get_user_chat_sessions(user_id: int, limit: int = 20) -> List[Dict]:
    """
    Return the most recent distinct sessions for a user (for a history panel).

    Args:
        user_id: The user's DB id.
        limit:   Max sessions to return.

    Returns:
        List of dicts with session_id, first_message, message_count, last_at.
    """
    sql = """
        SELECT
            session_id,
            MIN(content)  AS first_message,
            COUNT(*)      AS message_count,
            MAX(created_at) AS last_at
        FROM chat_history
        WHERE user_id = ? AND role = 'user'
        GROUP BY session_id
        ORDER BY last_at DESC
        LIMIT ?
    """
    with get_connection() as conn:
        rows = conn.execute(sql, (user_id, limit)).fetchall()
        return [dict(r) for r in rows]


def delete_chat_session(session_id: str) -> int:
    """
    Delete all messages for a session (clear chat).

    Returns:
        Number of deleted rows.
    """
    with get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM chat_history WHERE session_id = ?", (session_id,)
        )
        return cur.rowcount


# ═══════════════════════════════════════════════════════════════════════════════
# EHR — PATIENTS
# ═══════════════════════════════════════════════════════════════════════════════

def create_patient(
    full_name: str,
    user_id: Optional[int] = None,
    date_of_birth: str = "",
    age: Optional[int] = None,
    gender: str = "",
    blood_group: str = "",
    phone: str = "",
    email: str = "",
    address: str = "",
    occupation: str = "",
    emergency_contact_name: str = "",
    emergency_contact_phone: str = "",
    primary_doctor: str = "",
    notes: str = "",
) -> int:
    sql = """INSERT INTO patients
        (user_id, full_name, date_of_birth, age, gender, blood_group,
         phone, email, address, occupation,
         emergency_contact_name, emergency_contact_phone,
         primary_doctor, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
    with get_connection() as conn:
        cur = conn.execute(sql, (
            user_id, full_name, date_of_birth, age, gender, blood_group,
            phone, email, address, occupation,
            emergency_contact_name, emergency_contact_phone,
            primary_doctor, notes,
        ))
        return cur.lastrowid


def get_patient_by_user(user_id: int) -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM patients WHERE user_id=? ORDER BY id DESC LIMIT 1", (user_id,)
        ).fetchone()
        return dict(row) if row else None


def get_patient_by_id(patient_id: int) -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
        return dict(row) if row else None


def update_patient(patient_id: int, **fields) -> bool:
    allowed = {
        "full_name", "date_of_birth", "age", "gender", "blood_group",
        "phone", "email", "address", "occupation",
        "emergency_contact_name", "emergency_contact_phone",
        "primary_doctor", "health_risk_score", "notes",
    }
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return False
    set_parts = [f"{k}=?" for k in updates] + ["updated_at=datetime('now')"]
    vals = list(updates.values()) + [patient_id]
    with get_connection() as conn:
        cur = conn.execute(
            f"UPDATE patients SET {', '.join(set_parts)} WHERE id=?", vals
        )
        return cur.rowcount > 0


# ═══════════════════════════════════════════════════════════════════════════════
# EHR — REPORTS
# ═══════════════════════════════════════════════════════════════════════════════

def create_ehr_report(
    patient_id: int,
    patient_name: str,
    report_type: str,
    report_date: str,
    lab_name: str = "",
    doctor_name: str = "",
    file_name: str = "",
    ai_summary: str = "",
    raw_text: str = "",
    diagnosis: str = "",
    risk_level: str = "Normal",
    is_normal: bool = True,
    tags: str = "",
) -> int:
    sql = """INSERT INTO ehr_reports
        (patient_id, patient_name, report_type, report_date, lab_name,
         doctor_name, file_name, ai_summary, raw_text, diagnosis,
         risk_level, is_normal, tags)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"""
    with get_connection() as conn:
        cur = conn.execute(sql, (
            patient_id, patient_name, report_type, report_date, lab_name,
            doctor_name, file_name, ai_summary, raw_text, diagnosis,
            risk_level, int(is_normal), tags,
        ))
        return cur.lastrowid


def get_ehr_reports(patient_id: int) -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM ehr_reports WHERE patient_id=? ORDER BY report_date DESC",
            (patient_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def delete_ehr_report(report_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM ehr_reports WHERE id=?", (report_id,))
        return cur.rowcount > 0


# ═══════════════════════════════════════════════════════════════════════════════
# EHR — LAB RESULTS
# ═══════════════════════════════════════════════════════════════════════════════

def create_lab_result(
    patient_id: int,
    test_name: str,
    test_value: str,
    unit: str = "",
    normal_range: str = "",
    status: str = "Normal",
    tested_on: str = "",
    lab_name: str = "",
    notes: str = "",
    report_id: Optional[int] = None,
) -> int:
    sql = """INSERT INTO ehr_lab_results
        (patient_id, report_id, test_name, test_value, unit, normal_range,
         status, tested_on, lab_name, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?)"""
    with get_connection() as conn:
        cur = conn.execute(sql, (
            patient_id, report_id, test_name, test_value, unit, normal_range,
            status, tested_on, lab_name, notes,
        ))
        return cur.lastrowid


def get_lab_results(patient_id: int, limit: int = 100) -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM ehr_lab_results WHERE patient_id=? ORDER BY tested_on DESC LIMIT ?",
            (patient_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def delete_lab_result(result_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM ehr_lab_results WHERE id=?", (result_id,))
        return cur.rowcount > 0


# ═══════════════════════════════════════════════════════════════════════════════
# EHR — MEDICINES / PRESCRIPTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def create_ehr_medicine(
    patient_id: int,
    medicine_name: str,
    dosage: str,
    frequency: str,
    prescribed_by: str = "",
    start_date: str = "",
    end_date: str = "",
    notes: str = "",
) -> int:
    sql = """INSERT INTO ehr_medicines
        (patient_id, medicine_name, dosage, frequency,
         prescribed_by, start_date, end_date, notes, is_active)
        VALUES (?,?,?,?,?,?,?,?,1)"""
    with get_connection() as conn:
        cur = conn.execute(sql, (
            patient_id, medicine_name, dosage, frequency,
            prescribed_by, start_date, end_date, notes,
        ))
        return cur.lastrowid


def get_ehr_medicines(patient_id: int, active_only: bool = False) -> List[Dict]:
    sql = "SELECT * FROM ehr_medicines WHERE patient_id=?"
    params: List[Any] = [patient_id]
    if active_only:
        sql += " AND is_active=1"
    sql += " ORDER BY created_at DESC"
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def deactivate_ehr_medicine(medicine_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE ehr_medicines SET is_active=0 WHERE id=?", (medicine_id,)
        )
        return cur.rowcount > 0


# ═══════════════════════════════════════════════════════════════════════════════
# EHR — ALLERGIES
# ═══════════════════════════════════════════════════════════════════════════════

def create_ehr_allergy(
    patient_id: int,
    allergen: str,
    reaction: str = "",
    severity: str = "Mild",
    diagnosed_on: str = "",
    notes: str = "",
) -> int:
    sql = """INSERT INTO ehr_allergies
        (patient_id, allergen, reaction, severity, diagnosed_on, notes)
        VALUES (?,?,?,?,?,?)"""
    with get_connection() as conn:
        cur = conn.execute(sql, (patient_id, allergen, reaction, severity, diagnosed_on, notes))
        return cur.lastrowid


def get_ehr_allergies(patient_id: int) -> List[Dict]:
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM ehr_allergies WHERE patient_id=? ORDER BY severity, allergen",
            (patient_id,),
        ).fetchall()]


def delete_ehr_allergy(allergy_id: int) -> bool:
    with get_connection() as conn:
        return conn.execute("DELETE FROM ehr_allergies WHERE id=?", (allergy_id,)).rowcount > 0


# ═══════════════════════════════════════════════════════════════════════════════
# EHR — VITALS
# ═══════════════════════════════════════════════════════════════════════════════

def create_ehr_vital(
    patient_id: int,
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
    sql = """INSERT INTO ehr_vitals
        (patient_id, recorded_date, recorded_time, bp_systolic, bp_diastolic,
         heart_rate, temperature, weight_kg, height_cm, spo2, blood_glucose, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)"""
    with get_connection() as conn:
        cur = conn.execute(sql, (
            patient_id, recorded_date, recorded_time, bp_systolic, bp_diastolic,
            heart_rate, temperature, weight_kg, height_cm, spo2, blood_glucose, notes,
        ))
        return cur.lastrowid


def get_ehr_vitals(patient_id: int, limit: int = 50) -> List[Dict]:
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM ehr_vitals WHERE patient_id=? ORDER BY recorded_date DESC, recorded_time DESC LIMIT ?",
            (patient_id, limit),
        ).fetchall()]


# ═══════════════════════════════════════════════════════════════════════════════
# EHR — DOCTOR VISITS
# ═══════════════════════════════════════════════════════════════════════════════

def create_ehr_visit(
    patient_id: int,
    visit_date: str,
    doctor_name: str,
    specialization: str = "",
    hospital: str = "",
    chief_complaint: str = "",
    diagnosis: str = "",
    treatment: str = "",
    follow_up_date: str = "",
    notes: str = "",
) -> int:
    sql = """INSERT INTO ehr_doctor_visits
        (patient_id, visit_date, doctor_name, specialization, hospital,
         chief_complaint, diagnosis, treatment, follow_up_date, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?)"""
    with get_connection() as conn:
        cur = conn.execute(sql, (
            patient_id, visit_date, doctor_name, specialization, hospital,
            chief_complaint, diagnosis, treatment, follow_up_date, notes,
        ))
        return cur.lastrowid


def get_ehr_visits(patient_id: int) -> List[Dict]:
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM ehr_doctor_visits WHERE patient_id=? ORDER BY visit_date DESC",
            (patient_id,),
        ).fetchall()]


# ═══════════════════════════════════════════════════════════════════════════════
# EHR — VACCINATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def create_ehr_vaccination(
    patient_id: int,
    vaccine_name: str,
    administered_on: str,
    dose_number: str = "1st",
    administered_by: str = "",
    hospital: str = "",
    batch_number: str = "",
    next_due_date: str = "",
    notes: str = "",
) -> int:
    sql = """INSERT INTO ehr_vaccinations
        (patient_id, vaccine_name, administered_on, dose_number,
         administered_by, hospital, batch_number, next_due_date, notes)
        VALUES (?,?,?,?,?,?,?,?,?)"""
    with get_connection() as conn:
        cur = conn.execute(sql, (
            patient_id, vaccine_name, administered_on, dose_number,
            administered_by, hospital, batch_number, next_due_date, notes,
        ))
        return cur.lastrowid


def get_ehr_vaccinations(patient_id: int) -> List[Dict]:
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM ehr_vaccinations WHERE patient_id=? ORDER BY administered_on DESC",
            (patient_id,),
        ).fetchall()]


# ═══════════════════════════════════════════════════════════════════════════════
# EHR — MEDICAL HISTORY
# ═══════════════════════════════════════════════════════════════════════════════

def create_ehr_history(
    patient_id: int,
    condition_name: str,
    diagnosed_on: str = "",
    status: str = "Active",
    treating_doctor: str = "",
    notes: str = "",
) -> int:
    sql = """INSERT INTO ehr_medical_history
        (patient_id, condition_name, diagnosed_on, status, treating_doctor, notes)
        VALUES (?,?,?,?,?,?)"""
    with get_connection() as conn:
        cur = conn.execute(sql, (
            patient_id, condition_name, diagnosed_on, status, treating_doctor, notes,
        ))
        return cur.lastrowid


def get_ehr_history(patient_id: int) -> List[Dict]:
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM ehr_medical_history WHERE patient_id=? ORDER BY status, condition_name",
            (patient_id,),
        ).fetchall()]


def update_ehr_history_status(history_id: int, status: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE ehr_medical_history SET status=? WHERE id=?", (status, history_id)
        )
        return cur.rowcount > 0


# ═══════════════════════════════════════════════════════════════════════════════
# EHR — DASHBOARD SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

def get_ehr_dashboard(patient_id: int) -> Dict:
    """Return aggregate stats for the Patient Dashboard."""
    with get_connection() as conn:
        reports   = conn.execute("SELECT COUNT(*) FROM ehr_reports   WHERE patient_id=?", (patient_id,)).fetchone()[0]
        meds      = conn.execute("SELECT COUNT(*) FROM ehr_medicines  WHERE patient_id=? AND is_active=1", (patient_id,)).fetchone()[0]
        allergies = conn.execute("SELECT COUNT(*) FROM ehr_allergies  WHERE patient_id=?", (patient_id,)).fetchone()[0]
        visits    = conn.execute("SELECT COUNT(*) FROM ehr_doctor_visits WHERE patient_id=?", (patient_id,)).fetchone()[0]
        vaccs     = conn.execute("SELECT COUNT(*) FROM ehr_vaccinations WHERE patient_id=?", (patient_id,)).fetchone()[0]
        abnormal  = conn.execute(
            "SELECT COUNT(*) FROM ehr_lab_results WHERE patient_id=? AND status='Abnormal'", (patient_id,)
        ).fetchone()[0]
        latest_report = conn.execute(
            "SELECT report_date FROM ehr_reports WHERE patient_id=? ORDER BY report_date DESC LIMIT 1",
            (patient_id,),
        ).fetchone()
        next_visit = conn.execute(
            "SELECT follow_up_date FROM ehr_doctor_visits WHERE patient_id=? AND follow_up_date>date('now') ORDER BY follow_up_date LIMIT 1",
            (patient_id,),
        ).fetchone()
    return {
        "total_reports":    reports,
        "active_medicines": meds,
        "allergies":        allergies,
        "doctor_visits":    visits,
        "vaccinations":     vaccs,
        "abnormal_labs":    abnormal,
        "latest_report":    latest_report[0] if latest_report else "—",
        "next_followup":    next_visit[0]    if next_visit    else "—",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# EHR — HOSPITAL VISITS
# ═══════════════════════════════════════════════════════════════════════════════

def create_hospital_visit(
    patient_name: str,
    hospital_name: str,
    hospital_address: str,
    hospital_contact: str,
    department_visited: str,
    doctor_name: str,
    visit_date: str,
    reason_for_visit: str,
    emergency_contact: Optional[str] = "",
) -> int:
    """Insert a new hospital visit and return its ID."""
    sql = """
        INSERT INTO hospital_visits
            (patient_name, hospital_name, hospital_address, hospital_contact,
             specialty, doctor_name, visit_date, reason_notes, emergency_contact)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    with get_connection() as conn:
        cursor = conn.execute(sql, (
            patient_name, hospital_name, hospital_address, hospital_contact,
            department_visited, doctor_name, visit_date, reason_for_visit,
            emergency_contact or ""
        ))
        return cursor.lastrowid


def get_hospital_visits(patient_name: Optional[str] = None) -> List[Dict]:
    """Retrieve hospital visits, optionally filtered by patient name.
    Columns are aliased so callers can use 'department_visited' and 'reason_for_visit'.
    """
    _COLS = """
        id, patient_name, hospital_name, hospital_address, hospital_contact,
        specialty         AS department_visited,
        doctor_name,
        visit_date,
        reason_notes      AS reason_for_visit,
        emergency_contact,
        created_at
    """
    if patient_name:
        sql = f"SELECT {_COLS} FROM hospital_visits WHERE LOWER(patient_name) = LOWER(?) ORDER BY visit_date DESC, created_at DESC"
        with get_connection() as conn:
            rows = conn.execute(sql, (patient_name,)).fetchall()
    else:
        sql = f"SELECT {_COLS} FROM hospital_visits ORDER BY visit_date DESC, created_at DESC"
        with get_connection() as conn:
            rows = conn.execute(sql).fetchall()
    return [dict(r) for r in rows]

