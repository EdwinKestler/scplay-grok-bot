#!/usr/bin/env bash
# Smoke-test OpenAI / Claude connectors using env API keys (does not print keys).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
# Prefer project venv, else agentsc2 venv, else system
if [[ -x .venv/bin/python ]]; then
  PY=.venv/bin/python
elif [[ -x /home/kestl/github/agentsc2/.venv/bin/python ]]; then
  PY=/home/kestl/github/agentsc2/.venv/bin/python
else
  PY=python3
fi
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
"$PY" - <<'PY'
import asyncio, os, sys
sys.path.insert(0, ".")
from scplay.llm import get_provider, list_providers
from scplay.llm.base import LLMMessage

async def main():
    print("providers:", ", ".join(list_providers()))
    for name in list_providers():
        p = get_provider(name)
        configured = p.is_configured()
        print(f"\n== {name} configured={configured}")
        if not configured:
            print(" ", p.missing_key_hint())
            continue
        resp = await p.chat(
            [LLMMessage("user", "Reply with exactly: pong")],
            temperature=0,
            max_tokens=16,
        )
        if resp.ok:
            print(f"  ok model={resp.model} latency_ms={resp.latency_ms:.0f} text={resp.text!r}")
        else:
            print(f"  FAIL: {resp.error}")

asyncio.run(main())
# Never echo keys
for k in ("OPENAI_API_KEY", "CLAUDE_API_KEY", "ANTHROPIC_API_KEY"):
    v = os.environ.get(k, "")
    print(f"{k}: {'set ('+str(len(v))+' chars)' if v else 'not set'}")
PY
