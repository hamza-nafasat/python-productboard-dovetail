"""
Default prompt strategy: professional PRD prompt with standard sections.

Sections: problem, goals, user personas, requirements, metrics, risks, rollout.
Suitable for any LLM; no vendor-specific instructions.
"""
from __future__ import annotations

from services.prompt_builder.models import (
    NormalizedFeedback,
    NormalizedInsights,
    PromptBuilderConfig,
)
from services.prompt_builder.strategies.base import PromptStrategy


# Section names for metadata and future versioning
DEFAULT_SECTIONS = [
    "problem",
    "goals",
    "user_personas",
    "requirements",
    "metrics",
    "risks",
    "rollout",
]


class DefaultStrategy(PromptStrategy):
    """
    Builds a structured PRD generation prompt with: problem, goals,
    user personas, requirements, metrics, risks, rollout.
    """

    strategy_id = "default"
    sections = list(DEFAULT_SECTIONS)

    def build(
        self,
        insights: NormalizedInsights,
        feedback: NormalizedFeedback,
        config: PromptBuilderConfig,
    ) -> str:
        context = config.product_context or "General product."
        goals = config.business_goals or "To be defined."
        constraints = config.constraints or "None specified."
        audience = config.audience_type.replace("_", " ").title()
        tone = config.output_tone.replace("_", " ").title()

        instruction = (
            "You are an expert product manager. Write a complete, production-ready "
            "Product Requirements Document (PRD) in Markdown.\n\n"
            "Guidelines:\n"
            f"- Audience: {audience}. Use a {tone} tone.\n"
            "- Be specific and actionable. Include clear success criteria where relevant.\n"
            "- Structure with clear headings (##, ###). Use bullet lists for requirements.\n"
            "- Base the content on the research and feedback data provided below; do not invent data.\n"
            "- Output only the PRD Markdown, no meta-commentary.\n\n"
            "Include these sections: Problem statement, Goals, User personas, "
            "Requirements, Success metrics, Risks and mitigations, Rollout plan."
        )
        if config.include_roadmap:
            instruction += " Include a high-level Roadmap section at the end with phases and milestones."

        user_content = (
            "Use this context to write the PRD:\n\n"
            "**Product context (problem space)**\n"
            f"{context}\n\n"
            "**Business goals**\n"
            f"{goals}\n\n"
            "**Constraints**\n"
            f"{constraints}\n\n"
            "**User research (Dovetail)**\n"
            f"{insights.summary_text}\n\n"
            "**Product feedback (Productboard)**\n"
            f"{feedback.summary_text}\n\n"
            "Generate the full PRD in Markdown with the sections listed above. "
            "Use headings, bullets, and clear sections."
        )
        return f"{instruction}\n\n---\n\n{user_content}"
