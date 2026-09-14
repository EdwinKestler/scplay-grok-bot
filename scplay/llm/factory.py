from __future__ import annotations

from scplay.llm.base import LLMProvider
from scplay.llm.claude_provider import ClaudeProvider
from scplay.llm.openai_provider import OpenAIProvider

_REGISTRY: dict[str, type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "claude": ClaudeProvider,
}


def list_providers() -> list[str]:
    return sorted(_REGISTRY)


def get_provider(name: str) -> LLMProvider:
    key = name.strip().lower()
    if key in ("anthropic", "claude"):
        key = "claude"
    if key not in _REGISTRY:
        raise ValueError(f"Unknown LLM provider {name!r}. Choose from: {', '.join(list_providers())}")
    return _REGISTRY[key]()
