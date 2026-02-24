"""Productboard API client. Features and notes."""
import logging
from typing import Any, Optional

import httpx

from api.base import create_client
from app.config import HTTP_TIMEOUT

logger = logging.getLogger(__name__)

PRODUCTBOARD_BASE = "https://api.productboard.com"
# Required by Productboard API. Must be "1" (only accepted value per API enum).
PRODUCTBOARD_API_VERSION = "1"


def _headers(api_key: str) -> dict[str, str]:
    """Request headers including required X-Version."""
    return {
        "Authorization": f"Bearer {api_key.strip()}",
        "X-Version": PRODUCTBOARD_API_VERSION,
    }


def test_connection(api_key: str) -> tuple[bool, str]:
    """
    Test Productboard API (e.g. list features).
    Returns (success, error_message).
    """
    if not api_key or not api_key.strip():
        return False, "API key is empty"
    try:
        with create_client(timeout=HTTP_TIMEOUT) as client:
            r = client.get(
                f"{PRODUCTBOARD_BASE}/features",
                headers=_headers(api_key),
            )
            r.raise_for_status()
        return True, ""
    except httpx.HTTPStatusError as e:
        msg = f"HTTP {e.response.status_code}"
        try:
            body = e.response.json()
            if isinstance(body, dict) and "errors" in body:
                msg = body.get("errors", [{}])[0].get("detail", msg)
        except Exception:
            pass
        return False, msg
    except Exception as e:
        return False, str(e)


def get_features(api_key: str) -> list[dict[str, Any]]:
    """Fetch all features. Returns list of feature dicts."""
    if not api_key or not api_key.strip():
        return []
    try:
        with create_client(timeout=HTTP_TIMEOUT) as client:
            r = client.get(
                f"{PRODUCTBOARD_BASE}/features",
                headers=_headers(api_key),
            )
            r.raise_for_status()
            data = r.json()
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        logger.exception("Productboard get_features failed: %s", e)
        return []


def get_notes(api_key: str) -> list[dict[str, Any]]:
    """Fetch all notes (feedback). Returns list of note dicts."""
    if not api_key or not api_key.strip():
        return []
    try:
        with create_client(timeout=HTTP_TIMEOUT) as client:
            r = client.get(
                f"{PRODUCTBOARD_BASE}/notes",
                headers=_headers(api_key),
            )
            r.raise_for_status()
            data = r.json()
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        logger.exception("Productboard get_notes failed: %s", e)
        return []


def get_areas(api_key: str) -> list[dict[str, Any]]:
    """Fetch product areas if API supports it; otherwise derive from features."""
    # Productboard may expose areas; fallback to features as "areas" for selection
    features = get_features(api_key)
    # If there's a dedicated areas endpoint, use it; for now use features
    return features
