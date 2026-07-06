# Healthcare AI Assistant

An AI-powered healthcare assistant built with Streamlit and Google Gemini, combining 5 intelligent agents in one app.

## Features

| Agent | Description |
|-------|-------------|
| **Hospital Information** | Browse departments, doctors, facilities, timings, and insurance from local JSON |
| **Appointment Scheduling** | Book, view, cancel, and reschedule appointments with duplicate prevention |
| **Symptom Checker** | Describe symptoms in natural language; Gemini returns conditions + self-care tips |
| **Report Summarizer** | Upload a PDF report; Gemini returns a structured summary + downloadable .txt |
| **Prescription Reminders** | Add, edit, delete, and view medicine reminders sorted by time |

---

## Quick Start

### 1. Navigate to the project folder

```
cd "Healthcare_AI_Assistant"
```

### 2. Create a virtual environment and install dependencies

```
python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Configure your Gemini API key

```
copy .env.example .env
```

Then edit `.env` and replace `your-gemini-api-key-here` with your real key from
https://aistudio.google.com/app/apikey

### 4. Run the app

```
streamlit run app.py
```

The app opens at http://localhost:8501

---

## Folder Structure

```
Healthcare_AI_Assistant/
+-- app.py                          Main Streamlit entry point
+-- config.py                       Centralized config (loads .env)
+-- requirements.txt
+-- .env.example                    Copy to .env and add your Gemini API key
+-- agents/
|   +-- appointment_agent.py
|   +-- symptom_checker_agent.py
|   +-- report_summarizer_agent.py
|   +-- prescription_reminder_agent.py
|   +-- hospital_information_agent.py
|   +-- router.py
+-- database/
|   +-- database.py                 All SQLite CRUD operations
|   +-- schema.sql                  Table definitions
|   +-- healthcare.db               Auto-created on first run
+-- utils/
|   +-- llm.py                      Gemini wrapper with graceful fallback
|   +-- pdf_reader.py               pdfplumber text extraction
|   +-- validators.py               Input validation
|   +-- helpers.py                  Formatting utilities
|   +-- constants.py                LLM prompts, dropdown options
+-- data/
|   +-- doctors.json
|   +-- departments.json
|   +-- hospital_info.json
|   +-- sample_reports/
+-- assets/
|   +-- styles.css
+-- tests/
    +-- test_database.py
    +-- test_agents.py
```

---

## Running Tests

```
pip install pytest
python -m pytest tests/ -v
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| GEMINI_API_KEY | For LLM features | - | Your Google Gemini API key |
| GEMINI_MODEL | No | gemini-2.5-flash | Gemini model to use |
| GEMINI_MAX_TOKENS | No | 1024 | Max output tokens per response |
| GEMINI_TEMPERATURE | No | 0.3 | Response creativity (0 to 1) |
| LOG_LEVEL | No | INFO | Logging verbosity |

---

## Agents that require a Gemini API key

- Symptom Checker
- Medical Report Summarizer
- Hospital Information AI Chat

The Appointment Scheduling and Prescription Reminder agents work fully without an API key.

---

## Medical Disclaimer

This application provides AI-generated information for educational purposes only.
It is not a substitute for professional medical advice, diagnosis, or treatment.
Always consult a qualified healthcare professional.
