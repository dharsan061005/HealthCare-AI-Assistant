"""
Full project validation script.
Run with: python validate_project.py
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

errors   = []
warnings = []

def ok(msg):   print(f"  OK   {msg}")
def err(label, e): print(f"  ERR  {label}: {e}"); errors.append((label, str(e)))
def warn(msg): print(f"  WARN {msg}"); warnings.append(msg)

print("=" * 55)
print("  Healthcare AI Assistant — Full Validation")
print("=" * 55)

BASE = os.path.dirname(os.path.abspath(__file__))

# ── 1. Config ─────────────────────────────────────────────
print("\n[1] config.py")
try:
    import config
    ok(f"GROQ_MODEL         = {config.GROQ_MODEL}")
    ok(f"GROQ_MAX_TOKENS    = {config.GROQ_MAX_TOKENS}")
    ok(f"GROQ_TEMPERATURE   = {config.GROQ_TEMPERATURE}")
    if config.GROQ_API_KEY:
        ok("GROQ_API_KEY is set")
    else:
        warn("GROQ_API_KEY is NOT set — LLM features will show fallback messages")
    if hasattr(config, "GEMINI_API_KEY"):
        err("config", "GEMINI_API_KEY still present — migration incomplete")
    else:
        ok("No GEMINI_* attributes (clean)")
    if hasattr(config, "OPENAI_API_KEY"):
        err("config", "OPENAI_API_KEY still present — should be removed")
    else:
        ok("No OPENAI_* attributes (clean)")
except Exception as e:
    err("config", e)

# ── 2. Dependencies ───────────────────────────────────────
print("\n[2] Python packages")

# Must be present
must_have = {
    "streamlit":    "streamlit",
    "groq":         "groq",
    "pdfplumber":   "pdfplumber",
    "pandas":       "pandas",
    "dotenv":       "python-dotenv",
}
for import_name, pkg_label in must_have.items():
    try:
        mod = __import__(import_name)
        ver = getattr(mod, "__version__", "unknown")
        ok(f"{pkg_label} ({ver})")
    except ImportError as e:
        err(pkg_label, e)

# Must NOT be present
must_not_have = {"openai": "openai", "google.generativeai": "google-generativeai"}
for import_name, pkg_label in must_not_have.items():
    try:
        __import__(import_name)
        err(pkg_label, f"{pkg_label} is still installed — should be removed")
    except ImportError:
        ok(f"{pkg_label} NOT installed (correct)")

# ── 3. Database ───────────────────────────────────────────
print("\n[3] Database")
try:
    from database.database import (
        init_db, get_all_doctors, create_appointment,
        get_appointments, create_reminder, get_reminders,
        check_duplicate_appointment,
    )
    init_db()
    doctors = get_all_doctors()
    ok(f"init_db() succeeded — {len(doctors)} doctors seeded")

    apt_id = create_appointment(
        "Validation Test", "Dr. Suresh Patel",
        "General Medicine", "2027-12-01", "10:00", "smoke test",
    )
    apts = get_appointments(patient_name="Validation Test")
    assert len(apts) >= 1
    ok(f"Appointment CRUD works (ID={apt_id})")

    dup = check_duplicate_appointment("Dr. Suresh Patel", "2027-12-01", "10:00")
    assert dup is True
    ok("Duplicate detection works")

    rid = create_reminder("TestMed", "1 tab", "08:00", "Once daily", "Test Patient")
    rems = get_reminders(patient_name="Test Patient")
    assert len(rems) >= 1
    ok(f"Reminder CRUD works (ID={rid})")
except Exception as e:
    err("database", e)

# ── 4. Utils ──────────────────────────────────────────────
print("\n[4] Utils")
for mod in ["utils.constants", "utils.validators", "utils.helpers", "utils.pdf_reader", "utils.llm"]:
    try:
        __import__(mod)
        ok(mod)
    except Exception as e:
        err(mod, e)

try:
    import utils.llm as llm_mod, inspect
    src = inspect.getsource(llm_mod)
    if "from openai" in src or "import openai" in src:
        err("utils.llm", "Still contains openai import!")
    else:
        ok("utils.llm — no openai imports (clean)")
    if "google.generativeai" in src:
        err("utils.llm", "Still contains google.generativeai import!")
    else:
        ok("utils.llm — no google.generativeai imports (clean)")
    if "from groq" in src or "groq" in src.lower():
        ok("utils.llm — uses Groq SDK (correct)")
    else:
        err("utils.llm", "Groq SDK not found in source")
except Exception as e:
    err("utils.llm source check", e)

# ── 5. Agents ─────────────────────────────────────────────
print("\n[5] Agents")
for mod in [
    "agents.router",
    "agents.appointment_agent",
    "agents.symptom_checker_agent",
    "agents.report_summarizer_agent",
    "agents.prescription_reminder_agent",
    "agents.hospital_information_agent",
]:
    try:
        __import__(mod)
        ok(mod)
    except Exception as e:
        err(mod, e)

try:
    from agents.router import NAV_ITEMS, get_agent_renderer
    assert len(NAV_ITEMS) == 5, f"Expected 5 nav items, got {len(NAV_ITEMS)}"
    for page in NAV_ITEMS:
        fn = get_agent_renderer(page)
        assert callable(fn)
    ok(f"router — all {len(NAV_ITEMS)} agents resolve correctly")
except Exception as e:
    err("router completeness", e)

# ── 6. Data JSON files ────────────────────────────────────
print("\n[6] Data files")
for fname in ["doctors.json", "departments.json", "hospital_info.json"]:
    path = os.path.join(BASE, "data", fname)
    try:
        with open(path, encoding="utf-8") as f:
            json.load(f)
        ok(f"data/{fname} — valid JSON")
    except Exception as e:
        err(f"data/{fname}", e)

# ── 7. .env file ──────────────────────────────────────────
print("\n[7] .env file")
env_path = os.path.join(BASE, ".env")
try:
    if os.path.exists(env_path):
        with open(env_path) as f:
            env_content = f.read()
        if "GROQ_API_KEY" in env_content:
            ok(".env has GROQ_API_KEY")
        else:
            warn(".env exists but GROQ_API_KEY not found")
        if "GEMINI_API_KEY" in env_content:
            warn(".env still has GEMINI_API_KEY — should be removed")
        else:
            ok(".env — no GEMINI_API_KEY (clean)")
        if "OPENAI_API_KEY" in env_content:
            warn(".env still has OPENAI_API_KEY — should be removed")
        else:
            ok(".env — no OPENAI_API_KEY (clean)")
    else:
        warn(".env file does not exist — copy from .env.example and add your key")
except Exception as e:
    err(".env", e)

# ── 8. requirements.txt ───────────────────────────────────
print("\n[8] requirements.txt")
req_path = os.path.join(BASE, "requirements.txt")
try:
    with open(req_path) as f:
        txt = f.read().lower()
    checks = [
        ("groq",             "in",     "groq missing"),
        ("streamlit",        "in",     "streamlit missing"),
        ("pdfplumber",       "in",     "pdfplumber missing"),
        ("pandas",           "in",     "pandas missing"),
        ("python-dotenv",    "in",     "python-dotenv missing"),
        ("openai",           "not in", "openai should not be present"),
        ("google-generativeai", "not in", "google-generativeai should not be present"),
    ]
    for pkg, op, msg in checks:
        if op == "in":
            assert pkg in txt, msg
        else:
            assert pkg not in txt, msg
    ok("requirements.txt — correct packages, no legacy deps")
except Exception as e:
    err("requirements.txt", e)

# ── 9. Stale file check ───────────────────────────────────
print("\n[9] Stale files")
stale = ["apply_indexes.py"]
for fname in stale:
    path = os.path.join(BASE, fname)
    if os.path.exists(path):
        warn(f"{fname} still present — can be deleted")
    else:
        ok(f"{fname} not present (clean)")

# ── Summary ───────────────────────────────────────────────
print("\n" + "=" * 55)
print(f"  Errors:   {len(errors)}")
print(f"  Warnings: {len(warnings)}")
if errors:
    print("\n  ERRORS FOUND:")
    for label, msg in errors:
        print(f"    [{label}] {msg}")
if not errors:
    print("\n  ALL CHECKS PASSED")
    print("  Run the app with:")
    print('    cd "c:\\Dharsan\\Health_AI_Assistant\\Healthcare_AI_Assistant"')
    print("    streamlit run app.py")
print("=" * 55)
