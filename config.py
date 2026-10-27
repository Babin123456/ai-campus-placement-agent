import os
from pathlib import Path
from dotenv import load_dotenv

# Project version
__version__ = "1.0.0"

# Load env variables from .env
load_dotenv()

# Base project directory
BASE_DIR = Path(__file__).resolve().parent

# Directory configurations
UPLOAD_FOLDER = BASE_DIR / "uploads"
REPORT_FOLDER = BASE_DIR / "reports"
DATABASE_PATH = BASE_DIR / "placement_agent.db"

# Ensure folders exist
UPLOAD_FOLDER.mkdir(exist_ok=True)
REPORT_FOLDER.mkdir(exist_ok=True)

# API & Security Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-12345")

# Centralized model setting (to support easy future upgrades)
GEMINI_MODEL = "gemini-2.5-flash"

# Upload file size limit (16MB)
MAX_CONTENT_LENGTH = 16 * 1024 * 1024
