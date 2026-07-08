"""
Thin wrapper around the Anthropic API for AI-generated enforcement letters
and weekly report narratives (workstream C).

Reads ANTHROPIC_API_KEY from the environment at call time (not at import
time), so real generation activates the moment the key is added -- no code
changes needed, same pattern as the ISP proxy pools. Every call site must
treat None as "fall back to the deterministic template/rule-based
generator," never crash the request on a missing key or API error.
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-5"

_client = None
_client_checked = False


def is_available() -> bool:
    return _get_client() is not None


def _get_client():
    global _client, _client_checked
    if _client_checked:
        return _client
    _client_checked = True

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.info("ANTHROPIC_API_KEY not set; Claude-generated content disabled (falling back to templates).")
        return None

    try:
        import anthropic

        _client = anthropic.Anthropic(api_key=api_key)
    except Exception:
        logger.exception("Failed to initialize Anthropic client; falling back to templates.")
        _client = None

    return _client


def generate_text(system_prompt: str, user_prompt: str, *, max_tokens: int = 1024) -> str | None:
    """Returns generated text, or None if Claude is unavailable/errors -- callers must fall back."""
    client = _get_client()
    if client is None:
        return None

    try:
        response = client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL),
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text").strip()
        return text or None
    except Exception:
        logger.exception("Claude generation failed; falling back to template/rule-based output.")
        return None
