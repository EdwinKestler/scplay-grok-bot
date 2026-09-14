# Gameplay instructions (mode prompts)

Play modes are **system prompts + behavior flags**. They tell Playbot *how* to play and (when `--llm` is set) constrain the coach model.

## Where they live

```
gameplay/instructions/
  default.md
  defense_only.md
  <your_mode>.md
```

## File format

```yaml
---
id: defense_only
title: Defense only (siege / break the wall)
behavior: defense_only   # drives bot code: aggressive | defense_only | …
---

# Markdown body = system prompt
…
```

| Field | Purpose |
|-------|---------|
| `id` | CLI `--mode <id>` |
| `title` | Human-readable name (logs + chat) |
| `behavior` | Code path in `PlaybotSparBot` |
| body | Full instruction text / LLM system prompt |

## Launch

```bash
./scripts/play_vs_playbot.sh --mode default
./scripts/play_vs_playbot.sh --mode defense_only
./scripts/play_vs_playbot.sh --mode defense_only --chaos
./scripts/play_vs_playbot.sh --mode defense_only --llm claude
./scripts/play_vs_playbot.sh --instructions /path/to/custom.md
```

Env: `SCPLAY_MODE=defense_only`

Match metadata records `notes.gameplay_mode` and `notes.gameplay_behavior` in `logs/matches/<id>/match.json`.

---

## Built-in mode prompts

### `default` — Standard sparring

**Behavior:** `aggressive`

```
Play a normal 1v1. Harass, expand, and attack when you have an army advantage.
Human and Playbot both play full offense/defense as usual.
```

### `defense_only` — Siege / break the wall

**Behavior:** `defense_only`

```
## Roles
- Playbot (Zerg): Defense only. Do not attack the human's base or take map
  control offensively.
- Human: Must play offensively. Break Playbot's defenses and kill hatcheries /
  win by assault.

## Playbot rules
1. Fortify the main and natural (spines, queens, ling wall / hold near bases).
2. Never send a proactive attack wave to the enemy start location.
3. When enemy units enter your territory (near townhalls), counter them locally
   — fight, then return to defensive posts.
4. Keep producing defensive army and static defense; expand only to stabilize
   eco if needed.
5. Trash-talk like a wall: dare the human to break in; call out incoming pushes.

## Win conditions
- Playbot wins if the human army is crushed while assaulting, or the siege fails.
- Human wins by breaking the defense and destroying Playbot's bases.
```

**Code effects:** spines near hatcheries, extra queens, garrison lings, `_defend_and_counter` instead of attacking the enemy base.

---

## Authoring a new mode

1. Copy `gameplay/instructions/defense_only.md`.
2. Set new `id` / `title`.
3. Reuse an existing `behavior` **or** add a new branch in `examples/play_vs_playbot.py`.
4. Write clear roles, rules, and win conditions in the Markdown body.
5. Run with `--mode your_id` and check `match.json` notes.

### Prompt-writing tips (for LLM eval)

- Separate **roles**, **hard rules**, and **soft style** (banter).
- State win conditions explicitly so post-match graders can score compliance.
- Keep rules testable from logs (`defense_counter` events, no march to enemy start).

## Compliance signals in logs

| Signal | Where |
|--------|--------|
| Mode id / behavior | `match.json` → `notes` |
| Counter-only fights | `play.jsonl` → `defense_counter` |
| Opening mode announce | `chat.jsonl` |
| LLM banter under mode | `play.jsonl` → `llm_banter` + chat |
