"""
Prompt builder: modular service to produce structured PRD generation prompts.

Public API:
- build_prompt(...)       : raw insight/feedback dicts -> PromptResult
- build_prompt_from_summaries(...) : pre-aggregated text -> PromptResult

No Streamlit, FastAPI, or API client imports; safe to use from pipeline or API.
"""
from services.prompt_builder.builder import build_prompt, build_prompt_from_summaries
from services.prompt_builder.models import (
    FeedbackItem,
    InsightItem,
    NormalizedFeedback,
    NormalizedInsights,
    PromptBuilderConfig,
    PromptResult,
)
from services.prompt_builder.strategies import get_strategy
from services.prompt_builder.strategies.base import PromptStrategy

__all__ = [
    "build_prompt",
    "build_prompt_from_summaries",
    "PromptResult",
    "PromptBuilderConfig",
    "NormalizedInsights",
    "NormalizedFeedback",
    "InsightItem",
    "FeedbackItem",
    "PromptStrategy",
    "get_strategy",
]
