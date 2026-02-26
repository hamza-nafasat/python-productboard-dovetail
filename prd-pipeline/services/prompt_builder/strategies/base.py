"""
Abstract base for prompt strategies.

Strategies define how to turn normalized insights + feedback + config
into a single PRD generation prompt. Add new strategies here (e.g.
strategies/concise.py) and register in builder for extensibility.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from services.prompt_builder.models import (
    NormalizedFeedback,
    NormalizedInsights,
    PromptBuilderConfig,
)


class PromptStrategy(ABC):
    """Base class for PRD prompt generation strategies."""

    strategy_id: str = "base"
    """Unique id for this strategy; used in metadata and selection."""

    sections: list[str] = []
    """Section names this strategy includes (e.g. problem, goals, personas)."""

    @abstractmethod
    def build(
        self,
        insights: NormalizedInsights,
        feedback: NormalizedFeedback,
        config: PromptBuilderConfig,
    ) -> str:
        """
        Build the full prompt string. No side effects; pure function of inputs.
        """
        ...
