"""Step 3: Generate PRD prompt - run pipeline, show prompt with copy and edit."""
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import streamlit as st

from app.state import get_api_config
from core.models import APIConfig, PromptConfig
from core.prd_generator import build_prompt_from_context, run_pipeline

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=1)

# Thread-safe: worker writes, main thread reads on rerun
_generation_logs: list[str] = []
_generation_error: list[str] = []
_generation_done: list[bool] = [False]
_generation_result: list[str] = [""]
_generation_run_id: list[str] = [""]
_generation_metadata: list[dict[str, Any]] = [{}]


def _log_cb(msg: str) -> None:
    _generation_logs.append(msg)


def _run(payload: dict[str, Any]) -> None:
    """Run pipeline in thread. Do not touch st.session_state."""
    global _generation_logs, _generation_error, _generation_done, _generation_result, _generation_run_id, _generation_metadata
    _generation_logs.clear()
    _generation_error.clear()
    _generation_done.clear()
    _generation_done.append(False)
    _generation_result.clear()
    _generation_result.append("")
    _generation_run_id.clear()
    _generation_run_id.append("")
    _generation_metadata.clear()
    _generation_metadata.append({})
    try:
        prompt_config = PromptConfig(
            prd_template_id=payload.get("prd_template_id", "default"),
            product_context=payload.get("product_context", ""),
            business_goals=payload.get("business_goals", ""),
            constraints=payload.get("constraints", ""),
            audience_type=payload.get("audience_type", "internal_stakeholders"),
            output_tone=payload.get("output_tone", "professional"),
            include_roadmap=payload.get("include_roadmap", True),
        )
        context_data = payload.get("context_data")
        if context_data:
            prompt_text, err, run_id, metadata = build_prompt_from_context(
                context_data=context_data,
                selected_dovetail_insight_ids=payload.get("selected_dovetail_insight_ids", []),
                selected_productboard_product_ids=payload.get("selected_productboard_product_ids", []),
                prompt_config=prompt_config,
                log_callback=_log_cb,
            )
        else:
            api_config = APIConfig.from_session_dict(payload["api_config"])
            prompt_text, err, run_id, metadata = run_pipeline(
                api_config=api_config,
                prompt_config=prompt_config,
                selected_dovetail_project_ids=payload.get("selected_dovetail_project_ids", []),
                selected_dovetail_insight_ids=payload.get("selected_dovetail_insight_ids", []),
                selected_productboard_ids=payload.get("selected_productboard_ids", []),
                log_callback=_log_cb,
            )
        _generation_done.append(True)
        _generation_run_id.append(run_id)
        if err:
            _generation_error.append(err)
        else:
            _generation_result.append(prompt_text)
            _generation_metadata.append(metadata or {})
    except Exception as e:
        logger.exception("Pipeline failed: %s", e)
        _generation_error.append(str(e))
        _generation_done.append(True)


def _get_prompt_config_snapshot() -> dict[str, Any]:
    """Prompt config used for this run; survives step 4 because it's not widget-bound."""
    return st.session_state.get("generation_prompt_config_snapshot") or {}


def render_step_generation() -> None:
    st.header("Step 3: Generate PRD prompt")
    st.caption(
        "Run the pipeline to build a structured prompt from your selected Dovetail insights and Productboard notes. "
        "Copy the prompt into your own AI tool to generate the PRD."
    )

    # No prompt config step: use defaults (empty context/goals/constraints, default tone & roadmap)
    snapshot = _get_prompt_config_snapshot()
    if not snapshot:
        # Build default snapshot so generation uses defaults without user config
        st.session_state.generation_prompt_config_snapshot = {
            "prd_template_id": st.session_state.get("prd_template_id", "default"),
            "product_context": st.session_state.get("product_context", ""),
            "business_goals": st.session_state.get("business_goals", ""),
            "constraints": st.session_state.get("constraints", ""),
            "audience_type": st.session_state.get("audience_type", "internal_stakeholders"),
            "output_tone": st.session_state.get("output_tone", "professional"),
            "include_roadmap": st.session_state.get("include_roadmap", True),
        }
        snapshot = _get_prompt_config_snapshot()

    product_context_display = snapshot.get("product_context", "")
    business_goals_display = snapshot.get("business_goals", "")
    constraints_display = snapshot.get("constraints", "")

    # Optional: show that we're using default prompt settings (no config step)
    with st.expander("Prompt settings (defaults)", expanded=False):
        st.caption("Prompt is built from your selected data with default settings. No custom configuration.")

    # Sync session state from worker
    if _generation_logs:
        st.session_state.generation_logs = list(_generation_logs)
    if _generation_error:
        st.session_state.generation_error = _generation_error[-1]
    if _generation_done and _generation_result:
        st.session_state.generated_prompt = _generation_result[-1]
        st.session_state.generated_prompt_metadata = _generation_metadata[-1] if _generation_metadata else {}

    logs = st.session_state.get("generation_logs", [])
    err = st.session_state.get("generation_error")
    running = st.session_state.get("generation_running", False)
    prompt_text = st.session_state.get("generated_prompt", "")
    metadata = st.session_state.get("generated_prompt_metadata", {})
    has_result = bool(prompt_text)

    if st.button("Generate PRD prompt", type="primary", key="gen_btn", disabled=running):
        # Use snapshot for prompt config when present (set when leaving step 3); on step 4
        # session state may have lost widget keys so reading from session would be empty.
        snap = _get_prompt_config_snapshot()
        if snap:
            payload = {
                "api_config": get_api_config(),
                "prd_template_id": snap.get("prd_template_id", "default"),
                "product_context": snap.get("product_context", ""),
                "business_goals": snap.get("business_goals", ""),
                "constraints": snap.get("constraints", ""),
                "audience_type": snap.get("audience_type", "internal_stakeholders"),
                "output_tone": snap.get("output_tone", "professional"),
                "include_roadmap": snap.get("include_roadmap", True),
                "context_data": st.session_state.get("context_data"),
                "selected_dovetail_project_ids": st.session_state.get("selected_dovetail_project_ids", []),
                "selected_dovetail_insight_ids": st.session_state.get("selected_dovetail_insight_ids", []),
                "selected_productboard_ids": st.session_state.get("selected_productboard_ids", []),
                "selected_productboard_product_ids": st.session_state.get("selected_productboard_product_ids", []),
            }
        else:
            payload = {
                "api_config": get_api_config(),
                "prd_template_id": st.session_state.get("prd_template_id", "default"),
                "product_context": st.session_state.get("product_context", ""),
                "business_goals": st.session_state.get("business_goals", ""),
                "constraints": st.session_state.get("constraints", ""),
                "audience_type": st.session_state.get("audience_type", "internal_stakeholders"),
                "output_tone": st.session_state.get("output_tone", "professional"),
                "include_roadmap": st.session_state.get("include_roadmap", True),
                "context_data": st.session_state.get("context_data"),
                "selected_dovetail_project_ids": st.session_state.get("selected_dovetail_project_ids", []),
                "selected_dovetail_insight_ids": st.session_state.get("selected_dovetail_insight_ids", []),
                "selected_productboard_ids": st.session_state.get("selected_productboard_ids", []),
                "selected_productboard_product_ids": st.session_state.get("selected_productboard_product_ids", []),
            }
            st.session_state.generation_prompt_config_snapshot = {
                "prd_template_id": payload.get("prd_template_id", "default"),
                "product_context": payload.get("product_context", ""),
                "business_goals": payload.get("business_goals", ""),
                "constraints": payload.get("constraints", ""),
                "audience_type": payload.get("audience_type", "internal_stakeholders"),
                "output_tone": payload.get("output_tone", "professional"),
                "include_roadmap": payload.get("include_roadmap", True),
            }
        st.session_state.generation_running = True
        st.session_state.generation_logs = []
        st.session_state.generation_error = None
        _generation_logs.clear()
        _generation_error.clear()
        _generation_done.clear()
        _generation_done.append(False)
        _generation_result.clear()
        _generation_result.append("")
        _generation_run_id.clear()
        _generation_run_id.append("")
        _generation_metadata.clear()
        _generation_metadata.append({})
        _executor.submit(_run, payload)
        st.rerun()

    if running:
        st.info("Generating prompt… Building from your selected data. Click **Refresh status** to update.")
        if st.button("Refresh status", key="refresh_gen"):
            # Restore prompt config from snapshot (session state keys can be removed when step 3 widgets aren't rendered)
            snapshot = _get_prompt_config_snapshot()
            if _generation_logs:
                st.session_state.generation_logs = list(_generation_logs)
            if _generation_error:
                st.session_state.generation_error = _generation_error[-1]
                st.session_state.generation_running = False
            if _generation_done and _generation_done[-1]:
                st.session_state.generation_running = False
                if _generation_result:
                    st.session_state.generated_prompt = _generation_result[-1]
                    st.session_state.generated_prompt_metadata = _generation_metadata[-1] if _generation_metadata else {}
                if _generation_run_id:
                    st.session_state.pipeline_run_id = _generation_run_id[-1]
            if snapshot:
                st.session_state.product_context = snapshot.get("product_context", "")
                st.session_state.business_goals = snapshot.get("business_goals", "")
                st.session_state.constraints = snapshot.get("constraints", "")
                st.session_state.prd_template_id = snapshot.get("prd_template_id", "default")
                st.session_state.audience_type = snapshot.get("audience_type", "internal_stakeholders")
                st.session_state.output_tone = snapshot.get("output_tone", "professional")
                st.session_state.include_roadmap = snapshot.get("include_roadmap", True)
            st.rerun()

    if err:
        st.error(err)
        st.session_state.generation_running = False
        if st.button("Retry", key="retry_gen"):
            st.session_state.generation_error = None
            st.rerun()

    if logs:
        with st.expander("Pipeline logs", expanded=not has_result):
            for line in logs:
                st.code(line, language=None)

    if has_result:
        st.success("Prompt ready. Edit below if needed, then copy into your AI tool.")
        # Metadata in a compact block
        strategy_id = metadata.get("strategy_id", "default")
        template_id = metadata.get("template_id", "default")
        word_count = metadata.get("word_count", 0)
        sections = metadata.get("sections", [])
        st.caption(f"Strategy: {strategy_id} · Template: {template_id} · Words: {word_count}")
        if sections:
            st.caption("Sections: " + ", ".join(sections))

        # Editable prompt: user can tweak before copying
        edited = st.text_area(
            "PRD Prompt (Editable)",
            value=prompt_text,
            height=400,
            key="generated_prompt_editor",
            help="Edit the prompt if needed, then select all (Ctrl+A) and copy (Ctrl+C) to use in your AI tool.",
        )
        if edited != prompt_text:
            st.session_state.generated_prompt = edited

        # Copy hint (Streamlit has no built-in copy-to-clipboard for arbitrary text)
        st.caption("Select all text above and copy (Ctrl+A, Ctrl+C or Cmd+A, Cmd+C) to paste into your AI tool.")

        # Download prompt as Markdown (uses current content of the text area above)
        st.download_button(
            "Download prompt as .md",
            data=edited,
            file_name="prd_prompt.md",
            mime="text/markdown",
            key="download_prompt_md_btn",
        )

        st.divider()
        if st.button("Done", type="primary"):
            st.rerun()
