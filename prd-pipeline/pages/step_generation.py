"""Step 4: PRD generation - run pipeline, show progress and logs."""
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import streamlit as st

from app.state import get_api_config, next_step
from core.models import APIConfig, PromptConfig
from core.prd_generator import run_pipeline
from services import history

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=1)

# Thread-safe: worker writes, main thread reads on rerun
_generation_logs: list[str] = []
_generation_error: list[str] = []
_generation_done: list[bool] = [False]
_generation_result: list[str] = [""]
_generation_run_id: list[str] = [""]
_generation_meta: dict[str, Any] = {}  # for history entry, written by worker


def _log_cb(msg: str) -> None:
    _generation_logs.append(msg)


def _run(payload: dict[str, Any]) -> None:
    """Run pipeline in thread. Do not touch st.session_state."""
    global _generation_logs, _generation_error, _generation_done, _generation_result, _generation_run_id, _generation_meta
    _generation_logs.clear()
    _generation_error.clear()
    _generation_done.clear()
    _generation_done.append(False)
    _generation_result.clear()
    _generation_result.append("")
    _generation_run_id.clear()
    _generation_run_id.append("")
    _generation_meta.clear()
    try:
        api_config = APIConfig.from_session_dict(payload["api_config"])
        prompt_config = PromptConfig(
            prd_template_id=payload.get("prd_template_id", "default"),
            product_context=payload.get("product_context", ""),
            business_goals=payload.get("business_goals", ""),
            constraints=payload.get("constraints", ""),
            audience_type=payload.get("audience_type", "internal_stakeholders"),
            output_tone=payload.get("output_tone", "professional"),
            include_roadmap=payload.get("include_roadmap", True),
        )
        prd_text, err, run_id = run_pipeline(
            api_config=api_config,
            prompt_config=prompt_config,
            selected_dovetail_project_ids=payload.get("selected_dovetail_project_ids", []),
            selected_productboard_ids=payload.get("selected_productboard_ids", []),
            log_callback=_log_cb,
        )
        _generation_done.append(True)
        _generation_run_id.append(run_id)
        if err:
            _generation_error.append(err)
        else:
            _generation_result.append(prd_text)
            title = (prd_text.split("\n")[0] or "PRD").replace("#", "").strip()
            _generation_meta.update({
                "title": title[:200],
                "content": prd_text,
                "version": payload.get("current_prd_version", 1),
                "run_id": run_id,
                "selected_dovetail_ids": payload.get("selected_dovetail_project_ids", []),
                "selected_productboard_ids": payload.get("selected_productboard_ids", []),
                "prompt_config_snapshot": {
                    "prd_template_id": prompt_config.prd_template_id,
                    "audience_type": prompt_config.audience_type,
                    "output_tone": prompt_config.output_tone,
                },
            })
            history.add_entry(
                title=_generation_meta["title"],
                content=prd_text,
                version=_generation_meta["version"],
                pipeline_run_id=run_id,
                selected_dovetail_ids=_generation_meta["selected_dovetail_ids"],
                selected_productboard_ids=_generation_meta["selected_productboard_ids"],
                prompt_config_snapshot=_generation_meta["prompt_config_snapshot"],
            )
    except Exception as e:
        logger.exception("Pipeline failed: %s", e)
        _generation_error.append(str(e))
        _generation_done.append(True)


def render_step_generation() -> None:
    st.header("Step 4: PRD Generation")
    st.caption("Run the pipeline to generate the PRD from your data and prompt config.")

    # Sync session state from worker
    if _generation_logs:
        st.session_state.generation_logs = list(_generation_logs)
    if _generation_error:
        st.session_state.generation_error = _generation_error[-1]
    if _generation_done and _generation_result:
        st.session_state.current_prd_text = _generation_result[-1]

    logs = st.session_state.get("generation_logs", [])
    err = st.session_state.get("generation_error")
    running = st.session_state.get("generation_running", False)
    has_result = bool(st.session_state.get("current_prd_text"))

    if st.button("Generate PRD", type="primary", key="gen_btn", disabled=running):
        payload = {
            "api_config": get_api_config(),
            "prd_template_id": st.session_state.get("prd_template_id", "default"),
            "product_context": st.session_state.get("product_context", ""),
            "business_goals": st.session_state.get("business_goals", ""),
            "constraints": st.session_state.get("constraints", ""),
            "audience_type": st.session_state.get("audience_type", "internal_stakeholders"),
            "output_tone": st.session_state.get("output_tone", "professional"),
            "include_roadmap": st.session_state.get("include_roadmap", True),
            "selected_dovetail_project_ids": st.session_state.get("selected_dovetail_project_ids", []),
            "selected_productboard_ids": st.session_state.get("selected_productboard_ids", []),
            "current_prd_version": st.session_state.get("current_prd_version", 1),
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
        _executor.submit(_run, payload)
        st.rerun()

    if running:
        st.info("Generation in progress. Click 'Refresh status' to update.")
        if st.button("Refresh status", key="refresh_gen"):
            if _generation_logs:
                st.session_state.generation_logs = list(_generation_logs)
            if _generation_error:
                st.session_state.generation_error = _generation_error[-1]
                st.session_state.generation_running = False
            if _generation_done and len(_generation_done) > 0 and _generation_done[-1]:
                st.session_state.generation_running = False
                if _generation_result:
                    st.session_state.current_prd_text = _generation_result[-1]
                if _generation_run_id:
                    st.session_state.pipeline_run_id = _generation_run_id[-1]
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
        st.success("PRD generated. Go to Step 5 to review and edit.")
        st.divider()
        if st.button("Next: PRD Review →", type="primary"):
            next_step()
            st.rerun()
