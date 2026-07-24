# Healthcare AI Assistant 🏥🤖

An advanced, privacy-first healthcare management platform powered by Artificial Intelligence (Google Gemini & Groq). This assistant offers dynamic appointment scheduling, multi-family health tracking, AI-driven medical report analysis, symptom tracking, and sophisticated prescription reminders, all embedded in a beautiful and responsive Streamlit interface.

## Project Overview

The Healthcare AI Assistant digitizes personal and family medical management. It securely persists patient demographics and clinical histories across an offline-capable SQLite layer, while enabling LLM-powered diagnostics to explain complex medical reports and offer real-time health recommendations.

## Features

- **Dynamic Appointment Scheduling:** Complete workflows to book, reschedule, and cancel appointments with automated duplicate detection based on hospital, doctor, date, and time.
- **Family Management:** Comprehensive dashboards to manage "My Family". Features dynamic forms for inputting extensive medical fields (Height, Weight, BMI, Allergies, Blood Group).
- **Electronic Health Records (EHR):** Track vitals, medical history, vaccinations, and generate exportable PDF reports.
- **Medication Reminders:** Schedule and visualize active prescriptions, log missed medicines, and configure notification alerts.
- **Symptom Tracker & Emergency Connect:** Keep a rolling log of symptoms and configure prioritized emergency contacts.

## AI Features (Gemini & Groq)

- **AI Report Summarizer:** Upload raw medical and lab reports (PDF/TXT) and let the Gemini/Groq LLM extract key takeaways, highlight anomalies, and present actionable next steps in plain English.
- **Ask AI:** A customized, context-aware chatbot capable of understanding your family's specific medical conditions and history to provide accurate, safe health guidance.
- **Smart Recommendations:** Auto-generated wellness checklists uniquely tailored to the saved biometric parameters of patients.

## Screenshots

*(Coming Soon - Please add your application screenshots here to showcase the beautiful UI!)*

## Installation Guide

Ensure you have Python 3.9+ installed on your system. 

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/Healthcare-AI-Assistant.git
   cd Healthcare-AI-Assistant
   ```
2. **Set up a Virtual Environment:**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux/MacOS
   source .venv/bin/activate
   ```
3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Environment Variables

This project requires API keys to fuel the AI engine. Create a `.env` file at the root of the project with the following configuration:

```env
# Required for primary AI features
GEMINI_API_KEY=your_google_gemini_api_key_here

# Required for secondary fallback LLM features
GROQ_API_KEY=your_groq_api_key_here
```
> **Security Note:** Never commit your `.env` file! It is safely ignored via our `.gitignore`.

## Project Structure

```
Healthcare-AI-Assistant/
├── agents/             # Core UI components and routed Streamlit pages 
├── database/           # SQLite logic, migration scripts, and family / healthcare schemas
├── tests/              # Pytest battery (agents, DB, deletions)
├── utils/              # PDF extraction, styling constants, data validation, and LLM wrappers
├── app.py              # Main Streamlit execution entry point
├── config.py           # DotEnv variable instantiator
├── requirements.txt    # Project dependencies
└── README.md           # Documentation
```

## Technologies Used

- **Frontend / Application Framework:** [Streamlit](https://streamlit.io/)
- **Database:** SQLite3 (Serverless)
- **AI / LLMs:** Google Generative AI (Gemini), Groq
- **Data Manipulation:** Pandas
- **PDF Extraction:** PDFPlumber, FPDF2
- **Testing:** Pytest

## How to Run

Launch the application safely by executing:
```bash
streamlit run app.py
```
The interface will be hosted immediately at `http://localhost:8501`.

## Deployment Guide

If deploying to a production server (like Streamlit Community Cloud, Heroku, or AWS):
1. Push this repository to GitHub.
2. Link the repository to your hosting provider.
3. Inject the `GEMINI_API_KEY` and `GROQ_API_KEY` into your host's environment secrets interface.
4. Set the startup command to `streamlit run app.py`.

## Future Enhancements

- Integrate Twilio / SMTP for actual outbound SMS and Email reminders.
- Build interactive graphs (Plotly) for longitudinal vital signs (Blood Pressure & Glucose).
- Enable multi-lingual localization support using dynamic translation files.

## Author
*Created and Maintained by the Healthcare AI Assistant Team / Dharsan.*

## License
MIT License.
