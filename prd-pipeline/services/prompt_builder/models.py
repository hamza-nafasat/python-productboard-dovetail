"""
Pydantic models for prompt_builder inputs and outputs.

Keeps the builder independent of Streamlit/app globals and enables
validation and JSON serialization for the API layer.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# --- Input models (raw data from Dovetail/Productboard) ---


class InsightItem(BaseModel):
    """Single research insight (e.g. from Dovetail)."""
    id: str = ""
    title: str = ""
    body: str = ""
    source: str = "dovetail"

    class Config:
        extra = "allow"


class FeedbackItem(BaseModel):
    """Single customer feedback item (e.g. from Productboard)."""
    id: str = ""
    title: str = ""
    content: str = ""
    source: str = "productboard"

    class Config:
        extra = "allow"


# --- Prompt configuration (mirrors core.models.PromptConfig for builder use) ---


class PromptBuilderConfig(BaseModel):
    """Configuration for PRD prompt generation. Mirrors core PromptConfig."""
    prd_template_id: str = Field(default="default", description="Template/strategy id")
    product_context: str = Field(default="", description="Product and problem space")
    business_goals: str = Field(default="", description="Business objectives")
    constraints: str = Field(default="", description="Technical/timeline constraints")
    audience_type: str = Field(default="internal_stakeholders", description="Target audience")
    output_tone: str = Field(default="professional", description="Tone of the PRD")
    include_roadmap: bool = Field(default=True, description="Include roadmap section")

    class Config:
        extra = "forbid"


# --- Normalized inputs (after normalizer) ---


class NormalizedInsights(BaseModel):
    """Cleaned and deduplicated research insights."""
    items: list[InsightItem] = Field(default_factory=list)
    summary_text: str = Field(default="", description="Aggregated text for prompt")


class NormalizedFeedback(BaseModel):
    """Cleaned and deduplicated customer feedback."""
    items: list[FeedbackItem] = Field(default_factory=list)
    summary_text: str = Field(default="", description="Aggregated text for prompt")


# --- Output model ---


class PromptResult(BaseModel):
    """Result of building a PRD prompt: the prompt text and metadata."""
    prompt: str = Field(..., description="Full PRD generation prompt for any LLM")
    strategy_id: str = Field(default="default", description="Strategy used")
    template_id: str = Field(default="default", description="Template id")
    word_count: int = Field(default=0, description="Approximate word count of prompt")
    sections: list[str] = Field(default_factory=list, description="Section names included")
    template_version: str = Field(default="1", description="For future prompt versioning")

    class Config:
        extra = "forbid"
