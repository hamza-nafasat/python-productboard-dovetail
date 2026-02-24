"""
Orchestrates: fetch data from Dovetail/Productboard -> build prompt -> call Claude -> return PRD.
Designed to run in a thread; logs and errors are stored for the UI to read.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Callable, Optional

from core.models import APIConfig, PromptConfig
from core.prompts import build_prd_prompt

logger = logging.getLogger(__name__)


def _summarize_dovetail(projects: list[dict], insights: list[dict]) -> str:
    """Turn projects + insights into a short text summary for the prompt."""
    if not projects and not insights:
        return "No Dovetail data selected."
    lines = []
    for p in projects[:20]:
        name = p.get("name") or p.get("title") or str(p.get("id", ""))
        lines.append(f"- Project: {name}")
    for i in insights[:50]:
        body = (i.get("body") or i.get("content") or i.get("text") or "")[:500]
        title = i.get("name") or i.get("title") or "Insight"
        lines.append(f"- Insight: {title}. {body}")
    return "\n".join(lines) if lines else "No insights."


def _summarize_productboard(features: list[dict], notes: list[dict]) -> str:
    """Turn features/notes into a short text summary for the prompt."""
    if not features and not notes:
        return "No Productboard data selected."
    lines = []
    for f in features[:30]:
        name = f.get("name") or f.get("title") or str(f.get("id", ""))
        desc = (f.get("description") or "")[:300]
        lines.append(f"- Feature: {name}. {desc}")
    for n in notes[:30]:
        name = n.get("name") or n.get("title") or str(n.get("id", ""))
        content = (n.get("content") or n.get("description") or "")[:300]
        lines.append(f"- Note: {name}. {content}")
    return "\n".join(lines) if lines else "No feedback."


def run_pipeline(
    api_config: APIConfig,
    prompt_config: PromptConfig,
    selected_dovetail_project_ids: list[str],
    selected_productboard_ids: list[str],
    log_callback: Optional[Callable[[str], None]] = None,
) -> tuple[str, Optional[str], str]:
    """
    Run the full PRD generation pipeline (sync). Call from a thread.
    Returns (prd_text, error_message, run_id). If error_message is set, prd_text may be empty.
    """
    run_id = str(uuid.uuid4())[:8]
    def log(msg: str) -> None:
        logger.info("[%s] %s", run_id, msg)
        if log_callback:
            log_callback(msg)

    log("Starting pipeline.")
    try:
        from api import dovetail, productboard
        from api.anthropic_client import generate_prd
        from app.run_async import run_async
    except ImportError as e:
        err = f"Import error: {e}"
        log(err)
        return "", err, run_id

    # 1. Fetch Dovetail data
    log("Fetching Dovetail projects and insights...")
    projects = dovetail.get_projects(api_config.dovetail_key)
    projects_subset = [p for p in projects if str(p.get("id", "")) in selected_dovetail_project_ids]
    if not selected_dovetail_project_ids:
        projects_subset = projects[:5]  # use first 5 if none selected
    insights: list[dict[str, Any]] = []
    for p in projects_subset:
        pid = p.get("id")
        if pid:
            insights.extend(dovetail.get_insights(api_config.dovetail_key, project_id=str(pid)))
    dovetail_summary = _summarize_dovetail(projects_subset, insights)
    log(f"Dovetail: {len(projects_subset)} projects, {len(insights)} insights.")

    # 2. Fetch Productboard data
    log("Fetching Productboard features and notes...")
    features = productboard.get_features(api_config.productboard_key)
    notes = productboard.get_notes(api_config.productboard_key)
    if selected_productboard_ids:
        features = [f for f in features if str(f.get("id", "")) in selected_productboard_ids]
        notes = [n for n in notes if str(n.get("id", "")) in selected_productboard_ids]
    else:
        features = features[:20]
        notes = notes[:20]
    productboard_summary = _summarize_productboard(features, notes)
    log(f"Productboard: {len(features)} features, {len(notes)} notes.")

    # 3. Build prompt
    log("Building prompt...")
    prompt = build_prd_prompt(prompt_config, dovetail_summary, productboard_summary)

    # 4. Call Claude (async run from sync)
    log("Calling Claude...")
    try:
        prd_text = run_async(
            generate_prd(
                prompt=prompt,
                api_key=api_config.anthropic_key,
            )
        )
    except Exception as e:
        err = str(e)
        log(f"Claude error: {err}")
        return "", err, run_id

    log("Pipeline complete.")
    return prd_text, None, run_id
