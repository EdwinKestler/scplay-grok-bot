from __future__ import annotations

from scplay.llm.base import LLMMessage, LLMProvider, LLMResponse

SYSTEM_BANTER = """You are Playbot, a cocky but friendly StarCraft II Zerg sparring partner.
Reply with ONE short in-game chat line (max 18 words). No quotes, no markdown, no emojis overload.
Be specific to the game state if useful. Stay PG-13."""


async def banter_line(provider: LLMProvider, game_summary: str, *, model: str | None = None) -> LLMResponse:
    messages = [
        LLMMessage("system", SYSTEM_BANTER),
        LLMMessage("user", f"Game state:\n{game_summary}\n\nGive one chat line."),
    ]
    return await provider.chat(messages, model=model, temperature=0.9, max_tokens=64)


SYSTEM_EVAL = """You are evaluating an SC2 sparring bot transcript.
Be concise. Return plain text with: strengths, weaknesses, one concrete improvement."""


async def evaluate_match_chat(
    provider: LLMProvider,
    chat_transcript: str,
    *,
    model: str | None = None,
) -> LLMResponse:
    messages = [
        LLMMessage("system", SYSTEM_EVAL),
        LLMMessage("user", chat_transcript[:12000]),
    ]
    return await provider.chat(messages, model=model, temperature=0.3, max_tokens=400)
