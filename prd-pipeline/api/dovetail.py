"""Dovetail API client. Projects and insights."""
import logging
from typing import Any, Optional

import httpx

from api.base import create_client
from app.config import HTTP_TIMEOUT

logger = logging.getLogger(__name__)

DOVETAIL_BASE = "https://dovetail.com/api/v1"


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
                headers={"Authorization": f"Bearer {api_key.strip()}"},
            )
            r.raise_for_status()
        return True, ""
    except httpx.HTTPStatusError as e:
        msg = f"HTTP {e.response.status_code}"
        try:
            body = e.response.json()
            if isinstance(body, dict) and "message" in body:
                msg = body["message"]
        except Exception:
            pass
        return False, msg
    except Exception as e:
        return False, str(e)


def get_projects(api_key: str) -> list[dict[str, Any]]:
    """Fetch all projects. Returns list of project dicts with id, name, etc."""
    if not api_key or not api_key.strip():
        return []
    try:
        with create_client(timeout=HTTP_TIMEOUT) as client:
            r = client.get(
                f"{DOVETAIL_BASE}/projects",
                headers={"Authorization": f"Bearer {api_key.strip()}"},
            )
            r.raise_for_status()
            data = r.json()
        # API may return {"data": [...]} or direct list
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        logger.exception("Dovetail get_projects failed: %s", e)
        return []


def get_insights(
    api_key: str,
    project_id: Optional[str] = None,
    per_page: int = 50,
    page: int = 1,
) -> list[dict[str, Any]]:
    """
    Fetch insights. If project_id given, filter by project if API supports it.
    Returns list of insight dicts.
    """
    if not api_key or not api_key.strip():
        return []
    try:
        params: dict[str, Any] = {"per_page": per_page, "page": page}
        if project_id:
            params["project_id"] = project_id
        with create_client(timeout=HTTP_TIMEOUT) as client:
            r = client.get(
                f"{DOVETAIL_BASE}/insights",
                headers={"Authorization": f"Bearer {api_key.strip()}"},
                params=params,
            )
            r.raise_for_status()
            data = r.json()
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        logger.exception("Dovetail get_insights failed: %s", e)
        return []
