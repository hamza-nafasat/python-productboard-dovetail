"""Anthropic Claude API client (async). Used via app.run_async."""
import logging
from typing import Optional

from anthropic import AsyncAnthropic

from app.config import DEFAULT_CLAUDE_MODEL, DEFAULT_MAX_TOKENS

logger = logging.getLogger(__name__)


async def generate_prd(
    prompt: str,
    api_key: str,
    model: str = DEFAULT_CLAUDE_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """
    Call Claude to generate PRD text. Async; run via run_async.run_async() from Streamlit.
    """
    if not api_key or not api_key.strip():
        raise ValueError("Anthropic API key is empty")
    client = AsyncAnthropic(api_key=api_key.strip())
    response = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    text = ""
    for block in response.content:
        if hasattr(block, "text"):
            text += block.text
    return text.strip()


async def test_connection(api_key: str) -> tuple[bool, str]:
    """Test Anthropic API with a minimal message. Returns (success, error_message)."""
    if not api_key or not api_key.strip():
        return False, "API key is empty"
    try:
        client = AsyncAnthropic(api_key=api_key.strip())
        await client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say OK"}],
        )
        return True, ""
    except Exception as e:
        return False, str(e)


async def regenerate_section(
    section_content: str,
    context: str,
    api_key: str,
    model: str = DEFAULT_CLAUDE_MODEL,
    max_tokens: int = 2048,
) -> str:
    """Regenerate a single PRD section given section text and surrounding context."""
    if not api_key or not api_key.strip():
        raise ValueError("Anthropic API key is empty")
    prompt = f"""You are editing a PRD. Below is the full context of the document, and a section that the user wants you to rewrite.

Context (surrounding sections):
{context}

Section to rewrite (output only this section, improved, in the same format):
{section_content}

Rewrite only the section above. Keep the same heading level and style. Output nothing else."""
    client = AsyncAnthropic(api_key=api_key.strip())
    response = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    text = ""
    for block in response.content:
        if hasattr(block, "text"):
            text += block.text
    return text.strip()
