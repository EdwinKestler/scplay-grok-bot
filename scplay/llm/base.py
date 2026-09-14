from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMMessage:
    role: str  # system | user | assistant
    content: str


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str
    raw: dict[str, Any] = field(default_factory=dict)
    latency_ms: float | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and bool(self.text.strip())


class LLMProvider(ABC):
    """Minimal chat-completions style interface for evaluation + in-game use."""

    name: str = "base"

    @abstractmethod
    def is_configured(self) -> bool:
        """True if required API key env vars are present (does not call the network)."""

    @abstractmethod
    async def chat(
        self,
        messages: list[LLMMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 256,
    ) -> LLMResponse:
        ...

    def missing_key_hint(self) -> str:
        return f"Set the API key env var for provider '{self.name}' (see docs/LLM_CONNECTORS.md)."
