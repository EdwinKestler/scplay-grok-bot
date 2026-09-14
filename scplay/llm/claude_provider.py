from __future__ import annotations

import json
import os
import time
from typing import Any
from urllib import error, request

from scplay.llm.base import LLMMessage, LLMProvider, LLMResponse

# User asked for CLAUDE_API_KEY; also accept Anthropic's usual name as fallback.
DEFAULT_MODEL = os.environ.get("CLAUDE_MODEL", os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"))
API_URL = os.environ.get("ANTHROPIC_API_BASE", "https://api.anthropic.com/v1/messages")
API_VERSION = os.environ.get("ANTHROPIC_VERSION", "2023-06-01")


class ClaudeProvider(LLMProvider):
    name = "claude"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = (
            api_key
            or os.environ.get("CLAUDE_API_KEY", "").strip()
            or os.environ.get("ANTHROPIC_API_KEY", "").strip()
        )

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def missing_key_hint(self) -> str:
        return "Export CLAUDE_API_KEY (or ANTHROPIC_API_KEY) in your environment (never commit the key)."

    async def chat(
        self,
        messages: list[LLMMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 256,
    ) -> LLMResponse:
        model = model or DEFAULT_MODEL
        if not self.api_key:
            return LLMResponse(text="", provider=self.name, model=model, error="CLAUDE_API_KEY not set")

        system = ""
        converted: list[dict[str, str]] = []
        for m in messages:
            if m.role == "system":
                system = (system + "\n" + m.content).strip() if system else m.content
            else:
                # Anthropic only allows user/assistant in messages list
                role = m.role if m.role in ("user", "assistant") else "user"
                converted.append({"role": role, "content": m.content})

        if not converted:
            converted = [{"role": "user", "content": "Say glhf in one short SC2 trash-talk line."}]

        payload: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": converted,
        }
        if system:
            payload["system"] = system

        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            API_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": API_VERSION,
            },
            method="POST",
        )
        t0 = time.perf_counter()
        try:
            import asyncio

            def _do() -> dict[str, Any]:
                with request.urlopen(req, timeout=60) as resp:
                    return json.loads(resp.read().decode("utf-8"))

            body = await asyncio.to_thread(_do)
            latency = (time.perf_counter() - t0) * 1000
            parts = body.get("content") or []
            text = "".join(p.get("text", "") for p in parts if p.get("type") == "text").strip()
            return LLMResponse(text=text, provider=self.name, model=model, raw=body, latency_ms=latency)
        except error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            return LLMResponse(
                text="",
                provider=self.name,
                model=model,
                error=f"HTTP {e.code}: {err_body[:500]}",
                latency_ms=(time.perf_counter() - t0) * 1000,
            )
        except Exception as e:  # noqa: BLE001
            return LLMResponse(
                text="",
                provider=self.name,
                model=model,
                error=str(e),
                latency_ms=(time.perf_counter() - t0) * 1000,
            )
