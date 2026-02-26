"""Prompt strategies: pluggable ways to build PRD prompts."""
from services.prompt_builder.strategies.base import PromptStrategy
from services.prompt_builder.strategies.default import DefaultStrategy

# Registry for builder to resolve strategy_id -> strategy instance
STRATEGIES: dict[str, PromptStrategy] = {
    DefaultStrategy.strategy_id: DefaultStrategy(),
}


def get_strategy(strategy_id: str) -> PromptStrategy:
    """Return strategy by id; falls back to default if unknown."""
    return STRATEGIES.get(strategy_id) or STRATEGIES["default"]
