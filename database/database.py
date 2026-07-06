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


def init_db() -> None:
    """Initialize the database by running schema.sql and seeding doctors."""
    try:
        with get_connection() as conn:
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
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
    patient_name: str,
    doctor_name: str,
    specialization: str,
    appointment_date: str,
    appointment_time: str,
    notes: str = "",
) -> int:
    """Insert a new appointment and return its ID."""
    sql = """
        INSERT INTO appointments
            (patient_name, doctor_name, specialization, appointment_date, appointment_time, status, notes)
        VALUES (?, ?, ?, ?, ?, 'scheduled', ?)
    """
    with get_connection() as conn:
        cursor = conn.execute(sql, (patient_name, doctor_name, specialization,
                                    appointment_date, appointment_time, notes))
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
    doctor_name: str, appointment_date: str, appointment_time: str
) -> bool:
    """Return True if a scheduled appointment already exists for that slot."""
    sql = """
        SELECT COUNT(*) FROM appointments
        WHERE LOWER(doctor_name) = LOWER(?)
          AND appointment_date = ?
          AND appointment_time = ?
          AND status = 'scheduled'
    """
    with get_connection() as conn:
        count = conn.execute(sql, (doctor_name, appointment_date, appointment_time)).fetchone()[0]
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
