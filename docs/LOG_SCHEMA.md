# Log schema

Canonical research contract for match telemetry. **Schema v2** is the target
shape for confirmatory analysis. Live `MatchLogger` (`scplay/match_logger.py`)
still writes **legacy schema 1.0** today; Day 4+ migrates emission.

Machine-readable schemas: [`schemas/v2/`](../schemas/v2/).  
Python helper: `scplay.schema_v2.validate_record`.  
Fixtures: [`tests/fixtures/schema_v2/`](../tests/fixtures/schema_v2/).

See also [`../logs/README.md`](../logs/README.md) for on-disk layout.

## Schema v2 envelope (required on every record)

| Field | Type | Notes |
|-------|------|-------|
| `schema_version` | string | Const `"2.0"` |
| `run_id` | string | Non-empty run key (replaces `match_id`; may equal legacy `match_id` format) |
| `seq` | integer ≥ 0 | Ordered sequence id within the run |
| `game_loop` | integer ≥ 0 | SC2 game-loop time |
| `source` | enum | `logger` \| `bot` \| `human` \| `sc2` \| `llm` \| `system` |
| `event_type` | string | Discriminator (see below) |

Optional exploratory: `game_time_s` (number ≥ 0).

JSON Schema dialect: **draft 2020-12**.

### Record types

| `event_type` | Schema | Purpose |
|--------------|--------|---------|
| `run_manifest` | `run_manifest.schema.json` | Run metadata (Day 4 fills fingerprints) |
| `gameplay_event` | `gameplay_event.schema.json` | Sparse named events + `data` |
| `chat` | `chat_event.schema.json` | Speaker + message (+ optional `player_id`) |
| `snapshot` | `snapshot.schema.json` | Periodic `bot` / `enemy` feature objects |
| `llm_decision` | `llm_decision.schema.json` | T2 macro / optional T1 banter decision trace |

### LLM decision statuses

`proposed` · `validated` · `applied` · `rejected` · `expired` · `failed`

`decision_kind`: `macro` \| `banter`

### Example (chat)

```json
{
  "schema_version": "2.0",
  "run_id": "20260916T165000Z_AbyssalReefLE_deadbeef",
  "seq": 2,
  "game_loop": 224,
  "game_time_s": 10.0,
  "source": "bot",
  "event_type": "chat",
  "speaker": "playbot",
  "message": "Playbot online — holding the line.",
  "player_id": 1,
  "logged_at_utc": "2026-09-16T16:50:10Z"
}
```

Validate fixtures:

```bash
pytest tests/test_schema_v2.py -v
```

## Legacy schema 1.0 (current live logger)

Until migration, `MatchLogger` writes:

- `match.json` with `match_id`, `schema_version: "1.0"`, map/result fields
- `chat.jsonl` / `play.jsonl` lines with `match_id`, `type`, `game_time`, `iteration`
  (often **without** `schema_version`, `run_id`, `seq`, or unified `event_type`)

PROTOCOL_V1 notes that today’s `match_id` stands in for `run_id` until v2
emission lands. Do not mix v1 and v2 lines in the same analytical dataset
without an explicit adapter.

## Goals

1. **Chat corpus** — reconstruct in-match dialogue (privacy: consent + redaction Days 12–13).
2. **Play traces** — coarse state over time for cloning / debugging.
3. **Run index** — filter by map, tier, result, chaos, date via manifests.

## Privacy

Logs may include whatever humans type in SC2 chat. Do not publish raw logs
without consent. Redact before sharing datasets. Fixtures use synthetic text only.
