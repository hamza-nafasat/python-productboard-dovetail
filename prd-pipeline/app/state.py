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
        "selected_dovetail_insight_ids": [],
        "dovetail_insights": [],  # insights for selected projects only (cached after Load insights)
        "selected_productboard_ids": [],  # features or notes IDs
        "filters": {"tags": [], "date_from": "", "date_to": "", "priority": ""},
        "dovetail_projects": [],
        "productboard_items": {},  # dict: {"features": [...], "notes": [...]}
        "data_sources_loaded": False,
        # Context Selection (Step 2): normalized data + selections
        "context_data": None,  # { dovetail: { projects: [...] }, productboard: { products: [...] } }
        "selected_productboard_product_ids": [],  # product IDs for PRD prompt
        "generated_prd_prompt_text": "",  # Claude-style prompt from Step 2
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
        "generation_prompt_config_snapshot": None,  # prompt config used for current run (persists on step 4 when widget keys are not rendered)
        "pipeline_run_id": None,
        # Theme
        "dark_mode": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Optional: prefill API config from Streamlit Cloud secrets if present.
    # This keeps keys in Streamlit secrets and avoids retyping them on each session.
    # If no secrets file exists (StreamlitSecretNotFoundError), skip prefilling.
    try:
        secrets = st.secrets  # type: ignore[attr-defined]
        if secrets:
            api_cfg = st.session_state.get("api_config", {})
            if not api_cfg.get("dovetail_key") and "DOVETAIL_API_KEY" in secrets:
                api_cfg["dovetail_key"] = str(secrets.get("DOVETAIL_API_KEY") or "")
            if not api_cfg.get("productboard_key") and "PRODUCTBOARD_API_KEY" in secrets:
                api_cfg["productboard_key"] = str(secrets.get("PRODUCTBOARD_API_KEY") or "")
            st.session_state.api_config = api_cfg
    except Exception:
        # No secrets file, or StreamlitSecretNotFoundError: run without prefilled keys
        pass


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
