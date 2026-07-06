"""
Smoke tests for agent utility functions (no Streamlit UI, no API calls).
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))


# ─── Validators ──────────────────────────────────────────────────────────────

def test_validate_patient_name_valid():
    from utils.validators import validate_patient_name
    ok, msg = validate_patient_name("Ravi Kumar")
    assert ok is True
    assert msg == ""


def test_validate_patient_name_empty():
    from utils.validators import validate_patient_name
    ok, msg = validate_patient_name("")
    assert ok is False


def test_validate_patient_name_special_chars():
    from utils.validators import validate_patient_name
    ok, msg = validate_patient_name("R@vi123")
    assert ok is False


def test_validate_appointment_date_past():
    from utils.validators import validate_appointment_date
    from datetime import date
    past_date = date(2020, 1, 1)
    ok, msg = validate_appointment_date(past_date)
    assert ok is False
    assert "past" in msg.lower()


def test_validate_appointment_date_future():
    from utils.validators import validate_appointment_date
    from datetime import date
    future_date = date(2027, 6, 15)
    ok, msg = validate_appointment_date(future_date)
    assert ok is True


def test_validate_medicine_name():
    from utils.validators import validate_medicine_name
    ok, _ = validate_medicine_name("Aspirin 100mg")
    assert ok is True

    ok, _ = validate_medicine_name("")
    assert ok is False


def test_validate_reminder_time_valid():
    from utils.validators import validate_reminder_time
    ok, _ = validate_reminder_time("08:30")
    assert ok is True


def test_validate_reminder_time_invalid():
    from utils.validators import validate_reminder_time
    ok, _ = validate_reminder_time("25:00")
    assert ok is False


def test_validate_symptoms_input():
    from utils.validators import validate_symptoms_input
    ok, _ = validate_symptoms_input("I have a severe headache and fever for 2 days.")
    assert ok is True

    ok, _ = validate_symptoms_input("   ")
    assert ok is False


# ─── Helpers ─────────────────────────────────────────────────────────────────

def test_format_date():
    from utils.helpers import format_date
    assert format_date("2027-03-15") == "15 Mar 2027"
    assert format_date("bad-date") == "bad-date"  # fallback


def test_format_time_12h():
    from utils.helpers import format_time_12h
    assert format_time_12h("09:00") == "09:00 AM"
    assert format_time_12h("14:30") == "02:30 PM"


def test_truncate_text():
    from utils.helpers import truncate_text
    assert truncate_text("Hello", 10) == "Hello"
    assert len(truncate_text("A" * 100, 20)) == 20
    assert truncate_text("A" * 100, 20).endswith("...")


def test_group_by_key():
    from utils.helpers import group_by_key
    items = [
        {"dept": "Cardiology", "name": "Dr. A"},
        {"dept": "Neurology", "name": "Dr. B"},
        {"dept": "Cardiology", "name": "Dr. C"},
    ]
    grouped = group_by_key(items, "dept")
    assert len(grouped["Cardiology"]) == 2
    assert len(grouped["Neurology"]) == 1
