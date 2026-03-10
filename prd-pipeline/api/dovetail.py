"""Dovetail API client. Projects and highlights (insights) with cursor pagination."""
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Optional

import httpx

from api.base import create_client
from app.config import HTTP_TIMEOUT

logger = logging.getLogger(__name__)

DOVETAIL_BASE = "https://dovetail.com/api/v1"
PAGE_LIMIT = 100
# Cap insights per project (load only first N for Step 2)
MAX_INSIGHTS_PER_PROJECT = 20
MAX_CONCURRENT_REQUESTS = 5


def _headers(api_key: str) -> dict[str, str]:
    if not api_key or not api_key.strip():
        return {}
    return {"Authorization": f"Bearer {api_key.strip()}"}


def _parse_list_response(data: Any) -> tuple[list[dict[str, Any]], Optional[str]]:
    """Extract data list and next_cursor from API response. Handles missing/malformed page."""
    items: list[dict[str, Any]] = []
    next_cursor: Optional[str] = None
    if isinstance(data, dict):
        items = data.get("data") if isinstance(data.get("data"), list) else []
        page = data.get("page") if isinstance(data.get("page"), dict) else {}
        if page.get("has_more") and page.get("next_cursor"):
            next_cursor = str(page["next_cursor"]).strip() or None
    elif isinstance(data, list):
        items = data
    return items, next_cursor


def test_connection(api_key: str) -> tuple[bool, str]:
    """
    Test Dovetail API connection (e.g. list projects).
    Returns (success, error_message).
    """
    if not api_key or not api_key.strip():
        return False, "API key is empty"
    try:
        with create_client(timeout=HTTP_TIMEOUT) as client:
            r = client.get(
                f"{DOVETAIL_BASE}/projects",
                headers=_headers(api_key),
                params={"page[limit]": 1},
            )
            r.raise_for_status()
        return True, ""
    except httpx.HTTPStatusError as e:
        msg = f"HTTP {e.response.status_code}"
        try:
            body = e.response.json()
            if isinstance(body, dict) and "errors" in body:
                errs = body.get("errors", [])
                if errs and isinstance(errs[0], dict) and "message" in errs[0]:
                    msg = errs[0]["message"]
            elif isinstance(body, dict) and "message" in body:
                msg = body["message"]
        except Exception:
            pass
        return False, msg
    except Exception as e:
        return False, str(e)


def get_projects(api_key: str) -> list[dict[str, Any]]:
    """
    Fetch ALL projects from GET /v1/projects using cursor pagination (next_cursor) until no more pages.
    Returns list of project dicts with id, name, etc.
    """
    if not api_key or not api_key.strip():
        return []
    all_projects: list[dict[str, Any]] = []
    start_cursor: Optional[str] = None
    try:
        with create_client(timeout=HTTP_TIMEOUT) as client:
            while True:
                params: dict[str, Any] = {"page[limit]": PAGE_LIMIT}
                if start_cursor:
                    params["page[start_cursor]"] = start_cursor
                r = client.get(
                    f"{DOVETAIL_BASE}/projects",
                    headers=_headers(api_key),
                    params=params,
                )
                r.raise_for_status()
                data = r.json()
                items, next_cursor = _parse_list_response(data)
                for p in items:
                    if isinstance(p, dict) and (p.get("id") is not None or p.get("id") != ""):
                        all_projects.append(dict(p))
                if not next_cursor:
                    break
                start_cursor = next_cursor
                logger.debug("Projects next_cursor: %s", start_cursor[:20] if start_cursor else None)
        return all_projects
    except httpx.HTTPStatusError as e:
        logger.exception("Dovetail get_projects HTTP error: %s %s", e.response.status_code, e.response.text)
        return all_projects
    except Exception as e:
        logger.exception("Dovetail get_projects failed: %s", e)
        return all_projects


def _get_highlights_page(
    client: httpx.Client,
    api_key: str,
    project_id: str,
    start_cursor: Optional[str] = None,
) -> tuple[list[dict[str, Any]], Optional[str]]:
    """
    Fetch one page of highlights for a project from GET /v1/highlights?project_id={project_id}.
    Uses cursor pagination. Returns (items, next_cursor).
    """
    params: dict[str, Any] = {"project_id": project_id, "page[limit]": PAGE_LIMIT}
    if start_cursor:
        params["page[start_cursor]"] = start_cursor
    try:
        r = client.get(
            f"{DOVETAIL_BASE}/highlights",
            headers=_headers(api_key),
            params=params,
        )
        r.raise_for_status()
        data = r.json()
        logger.info("Dovetail highlights API response (project_id=%s): %s", project_id, json.dumps(data, default=str))
        return _parse_list_response(data)
    except Exception as e:
        logger.warning("Dovetail _get_highlights_page failed for project %s: %s", project_id, e)
        return [], None


def _get_insights_page(
    client: httpx.Client,
    api_key: str,
    project_id: str,
    start_cursor: Optional[str] = None,
) -> tuple[list[dict[str, Any]], Optional[str]]:
    """
    Fetch one page of insights (highlights) for a project.
    Uses GET /v1/highlights?project_id={project_id} per Dovetail API.
    """
    return _get_highlights_page(client, api_key, project_id, start_cursor)


def get_all_insights(api_key: str, page_size: int = 100) -> list[dict[str, Any]]:
    """
    Fetch all insights (highlights) by project. Uses GET /v1/highlights?project_id={id} per project
    (no single "all highlights" endpoint). Returns combined list with project_id set on each item.
    """
    if not api_key or not api_key.strip():
        return []
    projects = get_projects(api_key)
    if not projects:
        return []
    all_items: list[dict[str, Any]] = []
    try:
        with create_client(timeout=HTTP_TIMEOUT) as client:
            for p in projects:
                pid = p.get("id")
                if pid is None or str(pid).strip() == "":
                    continue
                pid = str(pid).strip()
                start_cursor: Optional[str] = None
                while True:
                    items, next_cursor = _get_highlights_page(client, api_key, pid, start_cursor)
                    for ins in items:
                        if isinstance(ins, dict):
                            rec = dict(ins)
                            rec.setdefault("project_id", pid)
                            all_items.append(rec)
                    if not next_cursor:
                        break
                    start_cursor = next_cursor
        return all_items
    except Exception as e:
        logger.exception("Dovetail get_all_insights (highlights by project) failed: %s", e)
        return all_items


def get_highlights(api_key: str, project_id: str) -> list[dict[str, Any]]:
    """
    Fetch all highlights for a project from GET /v1/highlights?project_id={project_id}.
    Uses cursor pagination. Returns list of highlight dicts (exposed as 'insights' in the app).
    """
    return get_insights(api_key, project_id=project_id)


def get_insights(
    api_key: str,
    project_id: Optional[str] = None,
    per_page: int = 50,
    page: int = 1,
) -> list[dict[str, Any]]:
    """
    Fetch insights (highlights) with pagination. If project_id is given, uses
    GET /v1/highlights?project_id={project_id} with cursor pagination until no more pages.
    Returns list of highlight/insight dicts with project_id set.
    """
    if not api_key or not api_key.strip():
        return []
    if not project_id:
        return get_all_insights(api_key)
    all_insights: list[dict[str, Any]] = []
    start_cursor: Optional[str] = None
    try:
        with create_client(timeout=HTTP_TIMEOUT) as client:
            while True:
                items, next_cursor = _get_insights_page(client, api_key, project_id, start_cursor)
                for ins in items:
                    if isinstance(ins, dict):
                        ins = dict(ins)
                        ins.setdefault("project_id", project_id)
                        all_insights.append(ins)
                if not next_cursor or len(all_insights) >= MAX_INSIGHTS_PER_PROJECT:
                    break
                start_cursor = next_cursor
        if len(all_insights) >= MAX_INSIGHTS_PER_PROJECT:
            logger.info("Dovetail get_insights for project %s capped at %s insights.", project_id, MAX_INSIGHTS_PER_PROJECT)
        return all_insights
    except Exception as e:
        logger.exception("Dovetail get_insights for project %s failed: %s", project_id, e)
        return all_insights


def get_insight(api_key: str, insight_id: str) -> Optional[dict[str, Any]]:
    """
    Fetch full insight details from GET /v1/insights/{insight_id}.
    Returns the full insight object or None on failure/missing.
    """
    if not api_key or not api_key.strip() or not insight_id or not str(insight_id).strip():
        return None
    try:
        with create_client(timeout=HTTP_TIMEOUT) as client:
            r = client.get(
                f"{DOVETAIL_BASE}/insights/{insight_id.strip()}",
                headers=_headers(api_key),
            )
            r.raise_for_status()
            data = r.json()
            logger.info("Dovetail insight API response (insight_id=%s): %s", insight_id, json.dumps(data, default=str))
            if isinstance(data, dict) and "data" in data:
                return dict(data["data"]) if isinstance(data["data"], dict) else None
            return dict(data) if isinstance(data, dict) else None
    except httpx.HTTPStatusError as e:
        logger.warning("Dovetail get_insight %s: HTTP %s", insight_id, e.response.status_code)
        return None
    except Exception as e:
        logger.warning("Dovetail get_insight %s failed: %s", insight_id, e)
        return None


def sync_dovetail_projects(api_key: str) -> dict[str, Any]:
    """
    Fetch all projects, then for each project fetch highlights (GET /v1/highlights?project_id=...),
    then fetch full insight details per item. Returns structure with projects and nested insights.
    """
    result: dict[str, Any] = {"projects": []}
    if not api_key or not api_key.strip():
        logger.warning("sync_dovetail_projects: empty API key")
        return result

    projects = get_projects(api_key)
    if not projects:
        logger.info("sync_dovetail_projects: no projects returned")
        return result

    for proj in projects:
        pid = proj.get("id")
        if pid is None or str(pid).strip() == "":
            continue
        pid = str(pid).strip()
        name = proj.get("name") or proj.get("title") or ""
        project_node: dict[str, Any] = {
            "id": pid,
            "name": name,
            "insights": [],
        }

        insight_refs = get_insights(api_key, project_id=pid)
        if not insight_refs:
            result["projects"].append(project_node)
            continue

        def fetch_one(ins_ref: dict[str, Any]) -> Optional[dict[str, Any]]:
            iid = ins_ref.get("id") if isinstance(ins_ref, dict) else None
            if not iid:
                return None
            details = get_insight(api_key, str(iid))
            if details is None:
                return {"id": str(iid), "title": ins_ref.get("title") or ins_ref.get("name") or "", "details": {}}
            return {
                "id": str(iid),
                "title": details.get("title") or details.get("name") or "",
                "details": details,
            }

        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
            futures = {executor.submit(fetch_one, ref): ref for ref in insight_refs}
            for future in as_completed(futures):
                try:
                    item = future.result()
                    if item:
                        project_node["insights"].append(item)
                except Exception as e:
                    ref = futures.get(future)
                    logger.warning("sync_dovetail_projects: insight fetch failed for %s: %s", ref, e)

        result["projects"].append(project_node)

    logger.info("sync_dovetail_projects: fetched %s projects", len(result["projects"]))
    try:
        logger.info("sync_dovetail_projects result (structured JSON):\n%s", json.dumps(result, indent=2, default=str))
    except Exception as e:
        logger.warning("sync_dovetail_projects: could not log JSON: %s", e)
    return result


if __name__ == "__main__":
    import os
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    key = os.environ.get("DOVETAIL_API_KEY", "").strip()
    if not key:
        print("Set DOVETAIL_API_KEY in environment to run sync.", file=sys.stderr)
        sys.exit(1)
    out = sync_dovetail_projects(key)
    print(json.dumps(out, indent=2, default=str))
