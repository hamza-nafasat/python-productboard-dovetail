"""Session state schema and helpers. All keys live in st.session_state."""
from __future__ import annotations

from typing import Any

import streamlit as st

from app.config import TOTAL_STEPS


def init_session_state() -> None:
    """Initialize all session state keys with defaults. Call once at app start."""
    defaults: dict[str, Any] = {
        # API config (user input)
        "api_config": {
            "dovetail_key": "",
            "productboard_key": "",
            "confluence_key": "",
            "confluence_base_url": "",
            "confluence_space": "",
        },
        # Connection test results: { "dovetail": True, "productboard": False, ... }
        "connection_status": {},
        # Last error message per service
        "connection_errors": {},
        # Wizard
        "step": 1,
        "step_visited": set(),  # type: ignore[typeddict-unknown-key]
        # Data sources
        "selected_dovetail_project_ids": [],
        "selected_productboard_ids": [],  # features or notes IDs
        "filters": {"tags": [], "date_from": "", "date_to": "", "priority": ""},
        "dovetail_projects": [],
        "productboard_items": {},  # dict: {"features": [...], "notes": [...]}
        "data_sources_loaded": False,
        # Prompt config
        "prd_template_id": "default",
        "product_context": "",
        "business_goals": "",
        "constraints": "",
        "audience_type": "internal_stakeholders",
        "output_tone": "professional",
        "include_roadmap": True,
        # Generation (prompt only; PRD comes from user's AI tool)
        "generation_logs": [],
        "generation_error": None,
        "generation_running": False,
        "generated_prompt": "",
        "generated_prompt_metadata": {},
        "current_prd_text": "",
        "current_prd_version": 1,
        "pipeline_run_id": None,
        "prd_versions": [],  # list of {"version": int, "text": str} for comparison
        # Publish
        "confluence_parent_page_id": "",
        "confluence_page_title": "",
        # Theme
        "dark_mode": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_api_config() -> dict[str, str]:
    """Return current API config from session state."""
    return st.session_state.get("api_config", {})


def set_step(step: int) -> None:
    """Set current wizard step (1-based)."""
    if 1 <= step <= TOTAL_STEPS:
        st.session_state.step = step
        st.session_state.setdefault("step_visited", set()).add(step)


def next_step() -> None:
    """Advance to next step if possible."""
    if st.session_state.get("step", 1) < TOTAL_STEPS:
        st.session_state.step += 1
        st.session_state.setdefault("step_visited", set()).add(st.session_state.step)


def prev_step() -> None:
    """Go back one step."""
    if st.session_state.get("step", 1) > 1:
        st.session_state.step -= 1
