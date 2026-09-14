# LLM connectors (OpenAI + Claude)

Plug other AI assistants into scplay-grok-bot for **in-game banter** and **post-match evaluation**. Keys stay in environment variables — never in git.

## Env vars

| Variable | Provider |
|----------|----------|
| `OPENAI_API_KEY` | OpenAI |
| `CLAUDE_API_KEY` | Claude (Anthropic). `ANTHROPIC_API_KEY` also accepted |
| `OPENAI_MODEL` | optional, default `gpt-4o-mini` |
| `CLAUDE_MODEL` | optional, default `claude-sonnet-4-20250514` |

```bash
export OPENAI_API_KEY=sk-...
export CLAUDE_API_KEY=sk-ant-...
```

Or copy `.env.example` → `.env` and load it yourself (`set -a; source .env; set +a`).

## Smoke test

```bash
./scripts/probe_llm.sh
```

Prints whether each provider is configured and sends a tiny ping (does **not** print key values).

## Play with an LLM coach (banter)

```bash
./scripts/play_vs_playbot.sh --llm openai
./scripts/play_vs_playbot.sh --llm claude --chaos --fast
```

When `--llm` is set, Playbot periodically asks that provider for a short chat line from the live game summary. Scripted banter remains the fallback if the API fails.

Match metadata records `llm_provider` / `llm_model` for evaluation.

## Evaluate a finished match

```bash
./scripts/eval_match_with_llm.sh openai logs/matches/<match_id>/chat.txt
./scripts/eval_match_with_llm.sh claude logs/matches/<match_id>/chat.jsonl
```

Writes `eval_openai.txt` / `eval_claude.txt` next to the chat log.

## Code layout

- `scplay/llm/openai_provider.py` — OpenAI Chat Completions
- `scplay/llm/claude_provider.py` — Anthropic Messages API
- `scplay/llm/factory.py` — `get_provider("openai"|"claude")`
- `scplay/llm/coach.py` — banter + eval prompts

Stdlib HTTP only (no extra pip deps required for connectors).
