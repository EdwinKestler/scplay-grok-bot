from __future__ import annotations

import json
import os
import time
from typing import Any
from urllib import error, request

from scplay.llm.base import LLMMessage, LLMProvider, LLMResponse

DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
API_URL = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1/chat/completions")


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "").strip()

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def missing_key_hint(self) -> str:
        return "Export OPENAI_API_KEY in your environment (never commit the key)."

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
            return LLMResponse(text="", provider=self.name, model=model, error="OPENAI_API_KEY not set")

        payload: dict[str, Any] = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            API_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        t0 = time.perf_counter()
        try:
            # stdlib call in a thread would be nicer; keep deps light for now
            import asyncio

            def _do() -> dict[str, Any]:
                with request.urlopen(req, timeout=60) as resp:
                    return json.loads(resp.read().decode("utf-8"))

            body = await asyncio.to_thread(_do)
            latency = (time.perf_counter() - t0) * 1000
            text = body["choices"][0]["message"]["content"].strip()
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
