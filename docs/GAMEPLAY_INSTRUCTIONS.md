# Gameplay instructions (system prompts)

Presets live in [`gameplay/instructions/`](../gameplay/instructions/). Each Markdown file has YAML frontmatter:

```yaml
---
id: defense_only
title: Defense only (siege / break the wall)
behavior: defense_only
---
```

`behavior` drives the bot code. The Markdown body is the **system prompt** (also fed to `--llm` coaches).

## Built-in presets

| Id | Behavior | Idea |
|----|----------|------|
| `default` | `aggressive` | Normal sparring |
| `defense_only` | `defense_only` | Playbot walls up; human must attack and break in |

## Launch

```bash
./scripts/play_vs_playbot.sh --mode defense_only
./scripts/play_vs_playbot.sh --instructions defense_only --chaos
./scripts/play_vs_playbot.sh --mode /path/to/custom.md --llm claude
```

Env default: `SCPLAY_MODE=defense_only`.

## Custom modes

1. Copy `gameplay/instructions/defense_only.md`.
2. Change `id`, `title`, `behavior` (reuse `defense_only` or `aggressive` until new behaviors exist).
3. Write the rules in Markdown.
4. Launch with `--mode your_id` or `--mode /full/path/file.md`.

New `behavior` values need a matching branch in `PlaybotSparBot` (see `_defend_and_counter`).
