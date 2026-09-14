# Research roadmap: LLM / agent strategy eval in SC2

**Goal:** Use scplay-grok-bot as a reproducible arena to test **reasoning and strategy** in LLMs and desktop agents (Grok Bot, OpenAI, Claude, …), against humans and against each other — with logs suitable for scoring and training.

## Why SC2 (this stack)

- Real-time strategy forces planning under uncertainty (fog, timing, multitasking).
- Human-vs-bot and bot-vs-bot both fit the same `burnysc2` + Proton Ubuntu path.
- Structured **chat + play JSONL** already capture dialogue and coarse state.
- **Gameplay instruction prompts** give controllable experimental conditions (e.g. defense_only).

## Research questions

1. **Instruction following** — Does the agent obey mode prompts (e.g. never leave base in `defense_only`)?
2. **Tactical adaptation** — How quickly does it counter novel human builds?
3. **Strategic coherence** — Economy vs army vs tech under pressure.
4. **Language ↔ action** — Does in-game chat match what the agent actually does?
5. **Cross-model comparison** — OpenAI vs Claude vs Grok Bot under identical prompts/maps.
6. **Human baseline** — Same human, same mode, different AI opponents.

## Experimental conditions (matrix)

| Factor | Levels (v1) |
|--------|-------------|
| Opponent | Human · OpenAI coach · Claude coach · scripted Playbot (no LLM) · Grok Bot-assisted |
| Mode prompt | `default` · `defense_only` · (later: `harass_only`, `eco_first`, custom) |
| Map | AbyssalReefLE · +1 ladder map |
| Resources | Normal · `--chaos` |
| Speed | Realtime · `--fast` |
| Seed / race | Terran human vs Zerg bot (fixed for v1) |

Each cell: **N ≥ 3** matches when possible; always store `match_id` + full logs.

## Comparison protocols

### A. Human vs AI (primary)

1. Fix mode + map + chaos flag.
2. Human plays the same role each time (e.g. attacker in `defense_only`).
3. Rotate AI condition: scripted / `--llm openai` / `--llm claude` / Grok Bot session notes.
4. Score with the rubric below + human self-report (fun, fairness, difficulty 1–5).

### B. OpenAI vs Claude (coach / banter layer)

Same scripted micro (`PlaybotSparBot`); only the **LLM coach** differs (`--llm`). Isolates language + high-level suggestions if/when coach output starts steering builds (v2).

### C. Agent vs agent (future)

Two API-driven bots or two desktop agents in one match (or mirror matches). Requires a second bot slot or shared-ladder runner — see milestones.

## Scoring rubric (v1 — log-gradable)

| Axis | 0–2 score | Evidence |
|------|-----------|----------|
| Instruction compliance | Violates / mixed / clean | Mode rules vs `play.jsonl` / chat |
| Defense integrity (defense_only) | Collapses early / holds mid / holds late | Snapshots: townhalls, army, threats |
| Counter quality | Ignores push / reacts / efficient hold | `defense_counter` timing vs threat spikes |
| Chat relevance | Spam / generic / situational | Unique chat lines vs events |
| Outcome | Loss / close / win | `match.json` result + duration |

Optional LLM judge: `./scripts/eval_match_with_llm.sh openai|claude path/to/chat.txt` (blind to which model played when possible).

## Data products

Per match (already):

- `match.json`, `chat.jsonl`, `chat.txt`, `play.jsonl`
- `logs/index.jsonl` catalog

Aggregates:

```bash
./scripts/export_logs_for_training.sh
```

Planned:

- `logs/export/leaderboard.csv` — scored rubric rows
- Redacted public dataset subset (consent + no API keys)

## Milestones

### M0 — Platform (done / in progress)

- [x] Human vs Playbot on Ubuntu Proton
- [x] Live chat + MatchLogger JSONL
- [x] OpenAI / Claude connectors + probe/eval scripts
- [x] Gameplay instruction presets (`default`, `defense_only`)
- [ ] Banter de-dupe / anti-spam
- [ ] GitHub Pages project site

### M1 — Controlled human baselines (near-term)

- [ ] Freeze v1 rubric + scoring sheet template in repo
- [ ] Run 3× human vs scripted on `defense_only` (normal + chaos)
- [ ] Run 3× human vs `--llm openai` and 3× vs `--llm claude` same mode
- [ ] Publish anonymized summary table on the project site

### M2 — Stronger LLM influence

- [ ] Let LLM coach propose build/tech choices (parsed actions), not only banter
- [ ] Log `llm_decision` events (prompt, response, applied/rejected)
- [ ] Ablation: banter-only vs decision-capable coach

### M3 — Cross-agent & multi-model ladder

- [ ] Bot-vs-bot runner (OpenAI-policy vs Claude-policy)
- [ ] Desktop-agent protocol (Grok Bot / others) with shared instruction packs
- [ ] Public “mode pack” challenges (community-authored `.md` prompts)

### M4 — Learning from logs

- [ ] Train/evaluate small models on chat+snapshot traces
- [ ] Automatic compliance classifiers for mode prompts
- [ ] Open benchmark card (dataset card + eval harness)

## Ethics & safety

- Do not publish raw human chat without consent.
- Never commit API keys; use env vars only.
- Label chaos / cheat matches clearly in datasets.
- SC2 © Blizzard; respect AI/ML map-pack license terms.

## How to contribute an experiment

1. Open an issue titled `experiment: <name>`.
2. State matrix cells, N, and scoring.
3. Attach `match_id`s under `logs/matches/` (or export bundle).
4. PR updates to this roadmap’s results table (below).

## Results log (fill as you run)

| Date | Condition | Mode | N | Human W–L | Notes |
|------|-----------|------|---|-----------|-------|
| 2026-09-14 | scripted chaos | defense_only | 1 | 1–0 | match `…a4216909`; wall fell ~22m |
| | | | | | |
