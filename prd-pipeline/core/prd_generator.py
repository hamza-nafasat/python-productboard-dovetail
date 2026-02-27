"""
Orchestrates: fetch data from Dovetail/Productboard -> build prompt via prompt_builder -> return prompt + metadata.
Designed to run in a thread; logs and errors are stored for the UI to read.
No AI execution; the prompt is for users to run in their own LLM tools.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Callable, Optional

from core.models import APIConfig, PromptConfig
from services.prompt_builder import build_prompt
from services.prompt_builder.models import PromptBuilderConfig, PromptResult

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
) -> tuple[str, Optional[str], str, Optional[dict[str, Any]]]:
    """
    Run the prompt generation pipeline (sync). Call from a thread.
    Returns (prompt_text, error_message, run_id, metadata).
    If error_message is set, prompt_text may be empty and metadata None.
    """
    run_id = str(uuid.uuid4())[:8]

    def log(msg: str) -> None:
        logger.info("[%s] %s", run_id, msg)
        if log_callback:
            log_callback(msg)

    log("Starting pipeline.")
    try:
        from api import dovetail, productboard
    except ImportError as e:
        err = f"Import error: {e}"
        log(err)
        return "", err, run_id, None

    # 1. Fetch Dovetail data
    log("Fetching Dovetail projects and insights...")
    projects = dovetail.get_projects(api_config.dovetail_key)
    projects_subset = [p for p in projects if str(p.get("id", "")) in selected_dovetail_project_ids]
    if not selected_dovetail_project_ids:
        projects_subset = projects[:5]
    insights: list[dict[str, Any]] = []
    for p in projects_subset:
        pid = p.get("id")
        if pid:
            project_insights = dovetail.get_insights(api_config.dovetail_key, project_id=str(pid))
            # Attach basic project metadata to each insight for richer context downstream.
            project_name = p.get("name") or p.get("title") or str(p.get("id", ""))
            for ins in project_insights:
                ins.setdefault("project_id", p.get("id"))
                ins.setdefault("project_name", project_name)
            insights.extend(project_insights)
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

    # Prepare raw items for the prompt builder (full data path).
    dovetail_raw: list[dict[str, Any]] = list(insights)
    productboard_raw: list[dict[str, Any]] = []
    for f in features:
        f_with_kind = dict(f)
        f_with_kind.setdefault("kind", "feature")
        productboard_raw.append(f_with_kind)
    for n in notes:
        n_with_kind = dict(n)
        n_with_kind.setdefault("kind", "note")
        productboard_raw.append(n_with_kind)

    # 3. Build prompt via prompt_builder (no AI call)
    log("Building prompt...")
    try:
        builder_config = PromptBuilderConfig(
            prd_template_id=prompt_config.prd_template_id,
            product_context=prompt_config.product_context or "",
            business_goals=prompt_config.business_goals or "",
            constraints=prompt_config.constraints or "",
            audience_type=prompt_config.audience_type,
            output_tone=prompt_config.output_tone,
            include_roadmap=prompt_config.include_roadmap,
        )
        result: PromptResult = build_prompt(
            dovetail_raw=dovetail_raw,
            productboard_raw=productboard_raw,
            config=builder_config,
        )
        metadata = result.model_dump()
        # Attach short human-readable previews for debugging/inspection only.
        metadata.setdefault("dovetail_summary_preview", dovetail_summary)
        metadata.setdefault("productboard_summary_preview", productboard_summary)
        log("Pipeline complete.")
        return result.prompt, None, run_id, metadata
    except Exception as e:
        err = str(e)
        log(f"Prompt build error: {err}")
        return "", err, run_id, None
