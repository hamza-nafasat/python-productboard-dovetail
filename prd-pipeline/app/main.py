"""
Entry point for the PRD Generation Pipeline.
Run: streamlit run app/main.py
"""
import logging
import sys
from pathlib import Path

import streamlit as st

# Add project root to path (prd-pipeline directory)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import LOGS_DIR, STEP_NAMES, TOTAL_STEPS
from app.state import init_session_state
from ui.sidebar import render_sidebar
from ui.theme import apply_theme

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS_DIR / "app.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("prd_pipeline")

# Page config (must be first Streamlit command)
st.set_page_config(
    page_title="PRD Generation Pipeline",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load env for optional prefilled keys (session state overrides)
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

# Session state
init_session_state()

# Theme from session state
apply_theme()

# Sidebar: step navigation and progress
render_sidebar()

# Main: render current step
step = st.session_state.get("step", 1)
step = max(1, min(step, TOTAL_STEPS))
st.session_state.step = step

# Dynamic page dispatch
try:
    if step == 1:
        from pages.step_setup import render_step_setup
        render_step_setup()
    elif step == 2:
        from pages.step_data_sources import render_step_data_sources
        render_step_data_sources()
    elif step == 3:
        from pages.step_prompt_config import render_step_prompt_config
        render_step_prompt_config()
    elif step == 4:
        from pages.step_generation import render_step_generation
        render_step_generation()
    elif step == 5:
        from pages.step_review import render_step_review
        render_step_review()
    elif step == 6:
        from pages.step_publish import render_step_publish
        render_step_publish()
    else:
        from pages.step_history import render_step_history
        render_step_history()
except Exception as e:
    logger.exception("Page error: %s", e)
    st.error("Something went wrong. Please try again or go back to Setup.")
    if st.button("Go to Setup"):
        st.session_state.step = 1
        st.rerun()
