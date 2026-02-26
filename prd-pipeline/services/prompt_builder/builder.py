"""
PromptBuilderService: normalize inputs -> select strategy -> build -> return PromptResult.

Orchestrates normalizer and strategy; does not fetch data or call external APIs.
Caller (pipeline or API) provides raw insights and feedback dicts plus config.
"""
from __future__ import annotations

from typing import Any

from services.prompt_builder.models import (
    NormalizedFeedback,
    NormalizedInsights,
    PromptBuilderConfig,
    PromptResult,
)
from services.prompt_builder.normalizer import normalize_feedback, normalize_insights
from services.prompt_builder.strategies import get_strategy


def build_prompt(
    *,
    dovetail_raw: list[dict[str, Any]],
    productboard_raw: list[dict[str, Any]],
    config: PromptBuilderConfig,
    strategy_id: str | None = None,
) -> PromptResult:
    """
    Build a PRD generation prompt from raw Dovetail/Productboard data and config.

    Flow: normalize and dedupe insights and feedback -> select strategy -> build
    prompt string -> return PromptResult with prompt and metadata.
    """
    insights = normalize_insights(dovetail_raw)
    feedback = normalize_feedback(productboard_raw)
    sid = strategy_id or config.prd_template_id or "default"
    strategy = get_strategy(sid)
    prompt_text = strategy.build(insights, feedback, config)
    word_count = len(prompt_text.split())
    return PromptResult(
        prompt=prompt_text,
        strategy_id=strategy.strategy_id,
        template_id=config.prd_template_id,
        word_count=word_count,
        sections=list(strategy.sections),
        template_version="1",
    )


def build_prompt_from_summaries(
    *,
    dovetail_summary: str,
    productboard_summary: str,
    config: PromptBuilderConfig,
    strategy_id: str | None = None,
) -> PromptResult:
    """
    Build prompt when caller has already aggregated text (e.g. pipeline summaries).
    No normalization step; summaries are used as single-item "insight" and "feedback".
    """
    # Represent as one insight and one feedback item so strategy can still run
    dovetail_raw = [{"title": "Research summary", "body": dovetail_summary or "No Dovetail data selected."}]
    productboard_raw = [{"title": "Feedback summary", "content": productboard_summary or "No Productboard data selected."}]
    return build_prompt(
        dovetail_raw=dovetail_raw,
        productboard_raw=productboard_raw,
        config=config,
        strategy_id=strategy_id,
    )
