"""Pydantic/dataclass models for API responses and app config."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class APIConfig:
    """API keys and Confluence settings (session-only)."""
    dovetail_key: str = ""
    productboard_key: str = ""
    anthropic_key: str = ""
    confluence_key: str = ""
    confluence_base_url: str = ""
    confluence_space: str = ""

    @classmethod
    def from_session_dict(cls, d: dict[str, Any]) -> "APIConfig":
        return cls(
            dovetail_key=d.get("dovetail_key", "") or "",
            productboard_key=d.get("productboard_key", "") or "",
            anthropic_key=d.get("anthropic_key", "") or "",
            confluence_key=d.get("confluence_key", "") or "",
            confluence_base_url=d.get("confluence_base_url", "") or "",
            confluence_space=d.get("confluence_space", "") or "",
        )


@dataclass
class PromptConfig:
    """PRD generation prompt options."""
    prd_template_id: str = "default"
    product_context: str = ""
    business_goals: str = ""
    constraints: str = ""
    audience_type: str = "internal_stakeholders"
    output_tone: str = "professional"
    include_roadmap: bool = True


@dataclass
class DataSourceFilters:
    """Filters for Dovetail/Productboard."""
    tags: list[str] = field(default_factory=list)
    date_from: str = ""
    date_to: str = ""
    priority: str = ""


@dataclass
class PRDHistoryEntry:
    """One saved PRD in history."""
    id: str
    title: str
    content: str
    version: int
    timestamp: str
    pipeline_run_id: Optional[str] = None
    selected_dovetail_ids: list[str] = field(default_factory=list)
    selected_productboard_ids: list[str] = field(default_factory=list)
    prompt_config_snapshot: dict[str, Any] = field(default_factory=dict)
    confluence_page_id: Optional[str] = None
    confluence_url: Optional[str] = None
