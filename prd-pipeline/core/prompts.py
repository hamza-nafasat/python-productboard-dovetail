"""
PRD prompt builder from template and user config.

DEPRECATED: New code should use services.prompt_builder (build_prompt_from_summaries)
which provides normalization, multiple strategies, and structured metadata.
This module is kept for backward compatibility; build_prd_prompt delegates to the new builder.
"""
from __future__ import annotations

import warnings

from core.models import PromptConfig
from services.prompt_builder import build_prompt_from_summaries
from services.prompt_builder.models import PromptBuilderConfig

# Legacy template constants (kept for any code that might reference them)
DEFAULT_TEMPLATE = """# Product Requirements Document

## 1. Overview
{product_context}

## 2. Business Goals
{business_goals}

## 3. Constraints
{constraints}

## 4. User Research & Insights
(To be filled from Dovetail and Productboard data below.)

## 5. Requirements
(Generated from insights and feedback.)

## 6. Success Metrics
(To be defined.)

---
*Audience: {audience_type}. Tone: {output_tone}.*
"""

ROADMAP_SECTION = """

## 7. Roadmap
(High-level phases and milestones.)
"""


def get_template(template_id: str) -> str:
    """Return template body by id. 'default' or unknown returns DEFAULT_TEMPLATE."""
    if template_id == "default":
        return DEFAULT_TEMPLATE
    return DEFAULT_TEMPLATE


def build_prd_prompt(
    config: PromptConfig,
    dovetail_summary: str,
    productboard_summary: str,
) -> str:
    """
    Build a PRD generation prompt (instructions + context + data).
    DEPRECATED: Use services.prompt_builder.build_prompt_from_summaries for new code.
    """
    warnings.warn(
        "core.prompts.build_prd_prompt is deprecated; use services.prompt_builder.build_prompt_from_summaries",
        DeprecationWarning,
        stacklevel=2,
    )
    builder_config = PromptBuilderConfig(
        prd_template_id=config.prd_template_id,
        product_context=config.product_context or "",
        business_goals=config.business_goals or "",
        constraints=config.constraints or "",
        audience_type=config.audience_type,
        output_tone=config.output_tone,
        include_roadmap=config.include_roadmap,
    )
    result = build_prompt_from_summaries(
        dovetail_summary=dovetail_summary,
        productboard_summary=productboard_summary,
        config=builder_config,
    )
    return result.prompt
