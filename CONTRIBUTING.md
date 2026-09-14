# Contributing

## Dev setup

```bash
./scripts/setup_venv.sh
./scripts/find_sc2.sh
./scripts/install_maps.sh   # needs SC2 installed via Proton/Wine
```

## Useful commands

| Command | Purpose |
|---------|---------|
| `./scripts/play_vs_playbot.sh` | Human vs Playbot |
| `./scripts/play_vs_playbot.sh --chaos --fast` | Arcade mode |
| `./scripts/play_vs_playbot.sh --llm openai` | OpenAI-coached banter |
| `./scripts/play_vs_playbot.sh --llm claude` | Claude-coached banter |
| `./scripts/probe_llm.sh` | Check API keys without printing them |
| `./scripts/export_logs_for_training.sh` | Bundle JSONL logs |
| `./scripts/eval_match_with_llm.sh openai path/to/chat.txt` | Post-match eval |

## Secrets

Never commit `.env` or API keys. Use `OPENAI_API_KEY` / `CLAUDE_API_KEY` in the environment. See `.env.example`.

## Captures & logs

- Screenshots: `captures/screenshots/`
- Gameplay video: `captures/gameplay/` (gitignored by default)
- Match DB: `logs/matches/<id>/`

## PRs

Keep changes focused. Update `README.md` / `docs/` when behavior or flags change.
