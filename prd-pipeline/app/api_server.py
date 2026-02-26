"""
FastAPI app exposing POST /generate-prd-prompt.

Run from prd-pipeline directory: uvicorn app.api_server:app --reload
The Streamlit UI calls the prompt_builder service directly; this endpoint
is for external clients and API access.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure project root (prd-pipeline) is on path when running uvicorn
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from services.prompt_builder import build_prompt_from_summaries
from services.prompt_builder.models import PromptBuilderConfig, PromptResult

logger = logging.getLogger(__name__)

app = FastAPI(
    title="PRD Prompt API",
    description="Generate structured PRD prompts from research and feedback data.",
    version="0.1.0",
)


# --- Request/response models (API contract) ---


class GeneratePromptRequest(BaseModel):
    """Request body for POST /generate-prd-prompt."""
    product_context: str = Field(default="", description="Product and problem space")
    business_goals: str = Field(default="", description="Business objectives")
    constraints: str = Field(default="", description="Constraints")
    audience_type: str = Field(default="internal_stakeholders", description="Target audience")
    output_tone: str = Field(default="professional", description="Tone")
    include_roadmap: bool = Field(default=True, description="Include roadmap section")
    prd_template_id: str = Field(default="default", description="Template/strategy id")
    dovetail_summary: str = Field(default="", description="Pre-aggregated Dovetail research text")
    productboard_summary: str = Field(default="", description="Pre-aggregated Productboard feedback text")


class GeneratePromptResponse(BaseModel):
    """Response: prompt text and metadata."""
    prompt: str = Field(..., description="Full PRD generation prompt")
    metadata: dict = Field(..., description="Strategy id, word count, sections, etc.")


@app.post("/generate-prd-prompt", response_model=GeneratePromptResponse)
def generate_prd_prompt(body: GeneratePromptRequest) -> GeneratePromptResponse:
    """
    Build a structured PRD generation prompt from config and pre-aggregated
    Dovetail/Productboard summaries. Returns the prompt and metadata.
    """
    try:
        config = PromptBuilderConfig(
            prd_template_id=body.prd_template_id,
            product_context=body.product_context,
            business_goals=body.business_goals,
            constraints=body.constraints,
            audience_type=body.audience_type,
            output_tone=body.output_tone,
            include_roadmap=body.include_roadmap,
        )
        result: PromptResult = build_prompt_from_summaries(
            dovetail_summary=body.dovetail_summary or "No Dovetail data provided.",
            productboard_summary=body.productboard_summary or "No Productboard data provided.",
            config=config,
        )
        return GeneratePromptResponse(
            prompt=result.prompt,
            metadata=result.model_dump(),
        )
    except Exception as e:
        logger.exception("Prompt build failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to build prompt.")


@app.get("/health")
def health() -> dict[str, str]:
    """Health check for load balancers."""
    return {"status": "ok"}
