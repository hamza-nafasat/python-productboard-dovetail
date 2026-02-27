"""
Clean, normalize, and deduplicate raw insights and feedback.

Pure in-memory logic; no API calls. Used by the builder before passing
data to a prompt strategy. Separation of concerns: this layer only
handles data quality; strategies handle prompt structure.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

from services.prompt_builder.models import (
    FeedbackItem,
    InsightItem,
    NormalizedFeedback,
    NormalizedInsights,
)


def _normalize_text(text: str, max_len: int = 0) -> str:
    """Trim, collapse whitespace, optionally truncate."""
    if not text or not isinstance(text, str):
        return ""
    s = " ".join(text.split())
    if max_len and len(s) > max_len:
        return s[: max_len - 3].rstrip() + "..."
    return s


def _content_hash(item: dict[str, Any], keys: list[str]) -> str:
    """Stable hash for deduplication from key fields."""
    parts = [str(item.get(k, "")) for k in keys]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def normalize_insights(
    raw: list[dict[str, Any]],
    *,
    max_items: int = 30,
    body_max_len: int = 800,
    title_max_len: int = 200,
) -> NormalizedInsights:
    """
    Clean and deduplicate raw insight dicts (e.g. from Dovetail).
    Returns normalized items and a summary text block for the prompt.
    """
    seen: set[str] = set()
    items: list[InsightItem] = []
    for r in raw[: max_items * 2]:  # allow extra for dedupe
        if not isinstance(r, dict):
            continue
        title = _normalize_text(str(r.get("name") or r.get("title") or r.get("id", "")), title_max_len)
        body = _normalize_text(
            str(r.get("body") or r.get("content") or r.get("text") or ""),
            body_max_len,
        )
        key = _content_hash({"title": title, "body": body}, ["title", "body"])
        if key in seen:
            continue
        seen.add(key)
        items.append(
            InsightItem(
                id=str(r.get("id", "")),
                title=title or "Insight",
                body=body,
                source="dovetail",
            )
        )
        if len(items) >= max_items:
            break

    lines = [f"- {i.title}. {i.body}" for i in items]
    summary_text = "\n".join(lines) if lines else "No Dovetail insights selected."
    return NormalizedInsights(items=items, summary_text=summary_text)


def normalize_feedback(
    raw: list[dict[str, Any]],
    *,
    max_items: int = 20,
    content_max_len: int = 600,
    title_max_len: int = 200,
) -> NormalizedFeedback:
    """
    Clean and deduplicate raw feedback dicts (e.g. from Productboard).
    Returns normalized items and a summary text block for the prompt.
    """
    seen: set[str] = set()
    items: list[FeedbackItem] = []
    for r in raw[: max_items * 2]:
        if not isinstance(r, dict):
            continue
        title = _normalize_text(str(r.get("name") or r.get("title") or r.get("id", "")), title_max_len)
        content = _normalize_text(
            str(r.get("content") or r.get("description") or ""),
            content_max_len,
        )
        key = _content_hash({"title": title, "content": content}, ["title", "content"])
        if key in seen:
            continue
        seen.add(key)
        items.append(
            FeedbackItem(
                id=str(r.get("id", "")),
                title=title or "Feedback",
                content=content,
                source="productboard",
            )
        )
        if len(items) >= max_items:
            break

    lines = [f"- {i.title}. {i.content}" for i in items]
    summary_text = "\n".join(lines) if lines else "No Productboard feedback selected."
    return NormalizedFeedback(items=items, summary_text=summary_text)
