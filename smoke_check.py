"""Quick smoke check — run with: python smoke_check.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
assert hasattr(config, "GROQ_API_KEY"), "GROQ_API_KEY missing from config"
assert hasattr(config, "GROQ_MODEL"),   "GROQ_MODEL missing from config"
print(f"config OK  (model={config.GROQ_MODEL}, tokens={config.GROQ_MAX_TOKENS})")

from database.database import init_db, get_all_doctors
init_db()
doctors = get_all_doctors()
print(f"database OK  — {len(doctors)} doctors seeded")

from agents.router import NAV_ITEMS, get_agent_renderer
assert len(NAV_ITEMS) == 5, f"Expected 5 nav items, got {len(NAV_ITEMS)}"
print(f"router OK  — {len(NAV_ITEMS)} agents registered")
for name in NAV_ITEMS:
    fn = get_agent_renderer(name)
    assert callable(fn)
    print(f"  {name}")

from utils.llm import chat_completion, simple_query
assert callable(chat_completion) and callable(simple_query)
print("llm OK  (Groq SDK)")

from utils.pdf_reader import extract_text_from_pdf
print("pdf_reader OK")

from utils.validators import validate_patient_name, validate_symptoms_input
ok, _ = validate_patient_name("Ravi Kumar")
assert ok
ok, _ = validate_symptoms_input("headache and fever for 2 days")
assert ok
print("validators OK")

from utils.helpers import format_date, format_time_12h, appointments_to_display_rows
assert format_date("2027-01-15") == "15 Jan 2027"
assert format_time_12h("14:30") == "02:30 PM"
print("helpers OK")

from utils.constants import TIME_SLOTS, FREQUENCY_OPTIONS, SPECIALIZATIONS
print(f"constants OK  — {len(TIME_SLOTS)} time slots, {len(SPECIALIZATIONS)} specializations")

# Groq SDK present, no legacy packages
from groq import Groq
assert Groq is not None
print("groq SDK OK")

for legacy in ["openai", "google.generativeai"]:
    try:
        __import__(legacy)
        print(f"WARNING: {legacy} is still installed (should be removed)")
    except ImportError:
        print(f"legacy check OK  — {legacy} not installed")

print()
print("=" * 45)
print("  All smoke checks passed. Ready to run:")
print("    streamlit run app.py")
print("=" * 45)
