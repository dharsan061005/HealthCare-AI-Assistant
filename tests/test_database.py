"""
Smoke tests: database initialization and basic CRUD operations.
Run with: python -m pytest tests/ -v
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path

# Ensure project root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))


@pytest.fixture(autouse=True)
def use_temp_db(tmp_path, monkeypatch):
    """Redirect the database to a temp file for each test."""
    import database.database as db_module
    import sqlite3 as _sqlite3
    temp_db = str(tmp_path / "test_healthcare.db")
    monkeypatch.setattr(db_module, "DB_PATH", temp_db)
    db_module.init_db()
    yield
    # Close all lingering SQLite connections before cleanup (Windows WAL lock fix)
    try:
        _conn = _sqlite3.connect(temp_db)
        _conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        _conn.close()
    except Exception:
        pass
    # Ignore deletion errors on Windows — temp files are cleaned up by OS
    try:
        if os.path.exists(temp_db):
            os.remove(temp_db)
    except PermissionError:
        pass  # Windows WAL lock; file will be cleaned by OS


def test_db_initializes():
    """Database should initialize without errors and doctors table should be seeded."""
    from database.database import get_all_doctors
    doctors = get_all_doctors()
    assert len(doctors) > 0, "Doctors table should be seeded on init"


def test_create_and_get_appointment():
    """Should create an appointment and retrieve it."""
    from database.database import create_appointment, get_appointments, get_appointment_by_id

    apt_id = create_appointment(
        patient_name="Test Patient",
        doctor_name="Dr. Suresh Patel",
        specialization="General Medicine",
        appointment_date="2027-01-15",
        appointment_time="10:00",
        notes="Test notes",
    )
    assert apt_id is not None and apt_id > 0

    apt = get_appointment_by_id(apt_id)
    assert apt is not None
    assert apt["patient_name"] == "Test Patient"
    assert apt["status"] == "scheduled"

    all_apts = get_appointments(patient_name="Test Patient")
    assert len(all_apts) == 1


def test_duplicate_appointment_detection():
    """Should detect a duplicate appointment for the same slot."""
    from database.database import create_appointment, check_duplicate_appointment

    create_appointment(
        patient_name="Alice",
        doctor_name="Dr. Suresh Patel",
        specialization="General Medicine",
        appointment_date="2027-02-10",
        appointment_time="09:00",
    )

    is_duplicate = check_duplicate_appointment("Dr. Suresh Patel", "2027-02-10", "09:00")
    assert is_duplicate is True

    not_duplicate = check_duplicate_appointment("Dr. Suresh Patel", "2027-02-10", "10:00")
    assert not_duplicate is False


def test_cancel_appointment():
    """Should cancel an appointment and update its status."""
    from database.database import create_appointment, update_appointment_status, get_appointment_by_id

    apt_id = create_appointment(
        patient_name="Bob",
        doctor_name="Dr. Suresh Patel",
        specialization="General Medicine",
        appointment_date="2027-03-01",
        appointment_time="11:00",
    )
    success = update_appointment_status(apt_id, "cancelled")
    assert success is True

    apt = get_appointment_by_id(apt_id)
    assert apt["status"] == "cancelled"


def test_reschedule_appointment():
    """Should reschedule an appointment to a new date/time."""
    from database.database import create_appointment, reschedule_appointment, get_appointment_by_id

    apt_id = create_appointment(
        patient_name="Carol",
        doctor_name="Dr. Rajesh Kumar",
        specialization="Neurology",
        appointment_date="2027-03-10",
        appointment_time="14:00",
    )
    success = reschedule_appointment(apt_id, "2027-03-15", "15:00")
    assert success is True

    apt = get_appointment_by_id(apt_id)
    assert apt["appointment_date"] == "2027-03-15"
    assert apt["appointment_time"] == "15:00"
    assert apt["status"] == "scheduled"


def test_create_and_manage_reminders():
    """Should create, retrieve, update, and delete reminders."""
    from database.database import (
        create_reminder, get_reminders, get_reminder_by_id,
        update_reminder, delete_reminder,
    )

    rid = create_reminder(
        medicine_name="Metformin",
        dosage="500mg",
        reminder_time="08:00",
        frequency="Twice daily",
        patient_name="Dave",
        notes="Take after breakfast",
    )
    assert rid > 0

    reminders = get_reminders(patient_name="Dave")
    assert len(reminders) == 1
    assert reminders[0]["medicine_name"] == "Metformin"

    success = update_reminder(
        reminder_id=rid,
        medicine_name="Metformin XR",
        dosage="1000mg",
        reminder_time="09:00",
        frequency="Once daily",
        patient_name="Dave",
        notes="Take after dinner",
    )
    assert success is True

    updated = get_reminder_by_id(rid)
    assert updated["medicine_name"] == "Metformin XR"
    assert updated["dosage"] == "1000mg"

    deleted = delete_reminder(rid)
    assert deleted is True

    active = get_reminders(patient_name="Dave", active_only=True)
    assert len(active) == 0


def test_app_imports_without_error():
    """All agent modules should import cleanly."""
    import config  # noqa: F401
    from agents.router import NAV_ITEMS, get_agent_renderer  # noqa: F401
    from utils.llm import simple_query  # noqa: F401
    from utils.validators import validate_patient_name  # noqa: F401
    from utils.helpers import format_date  # noqa: F401
    assert len(NAV_ITEMS) == 5
