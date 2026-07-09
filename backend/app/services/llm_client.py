"""
Thin wrapper around LLM providers for AI-generated enforcement letters and
weekly report narratives (workstream C).

Tries providers in order and returns which one actually produced the text,
so callers can record an honest generated_by/narrative_source instead of
assuming a fixed provider name:

  1. Claude (ANTHROPIC_API_KEY) -- preferred if configured.
  2. Groq (GROQ_API_KEY) -- free-tier fallback (OpenAI-compatible REST API,
     called directly via httpx rather than adding another SDK dependency).
  3. None -- caller must fall back to its own deterministic
     template/rule-based generator.

Every key is read from the environment at call time (not import time), so
whichever one is actually configured activates immediately -- no code
changes needed, same pattern as the proxy pools.
"""
from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)

DEFAULT_CLAUDE_MODEL = "claude-sonnet-5"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

_claude_client = None
_claude_client_checked = False


def is_available() -> bool:
    return _get_claude_client() is not None or bool(os.getenv("GROQ_API_KEY"))


def _get_claude_client():
    global _claude_client, _claude_client_checked
    if _claude_client_checked:
        return _claude_client
    _claude_client_checked = True

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic

        _claude_client = anthropic.Anthropic(api_key=api_key)
    except Exception:
        logger.exception("Failed to initialize Anthropic client; trying next provider.")
        _claude_client = None

    return _claude_client


def _generate_with_claude(system_prompt: str, user_prompt: str, max_tokens: int) -> str | None:
    client = _get_claude_client()
    if client is None:
        return None

    try:
        response = client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", DEFAULT_CLAUDE_MODEL),
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text").strip()
        return text or None
    except Exception:
        logger.exception("Claude generation failed; trying next provider.")
        return None


def _generate_with_groq(system_prompt: str, user_prompt: str, max_tokens: int) -> str | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    try:
        response = httpx.post(
            GROQ_CHAT_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": max_tokens,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        text = response.json()["choices"][0]["message"]["content"].strip()
        return text or None
    except Exception:
        logger.exception("Groq generation failed; falling back to template/rule-based output.")
        return None


def generate_text(system_prompt: str, user_prompt: str, *, max_tokens: int = 1024) -> tuple[str, str] | None:
    """
    Returns (text, provider_name) from the first provider that succeeds, or
    None if every configured provider is unavailable/errors -- callers must
    fall back to their own template/rule-based output in that case.
    """
    text = _generate_with_claude(system_prompt, user_prompt, max_tokens)
    if text is not None:
        return text, "claude"

    text = _generate_with_groq(system_prompt, user_prompt, max_tokens)
    if text is not None:
        return text, "groq"

    return None
