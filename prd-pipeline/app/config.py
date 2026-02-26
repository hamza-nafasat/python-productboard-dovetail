"""App constants and theme configuration."""
import os
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
TEMPLATES_DIR = PROJECT_ROOT / "templates" / "prd_templates"
HISTORY_FILE = DATA_DIR / "prd_history.json"

# Ensure dirs exist (created on first use in history.py)
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

# Wizard
TOTAL_STEPS = 6
STEP_NAMES = [
    "Setup",
    "Data Sources",
    "Prompt Config",
    "Generate PRD prompt",
    "PRD Review",
    "Publish to Confluence",
]

# API defaults (timeouts, retries)
HTTP_TIMEOUT = 30.0
HTTP_MAX_RETRIES = 2

# Theme keys for session state
THEME_KEY = "dark_mode"  # True = dark, False = light
