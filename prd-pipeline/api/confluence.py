"""Confluence REST API client. Spaces, pages, create page."""
import base64
import logging
import re
from typing import Any, Optional

import httpx

from api.base import create_client
from app.config import HTTP_TIMEOUT

logger = logging.getLogger(__name__)

# Confluence Cloud requires Basic auth with email:API_token (see Atlassian docs).
CONFLUENCE_AUTH_HELP = (
    "Confluence Cloud requires your email and API token in one field: email@example.com:YOUR_API_TOKEN"
)


def _base_url(base: str) -> str:
    base = base.rstrip("/")
    if not base.startswith("http"):
        base = "https://" + base
    return base


def _confluence_headers(api_key: str) -> tuple[dict[str, str] | None, str | None]:
    """
    Build Basic auth headers for Confluence Cloud.
    Returns (headers, None) on success, or (None, error_message) if api_key is not in email:token format.
    """
    auth = (api_key or "").strip()
    if not auth:
        return None, "Confluence API key is required"
    if ":" not in auth:
        return None, CONFLUENCE_AUTH_HELP
    auth_b64 = base64.b64encode(auth.encode()).decode()
    return {"Authorization": f"Basic {auth_b64}"}, None


def test_connection(base_url: str, api_key: str, space_key: Optional[str] = None) -> tuple[bool, str]:
    """
    Test Confluence. base_url e.g. https://your-domain.atlassian.net/wiki
    api_key must be email:API_TOKEN (Confluence Cloud requirement).
    Returns (success, error_message).
    """
    if not (base_url or "").strip():
        return False, "Confluence base URL is required"
    headers, err = _confluence_headers(api_key)
    if err:
        return False, err
    base = _base_url(base_url)
    try:
        with create_client(timeout=HTTP_TIMEOUT) as client:
            r = client.get(f"{base}/rest/api/user/current", headers=headers)
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


def get_spaces(base_url: str, api_key: str) -> list[dict[str, Any]]:
    """Fetch spaces. Returns list of space dicts with key, name."""
    headers, _ = _confluence_headers(api_key)
    if not headers:
        return []
    base = _base_url(base_url)
    try:
        with create_client(timeout=HTTP_TIMEOUT) as client:
            r = client.get(
                f"{base}/rest/api/space",
                headers=headers,
                params={"limit": 50},
            )
            r.raise_for_status()
            data = r.json()
        if isinstance(data, dict) and "results" in data:
            return data["results"]
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        logger.exception("Confluence get_spaces failed: %s", e)
        return []


def get_pages(base_url: str, api_key: str, space_key: str) -> list[dict[str, Any]]:
    """Fetch pages in a space. Returns list with id, title, etc."""
    headers, _ = _confluence_headers(api_key)
    if not headers or not space_key:
        return []
    base = _base_url(base_url)
    try:
        with create_client(timeout=HTTP_TIMEOUT) as client:
            r = client.get(
                f"{base}/rest/api/content",
                headers=headers,
                params={"spaceKey": space_key, "type": "page", "limit": 100},
            )
            r.raise_for_status()
            data = r.json()
        if isinstance(data, dict) and "results" in data:
            return data["results"]
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        logger.exception("Confluence get_pages failed: %s", e)
        return []


def markdown_to_confluence_storage(md: str) -> str:
    """Convert Markdown to Confluence storage format (XHTML-like). Minimal implementation."""
    if not md:
        return "<p></p>"
    html = md
    # Headings
    for level in range(1, 7):
        html = re.sub(rf"^#{'{' + str(level) + '}'}\s+(.+)$", f"<h{level}>\\1</h{level}>", html, flags=re.MULTILINE)
    # Bold
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"__(.+?)__", r"<strong>\1</strong>", html)
    # Italic
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
    html = re.sub(r"_(.+?)_", r"<em>\1</em>", html)
    # Code block
    html = re.sub(r"```(\w*)\n(.*?)```", r"<pre>\2</pre>", html, flags=re.DOTALL)
    html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)
    # Unordered list
    html = re.sub(r"^\s*-\s+(.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
    html = re.sub(r"(<li>.*</li>\n?)+", r"<ul>\g<0></ul>", html)
    # Paragraphs: wrap consecutive non-tag lines
    lines = html.split("\n")
    out = []
    in_para = False
    for line in lines:
        if re.match(r"^<(h[1-6]|ul|ol|li|pre|code)", line) or line.strip() == "":
            if in_para:
                out.append("</p>")
                in_para = False
            if line.strip():
                out.append(line)
        else:
            if not in_para:
                out.append("<p>")
                in_para = True
            out.append(line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    if in_para:
        out.append("</p>")
    return "\n".join(out) if out else "<p></p>"


def create_page(
    base_url: str,
    api_key: str,
    space_key: str,
    title: str,
    body_storage_html: str,
    parent_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create a Confluence page. Returns created page dict with id, _links.webui, etc.
    """
    headers, _ = _confluence_headers(api_key)
    if not headers:
        raise ValueError(CONFLUENCE_AUTH_HELP)
    base = _base_url(base_url)
    headers = {**headers, "Content-Type": "application/json"}
    payload = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "body": {
            "storage": {
                "value": body_storage_html,
                "representation": "storage",
            }
        },
    }
    if parent_id:
        payload["ancestors"] = [{"id": parent_id}]
    with create_client(timeout=HTTP_TIMEOUT) as client:
        r = client.post(
            f"{base}/rest/api/content",
            headers=headers,
            json=payload,
        )
        r.raise_for_status()
        return r.json()
