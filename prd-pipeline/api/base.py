"""Base HTTP client with timeout and retries."""
import logging
from typing import Any, Optional

import httpx

from app.config import HTTP_MAX_RETRIES, HTTP_TIMEOUT

logger = logging.getLogger(__name__)


def create_client(
    timeout: float = HTTP_TIMEOUT,
    max_retries: int = HTTP_MAX_RETRIES,
    headers: Optional[dict[str, str]] = None,
) -> httpx.Client:
    """Create a sync httpx client with timeout and retry transport."""
    transport = httpx.HTTPTransport(retries=max_retries)
    return httpx.Client(
        timeout=timeout,
        transport=transport,
        headers=headers or {},
    )


def get(
    url: str,
    *,
    headers: Optional[dict[str, str]] = None,
    params: Optional[dict[str, Any]] = None,
) -> httpx.Response:
    """Sync GET with shared timeout. Raises on 4xx/5xx."""
    with create_client(headers=headers) as client:
        r = client.get(url, params=params)
        r.raise_for_status()
        return r
