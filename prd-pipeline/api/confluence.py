"""Confluence REST API client. Spaces, pages, create page."""
import logging
import re
from typing import Any, Optional
from urllib.parse import urljoin

import httpx

from api.base import create_client
from app.config import HTTP_TIMEOUT

logger = logging.getLogger(__name__)


def _base_url(base: str) -> str:
    base = base.rstrip("/")
    if not base.startswith("http"):
        base = "https://" + base
    return base


def test_connection(base_url: str, api_key: str, space_key: Optional[str] = None) -> tuple[bool, str]:
    """
    Test Confluence: get current user or space.
    For Cloud: use API token as basic auth (email:token). base_url e.g. https://your-domain.atlassian.net/wiki
    Returns (success, error_message).
    """
    if not base_url or not api_key or not api_key.strip():
        return False, "Base URL and API key are required"
    base = _base_url(base_url)
    # Confluence Cloud: often uses email:api_token for Basic auth
    try:
        with create_client(timeout=HTTP_TIMEOUT) as client:
            # Try /rest/api/user/current or /rest/api/space
            url = f"{base}/rest/api/user/current"
            # Assume API key might be "email:token" or just token
            auth = api_key.strip()
            if ":" not in auth:
                # Cloud often needs email:api_token; if only token, try as Bearer (if supported) or Basic
                import base64
                auth_b64 = base64.b64encode(f"{auth}:{auth}".encode()).decode()  # noqa: placeholder
                headers = {"Authorization": f"Basic {auth_b64}"}
            else:
                import base64
                auth_b64 = base64.b64encode(auth.encode()).decode()
                headers = {"Authorization": f"Basic {auth_b64}"}
            r = client.get(url, headers=headers)
            r.raise_for_status()
        return True, ""
    except httpx.HTTPStatusError as e:
        # 401/403 common for bad auth
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
    base = _base_url(base_url)
    if not api_key or not api_key.strip():
        return []
    try:
        auth = api_key.strip()
        import base64
        if ":" in auth:
            auth_b64 = base64.b64encode(auth.encode()).decode()
        else:
            auth_b64 = base64.b64encode(f"{auth}:{auth}".encode()).decode()
        headers = {"Authorization": f"Basic {auth_b64}"}
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
    base = _base_url(base_url)
    if not api_key or not api_key.strip() or not space_key:
        return []
    try:
        auth = api_key.strip()
        import base64
        if ":" in auth:
            auth_b64 = base64.b64encode(auth.encode()).decode()
        else:
            auth_b64 = base64.b64encode(f"{auth}:{auth}".encode()).decode()
        headers = {"Authorization": f"Basic {auth_b64}"}
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
    base = _base_url(base_url)
    auth = api_key.strip()
    import base64
    if ":" in auth:
        auth_b64 = base64.b64encode(auth.encode()).decode()
    else:
        auth_b64 = base64.b64encode(f"{auth}:{auth}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json",
    }
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
