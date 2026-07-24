-- Healthcare AI Assistant Database Schema

-- ─── Users / Authentication ──────────────────────────────────────────────────

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

CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hospital_name TEXT NOT NULL DEFAULT 'General Hospital',
    patient_name TEXT NOT NULL,
    age INTEGER,
    gender TEXT,
    mobile_number TEXT,
    email TEXT,
    reason_for_visit TEXT,
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

-- ─── Caregiver / Companion ───────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS caregivers (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name            TEXT    NOT NULL,
    caregiver_name          TEXT    NOT NULL,
    relationship            TEXT    NOT NULL,
    mobile_number           TEXT    NOT NULL,
    email                   TEXT    NOT NULL,
    notification_preference TEXT    NOT NULL DEFAULT 'Email',
    is_active               INTEGER NOT NULL DEFAULT 1,
    created_at              TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS notification_log (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    caregiver_id      INTEGER NOT NULL REFERENCES caregivers(id),
    patient_name      TEXT    NOT NULL,
    notification_type TEXT    NOT NULL,   -- 'reminder' | 'report' | 'missed_medicine'
    channel           TEXT    NOT NULL,   -- 'email' | 'sms' | 'whatsapp'
    subject           TEXT,
    body              TEXT,
    status            TEXT    NOT NULL DEFAULT 'sent',   -- 'sent' | 'failed' | 'pending'
    sent_at           TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_caregivers_patient    ON caregivers(patient_name);
CREATE INDEX IF NOT EXISTS idx_caregivers_active     ON caregivers(is_active);
CREATE INDEX IF NOT EXISTS idx_notif_log_caregiver   ON notification_log(caregiver_id);
CREATE INDEX IF NOT EXISTS idx_notif_log_patient     ON notification_log(patient_name);
CREATE INDEX IF NOT EXISTS idx_notif_log_type        ON notification_log(notification_type);
CREATE INDEX IF NOT EXISTS idx_notif_log_sent_at     ON notification_log(sent_at);

-- ─── AI Health Assistant — Chat History ──────────────────────────────────────

CREATE TABLE IF NOT EXISTS chat_history (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER,                          -- NULL for guest sessions
    session_id    TEXT    NOT NULL,                 -- UUID per browser session
    role          TEXT    NOT NULL,                 -- 'user' | 'assistant'
    content       TEXT    NOT NULL,
    provider      TEXT    NOT NULL DEFAULT 'groq',  -- 'groq' | 'gemini'
    has_pdf       INTEGER NOT NULL DEFAULT 0,       -- 1 if a PDF was attached
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_chat_history_session  ON chat_history(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_user     ON chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_created  ON chat_history(created_at);

-- ─── Patient EHR — Core Patient Record ───────────────────────────────────────

CREATE TABLE IF NOT EXISTS patients (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER,                        -- linked to auth users table
    full_name       TEXT    NOT NULL,
    date_of_birth   TEXT    NOT NULL DEFAULT '',
    age             INTEGER,
    gender          TEXT    NOT NULL DEFAULT '',
    blood_group     TEXT    NOT NULL DEFAULT '',
    phone           TEXT    NOT NULL DEFAULT '',
    email           TEXT    NOT NULL DEFAULT '',
    address         TEXT    NOT NULL DEFAULT '',
    occupation      TEXT    NOT NULL DEFAULT '',
    emergency_contact_name  TEXT NOT NULL DEFAULT '',
    emergency_contact_phone TEXT NOT NULL DEFAULT '',
    primary_doctor  TEXT    NOT NULL DEFAULT '',
    health_risk_score       INTEGER NOT NULL DEFAULT 0,
    notes           TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_patients_user ON patients(user_id);
CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(full_name);

-- ─── Medical Reports (EHR — separate from AI chat) ───────────────────────────

CREATE TABLE IF NOT EXISTS ehr_reports (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      INTEGER NOT NULL REFERENCES patients(id),
    patient_name    TEXT    NOT NULL,
    report_type     TEXT    NOT NULL,
    report_date     TEXT    NOT NULL DEFAULT (date('now')),
    lab_name        TEXT    NOT NULL DEFAULT '',
    doctor_name     TEXT    NOT NULL DEFAULT '',
    file_name       TEXT    NOT NULL DEFAULT '',
    ai_summary      TEXT    NOT NULL DEFAULT '',
    raw_text        TEXT    NOT NULL DEFAULT '',
    diagnosis       TEXT    NOT NULL DEFAULT '',
    risk_level      TEXT    NOT NULL DEFAULT 'Normal',
    is_normal       INTEGER NOT NULL DEFAULT 1,
    tags            TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_ehr_reports_patient ON ehr_reports(patient_id);
CREATE INDEX IF NOT EXISTS idx_ehr_reports_date    ON ehr_reports(report_date);
CREATE INDEX IF NOT EXISTS idx_ehr_reports_type    ON ehr_reports(report_type);

-- ─── Lab Results ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ehr_lab_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      INTEGER NOT NULL REFERENCES patients(id),
    report_id       INTEGER REFERENCES ehr_reports(id),
    test_name       TEXT    NOT NULL,
    test_value      TEXT    NOT NULL,
    unit            TEXT    NOT NULL DEFAULT '',
    normal_range    TEXT    NOT NULL DEFAULT '',
    status          TEXT    NOT NULL DEFAULT 'Normal',  -- Normal | Abnormal | Borderline
    tested_on       TEXT    NOT NULL DEFAULT (date('now')),
    lab_name        TEXT    NOT NULL DEFAULT '',
    notes           TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_lab_patient  ON ehr_lab_results(patient_id);
CREATE INDEX IF NOT EXISTS idx_lab_date     ON ehr_lab_results(tested_on);
CREATE INDEX IF NOT EXISTS idx_lab_status   ON ehr_lab_results(status);

-- ─── Prescriptions / Medicines ────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ehr_medicines (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      INTEGER NOT NULL REFERENCES patients(id),
    medicine_name   TEXT    NOT NULL,
    dosage          TEXT    NOT NULL,
    frequency       TEXT    NOT NULL,
    prescribed_by   TEXT    NOT NULL DEFAULT '',
    start_date      TEXT    NOT NULL DEFAULT (date('now')),
    end_date        TEXT    NOT NULL DEFAULT '',
    is_active       INTEGER NOT NULL DEFAULT 1,
    notes           TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_ehr_med_patient ON ehr_medicines(patient_id);
CREATE INDEX IF NOT EXISTS idx_ehr_med_active  ON ehr_medicines(is_active);

-- ─── Allergies ────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ehr_allergies (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      INTEGER NOT NULL REFERENCES patients(id),
    allergen        TEXT    NOT NULL,
    reaction        TEXT    NOT NULL DEFAULT '',
    severity        TEXT    NOT NULL DEFAULT 'Mild',  -- Mild | Moderate | Severe
    diagnosed_on    TEXT    NOT NULL DEFAULT '',
    notes           TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_allergy_patient ON ehr_allergies(patient_id);

-- ─── Vital Signs ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ehr_vitals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      INTEGER NOT NULL REFERENCES patients(id),
    recorded_date   TEXT    NOT NULL DEFAULT (date('now')),
    recorded_time   TEXT    NOT NULL DEFAULT (time('now')),
    bp_systolic     INTEGER,
    bp_diastolic    INTEGER,
    heart_rate      INTEGER,
    temperature     REAL,
    weight_kg       REAL,
    height_cm       REAL,
    spo2            INTEGER,
    blood_glucose   INTEGER,
    notes           TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_vitals_patient ON ehr_vitals(patient_id);
CREATE INDEX IF NOT EXISTS idx_vitals_date    ON ehr_vitals(recorded_date);

-- ─── Doctor Visits ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ehr_doctor_visits (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      INTEGER NOT NULL REFERENCES patients(id),
    visit_date      TEXT    NOT NULL,
    doctor_name     TEXT    NOT NULL,
    specialization  TEXT    NOT NULL DEFAULT '',
    hospital        TEXT    NOT NULL DEFAULT '',
    chief_complaint TEXT    NOT NULL DEFAULT '',
    diagnosis       TEXT    NOT NULL DEFAULT '',
    treatment       TEXT    NOT NULL DEFAULT '',
    follow_up_date  TEXT    NOT NULL DEFAULT '',
    notes           TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_visits_patient ON ehr_doctor_visits(patient_id);
CREATE INDEX IF NOT EXISTS idx_visits_date    ON ehr_doctor_visits(visit_date);

-- ─── Vaccination History ──────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ehr_vaccinations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      INTEGER NOT NULL REFERENCES patients(id),
    vaccine_name    TEXT    NOT NULL,
    dose_number     TEXT    NOT NULL DEFAULT '1st',
    administered_on TEXT    NOT NULL,
    administered_by TEXT    NOT NULL DEFAULT '',
    hospital        TEXT    NOT NULL DEFAULT '',
    batch_number    TEXT    NOT NULL DEFAULT '',
    next_due_date   TEXT    NOT NULL DEFAULT '',
    notes           TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_vacc_patient ON ehr_vaccinations(patient_id);
CREATE INDEX IF NOT EXISTS idx_vacc_date    ON ehr_vaccinations(administered_on);

-- ─── Medical History (conditions) ────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ehr_medical_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      INTEGER NOT NULL REFERENCES patients(id),
    condition_name  TEXT    NOT NULL,
    diagnosed_on    TEXT    NOT NULL DEFAULT '',
    status          TEXT    NOT NULL DEFAULT 'Active',  -- Active | Resolved | Chronic
    treating_doctor TEXT    NOT NULL DEFAULT '',
    notes           TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_history_patient ON ehr_medical_history(patient_id);
CREATE INDEX IF NOT EXISTS idx_history_status  ON ehr_medical_history(status);

-- ─── Hospital Visits ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS hospital_visits (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name      TEXT    NOT NULL,
    hospital_name     TEXT    NOT NULL,
    hospital_address  TEXT    NOT NULL,
    hospital_contact  TEXT    NOT NULL,
    specialty         TEXT    NOT NULL,
    doctor_name       TEXT    NOT NULL,
    visit_date        TEXT    NOT NULL,
    reason_notes      TEXT    NOT NULL,
    emergency_contact TEXT    DEFAULT '',
    created_at        TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_hospital_visits_patient ON hospital_visits(patient_name);

