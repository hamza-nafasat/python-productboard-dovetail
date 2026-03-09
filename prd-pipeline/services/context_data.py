"""
Context data layer: parallel fetch of Dovetail (projects + insights) and Productboard (products),
with a unified normalized structure. API logic is separate from UI.
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from api import dovetail, productboard

logger = logging.getLogger(__name__)


def _project_id_from_insight(insight: dict[str, Any]) -> str | None:
    """Extract project_id from an insight (may be in project.id, project_id, or relationships)."""
    pid = insight.get("project_id")
    if pid is not None and str(pid).strip():
        return str(pid).strip()
    proj = insight.get("project")
    if isinstance(proj, dict) and proj.get("id") is not None:
        return str(proj["id"]).strip()
    if isinstance(proj, str) and proj.strip():
        return proj.strip()
    rel = insight.get("relationships") or {}
    proj_rel = (rel.get("project") or {}).get("data") if isinstance(rel.get("project"), dict) else None
    if isinstance(proj_rel, dict) and proj_rel.get("id"):
        return str(proj_rel["id"]).strip()
    attrs = insight.get("attributes") or {}
    if attrs.get("project_id"):
        return str(attrs["project_id"]).strip()
    return None


def _insight_summary(insight: dict[str, Any], max_len: int = 300) -> str:
    """Derive a short summary from insight body/content/text."""
    for key in ("body", "content", "text", "summary", "description"):
        val = insight.get(key)
        if val and isinstance(val, str) and val.strip():
            s = " ".join(val.split())
            return s[:max_len] + ("..." if len(s) > max_len else "")
    return ""


def _normalize_dovetail(projects: list[dict], insights: list[dict]) -> dict[str, Any]:
    """Group insights by project_id and attach to projects. Returns dovetail part of context."""
    pid_to_insights: dict[str, list[dict[str, Any]]] = {}
    for ins in insights:
        if not isinstance(ins, dict):
            continue
        pid = _project_id_from_insight(ins)
        if not pid:
            continue
        pid_to_insights.setdefault(pid, []).append({
            "id": str(ins.get("id", "")),
            "title": (ins.get("title") or ins.get("name") or "(No title)").strip(),
            "summary": _insight_summary(ins),
        })
    project_list: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for p in projects:
        if not isinstance(p, dict):
            continue
        pid = str(p.get("id", "")).strip()
        if not pid or pid in seen_ids:
            continue
        seen_ids.add(pid)
        name = (p.get("name") or p.get("title") or pid).strip()
        project_list.append({
            "id": pid,
            "name": name,
            "insights": pid_to_insights.get(pid, []),
        })
    for pid, ins_list in pid_to_insights.items():
        if pid in seen_ids:
            continue
        seen_ids.add(pid)
        project_list.append({
            "id": pid,
            "name": f"Project {pid}",
            "insights": ins_list,
        })
    return {"projects": project_list}


def _normalize_productboard(products: list[dict]) -> dict[str, Any]:
    """Normalize products to { id, name }."""
    out = []
    for p in products:
        if not isinstance(p, dict):
            continue
        pid = p.get("id")
        if pid is None:
            continue
        name = (p.get("name") or p.get("title") or str(pid)).strip()
        out.append({"id": str(pid), "name": name})
    return {"products": out}


def fetch_context_data(dovetail_key: str, productboard_key: str) -> dict[str, Any]:
    """
    Fetch all context in parallel (Dovetail projects, Dovetail insights, Productboard products),
    then normalize into a unified structure. Avoids N+1 by fetching all insights once.
    """
    result: dict[str, Any] = {
        "dovetail": {"projects": []},
        "productboard": {"products": []},
    }
    projects: list[dict] = []
    insights: list[dict] = []
    products: list[dict] = []

    def fetch_projects() -> None:
        nonlocal projects
        if dovetail_key and dovetail_key.strip():
            projects = dovetail.get_projects(dovetail_key)

    def fetch_insights() -> None:
        nonlocal insights
        if dovetail_key and dovetail_key.strip():
            insights = dovetail.get_all_insights(dovetail_key, page_size=100)

    def fetch_products() -> None:
        nonlocal products
        if productboard_key and productboard_key.strip():
            products = productboard.get_products(productboard_key)

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(fetch_projects),
            executor.submit(fetch_insights),
            executor.submit(fetch_products),
        ]
        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                logger.warning("Context fetch task failed: %s", e)

    result["dovetail"] = _normalize_dovetail(projects, insights)
    result["productboard"] = _normalize_productboard(products)
    return result


def build_prd_prompt_for_claude(
    selected_product_names: list[str],
    selected_insight_titles: list[str],
) -> str:
    """
    Generate a structured Claude prompt for PRD generation.
    Returns a single string the user can copy and paste into Claude.
    """
    product_block = ", ".join(selected_product_names) if selected_product_names else "(none selected)"
    insight_lines = "\n".join(f"{i+1}. {t}" for i, t in enumerate(selected_insight_titles))
    if not insight_lines:
        insight_lines = "(none selected)"

    return f"""CONTEXT
You are an expert product manager.

PRODUCT
{product_block}

USER RESEARCH INSIGHTS

{insight_lines}

TASK
Generate a detailed Product Requirement Document.

OUTPUT FORMAT
Problem
User Persona
Goals
Proposed Solution
Features
Success Metrics
"""
