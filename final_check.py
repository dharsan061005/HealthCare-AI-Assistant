"""
Final validation — tests config from multiple import scenarios.
python final_check.py
"""
import sys, os

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

PASS = []
FAIL = []

def check(label, fn):
    try:
        fn()
        print(f"  PASS  {label}")
        PASS.append(label)
    except Exception as e:
        print(f"  FAIL  {label}: {e}")
        FAIL.append((label, str(e)))

print("=" * 52)
print("  Final Validation")
print("=" * 52)

# ── Config attributes ─────────────────────────────────────
print("\n[config.py]")

def check_config_attrs():
    import config
    assert hasattr(config, "GROQ_API_KEY"),    "Missing GROQ_API_KEY"
    assert hasattr(config, "GROQ_MODEL"),       "Missing GROQ_MODEL"
    assert hasattr(config, "GROQ_MAX_TOKENS"),  "Missing GROQ_MAX_TOKENS"
    assert hasattr(config, "GROQ_TEMPERATURE"), "Missing GROQ_TEMPERATURE"
    assert not hasattr(config, "GEMINI_API_KEY"),  "GEMINI_API_KEY still present"
    assert not hasattr(config, "OPENAI_API_KEY"),  "OPENAI_API_KEY still present"

check("config attributes (GROQ_* present, old keys absent)", check_config_attrs)

def check_config_dotenv():
    import config
    assert isinstance(config.GROQ_API_KEY, str), "GROQ_API_KEY not a string"
    assert config.GROQ_MODEL == "llama-3.3-70b-versatile", f"Model wrong: {config.GROQ_MODEL}"

check("config dotenv loaded + correct model", check_config_dotenv)

# ── LLM module ────────────────────────────────────────────
print("\n[utils/llm.py]")

def check_llm_no_legacy():
    import inspect, utils.llm as llm
    src = inspect.getsource(llm)
    assert "import openai"           not in src, "openai import found"
    assert "from openai"             not in src, "openai import found"
    assert "google.generativeai"     not in src, "google.generativeai import found"
    assert "GenerativeModel"         not in src, "GenerativeModel found"

check("no OpenAI / Gemini code in llm.py", check_llm_no_legacy)

def check_llm_uses_groq():
    import inspect, utils.llm as llm
    src = inspect.getsource(llm)
    assert "from groq import Groq" in src or "groq" in src.lower(), "Groq not used"
    assert "chat.completions.create" in src, "chat.completions.create not found"

check("llm.py uses Groq SDK", check_llm_uses_groq)

def check_llm_functions():
    from utils.llm import chat_completion, simple_query
    assert callable(chat_completion)
    assert callable(simple_query)

check("chat_completion and simple_query callable", check_llm_functions)

# ── app.py ────────────────────────────────────────────────
print("\n[app.py]")

def check_app_no_legacy():
    with open(os.path.join(ROOT, "app.py")) as f:
        src = f.read()
    assert "OPENAI_API_KEY"  not in src, "OPENAI_API_KEY in app.py"
    assert "GEMINI_API_KEY"  not in src, "GEMINI_API_KEY in app.py"
    assert "GROQ_API_KEY"    in src,     "GROQ_API_KEY missing from app.py"

check("app.py uses GROQ_API_KEY only", check_app_no_legacy)

def check_app_sys_path():
    with open(os.path.join(ROOT, "app.py")) as f:
        src = f.read()
    assert "sys.path.insert" in src, "sys.path.insert missing"
    assert "ROOT_DIR" in src or "os.chdir" in src

check("app.py sets sys.path and cwd before imports", check_app_sys_path)

# ── requirements.txt ──────────────────────────────────────
print("\n[requirements.txt]")

def check_requirements():
    with open(os.path.join(ROOT, "requirements.txt")) as f:
        txt = f.read().lower()
    assert "openai"              not in txt, "openai still in requirements.txt"
    assert "google-generativeai" not in txt, "google-generativeai still in requirements.txt"
    assert "groq"                    in txt, "groq missing from requirements.txt"
    assert "streamlit"               in txt
    assert "pdfplumber"              in txt
    assert "pandas"                  in txt
    assert "python-dotenv"           in txt

check("requirements.txt correct (groq, no openai/gemini)", check_requirements)

# ── Installed packages ────────────────────────────────────
print("\n[installed packages]")

def check_no_legacy_installed():
    for pkg in ["openai", "google.generativeai"]:
        try:
            __import__(pkg)
            raise AssertionError(f"{pkg} is installed — should be removed")
        except ImportError:
            pass

check("openai / google-generativeai NOT installed", check_no_legacy_installed)

def check_groq_installed():
    from groq import Groq
    assert Groq is not None

check("groq package installed", check_groq_installed)

# ── All 5 agents ──────────────────────────────────────────
print("\n[agents]")

agent_modules = [
    "agents.router",
    "agents.appointment_agent",
    "agents.symptom_checker_agent",
    "agents.report_summarizer_agent",
    "agents.prescription_reminder_agent",
    "agents.hospital_information_agent",
]
for mod in agent_modules:
    check(mod, lambda m=mod: __import__(m))

def check_router_complete():
    from agents.router import NAV_ITEMS, get_agent_renderer
    assert len(NAV_ITEMS) == 5, f"Expected 5 nav items, got {len(NAV_ITEMS)}"
    for page in NAV_ITEMS:
        fn = get_agent_renderer(page)
        assert callable(fn)

check("router resolves all 5 agents", check_router_complete)

# ── Database ──────────────────────────────────────────────
print("\n[database]")

def check_db():
    from database.database import init_db, get_all_doctors
    init_db()
    docs = get_all_doctors()
    assert len(docs) > 0, "No doctors seeded"

check("database init + doctor seed", check_db)

# ── Data JSON files ───────────────────────────────────────
print("\n[data files]")

import json
for fname in ["doctors.json", "departments.json", "hospital_info.json"]:
    path = os.path.join(ROOT, "data", fname)
    check(f"data/{fname}", lambda p=path: json.load(open(p, encoding="utf-8")))

# ── .env file ─────────────────────────────────────────────
print("\n[.env]")

def check_env_file():
    env_path = os.path.join(ROOT, ".env")
    assert os.path.exists(env_path), ".env file missing"
    with open(env_path) as f:
        content = f.read()
    assert "GROQ_API_KEY"   in content, "GROQ_API_KEY not in .env"
    assert "GEMINI_API_KEY" not in content, "GEMINI_API_KEY still in .env"
    assert "OPENAI_API_KEY" not in content, "OPENAI_API_KEY still in .env"

check(".env has GROQ_API_KEY only", check_env_file)

# ── Summary ───────────────────────────────────────────────
print("\n" + "=" * 52)
print(f"  Passed: {len(PASS)}")
print(f"  Failed: {len(FAIL)}")
if FAIL:
    print("\n  FAILURES:")
    for label, msg in FAIL:
        print(f"    [{label}]")
        print(f"      {msg}")
else:
    print("\n  ALL CHECKS PASSED")
    print("\n  To run the app:")
    print('    cd "c:\\Dharsan\\Health_AI_Assistant\\Healthcare_AI_Assistant"')
    print("    streamlit run app.py")
print("=" * 52)
