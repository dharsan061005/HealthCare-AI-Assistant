"""
Verification tests for patient record cascade deletion.
Run with: python -m pytest tests/test_deletion.py -v
"""

import os
import sys
import sqlite3
import pytest
from pathlib import Path

# Ensure project root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import database.database as db_module
from utils.delete_patient import delete_patient_by_id, AUDIT_LOG_PATH


@pytest.fixture(autouse=True)
def setup_test_env(tmp_path, monkeypatch):
    """Setup temporary database and audit log for isolation."""
    temp_db = str(tmp_path / "test_healthcare.db")
    temp_audit = str(tmp_path / "test_audit_log.txt")

    monkeypatch.setattr(db_module, "DB_PATH", temp_db)
    import utils.delete_patient
    monkeypatch.setattr(utils.delete_patient, "AUDIT_LOG_PATH", temp_audit)

    db_module.init_db()
    yield temp_audit
    
    # Clean up sqlite connections
    try:
        conn = sqlite3.connect(temp_db)
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.close()
    except Exception:
        pass


def test_cascade_deletion(setup_test_env):
    """Test that a patient and all their referencing and name-matching records are deleted."""
    audit_file = setup_test_env

    # 1. Create a test patient
    from database.database import (
        create_patient, create_ehr_report, create_lab_result,
        create_ehr_medicine, create_ehr_allergy, create_ehr_vital,
        create_ehr_visit, create_ehr_vaccination, create_ehr_history,
        create_appointment, create_reminder, create_caregiver,
        log_notification, get_patient_by_id, get_connection
    )

    pid = create_patient(
        full_name="Deletable Patient",
        email="delete_me@example.com"
    )
    assert pid > 0

    # 2. Add referencing records
    rid = create_ehr_report(pid, "Deletable Patient", "Lab Report", "2027-01-01")
    create_lab_result(pid, "FBS", "99", report_id=rid)
    create_ehr_medicine(pid, "Aspirin", "75mg", "Once daily")
    create_ehr_allergy(pid, "Penicillin")
    create_ehr_vital(pid, "2027-01-01", "10:00", bp_systolic=120, bp_diastolic=80)
    create_ehr_visit(pid, "2027-01-01", "Dr. Patel")
    create_ehr_vaccination(pid, "Covid19", "2027-01-01")
    create_ehr_history(pid, "Hypertension")

    # Name matching records
    create_appointment(
        hospital_name="Apollo Hospital",
        patient_name="Deletable Patient",
        age=30,
        gender="Male",
        mobile_number="+91 98765 43210",
        email="",
        reason_for_visit="Consultation",
        doctor_name="Dr. Patel",
        specialization="Cardiology",
        appointment_date="2027-01-02",
        appointment_time="12:00"
    )
    create_reminder("Aspirin", "75mg", "08:00", "Daily", patient_name="Deletable Patient")
    cg_id = create_caregiver("Deletable Patient", "Care Giver", "Spouse", "12345", "cg@example.com")
    log_notification(cg_id, "Deletable Patient", "reminder", "email")

    # 3. Assert relations exist before delete
    with get_connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM patients WHERE id = ?", (pid,)).fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM ehr_reports WHERE patient_id = ?", (pid,)).fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM ehr_lab_results WHERE patient_id = ?", (pid,)).fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM ehr_medicines WHERE patient_id = ?", (pid,)).fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM ehr_allergies WHERE patient_id = ?", (pid,)).fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM ehr_vitals WHERE patient_id = ?", (pid,)).fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM ehr_doctor_visits WHERE patient_id = ?", (pid,)).fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM ehr_vaccinations WHERE patient_id = ?", (pid,)).fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM ehr_medical_history WHERE patient_id = ?", (pid,)).fetchone()[0] == 1

        assert conn.execute("SELECT COUNT(*) FROM appointments WHERE patient_name = 'Deletable Patient'").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM medicine_reminders WHERE patient_name = 'Deletable Patient'").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM caregivers WHERE patient_name = 'Deletable Patient'").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM notification_log WHERE patient_name = 'Deletable Patient'").fetchone()[0] == 1

    # 4. Perform Delete
    success = delete_patient_by_id(pid)
    assert success is True

    # 5. Assert all records are deleted in DB
    with get_connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM patients WHERE id = ?", (pid,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM ehr_reports WHERE patient_id = ?", (pid,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM ehr_lab_results WHERE patient_id = ?", (pid,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM ehr_medicines WHERE patient_id = ?", (pid,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM ehr_allergies WHERE patient_id = ?", (pid,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM ehr_vitals WHERE patient_id = ?", (pid,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM ehr_doctor_visits WHERE patient_id = ?", (pid,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM ehr_vaccinations WHERE patient_id = ?", (pid,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM ehr_medical_history WHERE patient_id = ?", (pid,)).fetchone()[0] == 0

        assert conn.execute("SELECT COUNT(*) FROM appointments WHERE patient_name = 'Deletable Patient'").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM medicine_reminders WHERE patient_name = 'Deletable Patient'").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM caregivers WHERE patient_name = 'Deletable Patient'").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM notification_log WHERE patient_name = 'Deletable Patient'").fetchone()[0] == 0

    # 6. Verify audit trail log file
    assert os.path.exists(audit_file)
    with open(audit_file, "r", encoding="utf-8") as f:
        log_content = f.read()
        assert "Deletable Patient" in log_content
        assert "Cascade Hard Delete" in log_content
        assert f"Patient ID: {pid}" in log_content
        assert "Status: Success" in log_content
