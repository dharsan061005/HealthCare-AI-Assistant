"""
Central configuration for Healthcare AI Assistant
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Project directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

# ==========================
# Groq Configuration
# ==========================
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "2048"))
GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0.4"))

# ==========================
# Gemini Configuration
# ==========================
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL    = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Active AI provider: "gemini" or "groq" (falls back to groq if key missing)
AI_PROVIDER = os.getenv("AI_PROVIDER", "groq").lower()

# ==========================
# App Configuration
# ==========================
APP_TITLE = "Healthcare AI Assistant"
APP_ICON = "\U0001f3e5"   # 🏥
APP_VERSION = "1.0.0"

# ==========================
# Paths
# ==========================
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
DATABASE_DIR = BASE_DIR / "database"

# ==========================
# Logging
# ==========================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
