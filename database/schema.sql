-- Healthcare AI Assistant Database Schema

CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name TEXT NOT NULL,
    doctor_name TEXT NOT NULL,
    specialization TEXT NOT NULL,
    appointment_date TEXT NOT NULL,
    appointment_time TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'scheduled',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    notes TEXT
);

CREATE TABLE IF NOT EXISTS doctors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_name TEXT NOT NULL UNIQUE,
    specialization TEXT NOT NULL,
    available_slots TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS medicine_reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_name TEXT NOT NULL,
    dosage TEXT NOT NULL,
    reminder_time TEXT NOT NULL,
    frequency TEXT NOT NULL,
    patient_name TEXT,
    notes TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_appointments_patient   ON appointments(patient_name);
CREATE INDEX IF NOT EXISTS idx_appointments_status    ON appointments(status);
CREATE INDEX IF NOT EXISTS idx_appointments_date      ON appointments(appointment_date);
CREATE INDEX IF NOT EXISTS idx_appointments_doctor    ON appointments(doctor_name);
CREATE INDEX IF NOT EXISTS idx_reminders_patient      ON medicine_reminders(patient_name);
CREATE INDEX IF NOT EXISTS idx_reminders_active       ON medicine_reminders(is_active);
CREATE INDEX IF NOT EXISTS idx_reminders_time         ON medicine_reminders(reminder_time);
