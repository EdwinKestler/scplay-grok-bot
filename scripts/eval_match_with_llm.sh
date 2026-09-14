#!/usr/bin/env bash
# Evaluate a match chat log with openai or claude.
# Usage: ./scripts/eval_match_with_llm.sh openai logs/matches/<id>/chat.txt
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROVIDER="${1:?provider openai|claude}"
CHAT_FILE="${2:?path to chat.txt or chat.jsonl}"
cd "$ROOT"
if [[ -x .venv/bin/python ]]; then PY=.venv/bin/python
elif [[ -x /home/kestl/github/agentsc2/.venv/bin/python ]]; then PY=/home/kestl/github/agentsc2/.venv/bin/python
else PY=python3; fi
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
"$PY" - <<PY
import asyncio, json, sys
from pathlib import Path
sys.path.insert(0, ".")
from scplay.llm import get_provider
from scplay.llm.coach import evaluate_match_chat

provider_name = ${PROVIDER@Q}
path = Path(${CHAT_FILE@Q})
text = path.read_text(encoding="utf-8")
if path.suffix == ".jsonl":
    lines = []
    for line in text.splitlines():
        if not line.strip():
            continue
        o = json.loads(line)
        lines.append(f"t={o.get('game_time')} [{o.get('speaker')}] {o.get('message')}")
    text = "\\n".join(lines)

async def main():
    p = get_provider(provider_name)
    if not p.is_configured():
        print(p.missing_key_hint()); sys.exit(2)
    resp = await evaluate_match_chat(p, text)
    out = path.with_name(f"eval_{provider_name}.txt")
    if resp.ok:
        out.write_text(resp.text + "\\n", encoding="utf-8")
        print(resp.text)
        print(f"\\nWrote {out}")
    else:
        print("ERROR:", resp.error); sys.exit(1)

asyncio.run(main())
PY
