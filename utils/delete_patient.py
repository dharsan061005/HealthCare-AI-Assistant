"""
Patient Record Cascade Deletion Tool — Healthcare AI Assistant.
Provides a secure cascade deletion database function and records an audit trail.
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime
from typing import Dict, Optional

# Ensure base/database imports work properly
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_BASE_DIR)
if _PROJECT_DIR not in sys.path:
    sys.path.insert(0, _PROJECT_DIR)

from database.database import get_connection

logger = logging.getLogger(__name__)

AUDIT_LOG_PATH = os.path.join(_PROJECT_DIR, "data", "audit_log.txt")


def delete_patient_by_id(patient_id: int) -> bool:
    """
    Performs a cascade transaction delete on a patient and all referencing records,
    logging the audit report on success.
    """
    # 1. Fetch patient detail first for auditing
    patient = None
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
        if row:
            patient = dict(row)

    if not patient:
        logger.error("Patient delete failed: ID %s not found.", patient_id)
        return False

    patient_name = patient["full_name"]
    patient_email = patient.get("email", "")

    # 2. Begin transaction deletion
    try:
        with get_connection() as conn:
            conn.execute("BEGIN TRANSACTION;")

            # Delete strict foreign-key referencing tables in EHR
            conn.execute("DELETE FROM ehr_lab_results WHERE patient_id = ?", (patient_id,))
            conn.execute("DELETE FROM ehr_reports WHERE patient_id = ?", (patient_id,))
            conn.execute("DELETE FROM ehr_medicines WHERE patient_id = ?", (patient_id,))
            conn.execute("DELETE FROM ehr_allergies WHERE patient_id = ?", (patient_id,))
            conn.execute("DELETE FROM ehr_vitals WHERE patient_id = ?", (patient_id,))
            conn.execute("DELETE FROM ehr_doctor_visits WHERE patient_id = ?", (patient_id,))
            conn.execute("DELETE FROM ehr_vaccinations WHERE patient_id = ?", (patient_id,))
            conn.execute("DELETE FROM ehr_medical_history WHERE patient_id = ?", (patient_id,))

            # Delete soft/loose matches on name text
            if patient_name:
                conn.execute("DELETE FROM appointments WHERE patient_name = ?", (patient_name,))
                conn.execute("DELETE FROM medicine_reminders WHERE patient_name = ?", (patient_name,))
                conn.execute("DELETE FROM notification_log WHERE patient_name = ?", (patient_name,))
                conn.execute("DELETE FROM caregivers WHERE patient_name = ?", (patient_name,))

            # Delete core patient record
            conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
            conn.execute("COMMIT;")

        # 3. Write Audit trail log
        timestamp = datetime.now().isoformat()
        os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n--- PATIENT RECORD DELETION AUDIT TRAIL ---\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Action: Cascade Hard Delete\n")
            f.write(f"Patient ID: {patient_id}\n")
            f.write(f"Patient Name: {patient_name}\n")
            f.write(f"Patient Email: {patient_email}\n")
            f.write(f"Performed By: System/Admin (AI Command Line)\n")
            f.write(f"Status: Success\n")
            f.write(f"-------------------------------------------\n")

        logger.info("Patient ID %s successfully deleted and logged to audit trail.", patient_id)
        return True

    except Exception as e:
        logger.exception("Failed to execute cascade delete transaction for patient %s: %s", patient_id, e)
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python delete_patient.py <patient_id>")
        sys.exit(1)
    try:
        pid = int(sys.argv[1])
        success = delete_patient_by_id(pid)
        if success:
            print(f"Success: Patient record ID {pid} and related records have been deleted.")
        else:
            print(f"Error: Failed to delete patient ID {pid}.")
    except ValueError:
        print("Error: Patient ID must be an integer.")
        sys.exit(1)
