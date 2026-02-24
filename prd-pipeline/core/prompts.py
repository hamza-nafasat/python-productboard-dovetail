"""PRD prompt builder from template and user config."""
from __future__ import annotations

from typing import Any

from core.models import PromptConfig

# Default template structure (placeholders filled by build_prd_prompt)
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
    Build the full prompt sent to Claude: instructions + context + data.
    Claude will output a complete PRD in Markdown.
    """
    context = config.product_context or "General product."
    goals = config.business_goals or "To be defined."
    constraints = config.constraints or "None specified."
    audience = config.audience_type.replace("_", " ").title()
    tone = config.output_tone.replace("_", " ").title()

    template = get_template(config.prd_template_id)
    roadmap_block = ROADMAP_SECTION if config.include_roadmap else ""

    system_instruction = f"""You are an expert product manager. Write a complete, production-ready Product Requirements Document (PRD) in Markdown.

Guidelines:
- Audience: {audience}. Use a {tone} tone.
- Be specific and actionable. Include clear success criteria where relevant.
- Structure with clear headings (##, ###). Use bullet lists for requirements.
- Base the content on the research and feedback data provided below; do not invent data.
- Output only the PRD Markdown, no meta-commentary."""

    user_content = f"""Use this context to write the PRD:

**Product context**
{context}

**Business goals**
{goals}

**Constraints**
{constraints}

**User research (Dovetail)**
{dovetail_summary}

**Product feedback (Productboard)**
{productboard_summary}

Generate the full PRD in Markdown. Use headings, bullets, and clear sections. Do not include a roadmap section unless the user requested it.
"""
    if config.include_roadmap:
        user_content += "\nInclude a high-level Roadmap section at the end with phases/milestones.\n"

    # We send one user message with the full brief; Claude generates the PRD
    full_user = f"{system_instruction}\n\n---\n\n{user_content}"
    return full_user
