# Healthcare AI Assistant — Requirements

## Functional Requirements

### FR-1: Appointment Scheduling Agent
- Book appointments: patient name, doctor, specialization, date, time, optional notes
- Prevent duplicate bookings for the same doctor/date/time slot
- View appointments filtered by patient name and/or status
- Cancel appointments (status → cancelled)
- Reschedule appointments to a new date/time with duplicate check
- Show doctor availability for a selected date (booked vs. free slots)
- Persist all data in SQLite

### FR-2: Symptom Checker Agent
- Accept natural language symptom descriptions via chat interface
- Call OpenAI LLM to return: possible conditions, self-care guidance, when to see a doctor
- Maintain full session chat history (multi-turn conversation)
- Display medical disclaimer after every AI response
- Quick-start example buttons for new users

### FR-3: Medical Report Summarizer Agent
- Accept PDF file upload (pdfplumber extraction)
- Send extracted text to LLM for structured summary:
  - Overall Summary, Key Findings, Abnormal Values, Recommendations
- Handle truncation of large reports gracefully
- Allow download of summary as .txt file
- Show raw extracted text in expandable section

### FR-4: Prescription Reminder Agent
- Add reminders: medicine name, dosage, time, frequency, patient, notes
- View all active reminders sorted by time; show next upcoming reminder
- Edit any field of an existing reminder
- Soft-delete reminders (is_active = 0)
- No background scheduler; display-only upcoming reminders

### FR-5: Hospital Information Agent
- Display hospital overview, contact, timings, accreditations from JSON
- List all departments with services, floor, HOD, phone
- List all doctors with specialization filter; show qualifications, slots, fees
- Show facilities with 24/7 status
- Insurance partners and government schemes
- FAQ section
- LLM chat fallback for questions not answered by JSON data

## Non-Functional Requirements
- NFR-1: All LLM calls must have graceful error handling with user-friendly messages
- NFR-2: App must load and show UI even without an OpenAI API key
- NFR-3: Input validation on all forms with clear error messages
- NFR-4: SQLite database auto-created and seeded on first run
- NFR-5: Modular code — each agent is an independent module
