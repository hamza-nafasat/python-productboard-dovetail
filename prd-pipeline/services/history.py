"""Local JSON store for PRD history and audit."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from app.config import DATA_DIR, HISTORY_FILE

logger = logging.getLogger(__name__)

# Ensure data dir exists
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_all() -> list[dict[str, Any]]:
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.exception("Failed to load history: %s", e)
        return []


def _save_all(entries: list[dict[str, Any]]) -> None:
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def add_entry(
    title: str,
    content: str,
    version: int = 1,
    pipeline_run_id: Optional[str] = None,
    selected_dovetail_ids: Optional[list[str]] = None,
    selected_productboard_ids: Optional[list[str]] = None,
    prompt_config_snapshot: Optional[dict[str, Any]] = None,
    confluence_page_id: Optional[str] = None,
    confluence_url: Optional[str] = None,
) -> str:
    """Append a PRD to history. Returns the new entry id."""
    entries = _load_all()
    entry_id = datetime.utcnow().strftime("%Y%m%d%H%M%S") + f"_{len(entries)}"
    entry = {
        "id": entry_id,
        "title": title,
        "content": content,
        "version": version,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "pipeline_run_id": pipeline_run_id,
        "selected_dovetail_ids": selected_dovetail_ids or [],
        "selected_productboard_ids": selected_productboard_ids or [],
        "prompt_config_snapshot": prompt_config_snapshot or {},
        "confluence_page_id": confluence_page_id,
        "confluence_url": confluence_url,
    }
    entries.append(entry)
    _save_all(entries)
    return entry_id


def list_entries(limit: int = 100) -> list[dict[str, Any]]:
    """Return recent entries, newest first."""
    entries = _load_all()
    entries = sorted(entries, key=lambda x: x.get("timestamp", ""), reverse=True)
    return entries[:limit]


def get_entry(entry_id: str) -> Optional[dict[str, Any]]:
    """Get a single entry by id."""
    for e in _load_all():
        if e.get("id") == entry_id:
            return e
    return None


def update_entry_confluence(entry_id: str, page_id: str, url: str) -> bool:
    """Update an entry with Confluence publish info."""
    entries = _load_all()
    for e in entries:
        if e.get("id") == entry_id:
            e["confluence_page_id"] = page_id
            e["confluence_url"] = url
            _save_all(entries)
            return True
    return False
