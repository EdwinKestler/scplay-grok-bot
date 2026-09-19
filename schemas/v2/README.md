# Log schema v2 (research contract)

JSON Schema **draft 2020-12**. Every record — run manifest, gameplay event, chat,
snapshot, and LLM decision — shares a common **envelope**. Live `MatchLogger`
still emits legacy schema 1.0; Day 3 freezes the v2 contract + fixtures +
validator. Day 4 fills real manifests; Day 6 corrects game-loop capture.

## Envelope (required on every record)

| Field | Type | Meaning |
|-------|------|---------|
| `schema_version` | string const `"2.0"` | Schema major.minor |
| `run_id` | non-empty string | Replaces `match_id` as the run key (may reuse legacy `match_id` format) |
| `seq` | integer ≥ 0 | Ordered sequence id within the run (monotonic in examples) |
| `game_loop` | integer ≥ 0 | SC2 game-loop time (prefer this over wall clock) |
| `source` | enum | Who produced the record |
| `event_type` | string | Discriminator selecting which schema applies |

### Allowed `source` values

`logger` · `bot` · `human` · `sc2` · `llm` · `system`

### Allowed `event_type` values (v2)

| `event_type` | Schema file |
|--------------|-------------|
| `run_manifest` | `run_manifest.schema.json` |
| `gameplay_event` | `gameplay_event.schema.json` |
| `chat` | `chat_event.schema.json` |
| `snapshot` | `snapshot.schema.json` |
| `llm_decision` | `llm_decision.schema.json` |

Optional exploratory field on any record: `game_time_s` (number ≥ 0), wall-ish
seconds derived from game loops for human readability.

## Python helper

`scplay.schema_v2.validate_record(obj)` loads the matching schema from this
directory and validates with `jsonschema` Draft 2020-12.

## Fixtures

See `tests/fixtures/schema_v2/` for one valid example per type plus a mixed
`sample_run.jsonl`.

## Day 4 optional run_manifest fields

In addition to Day 3 required/optional fields, `run_manifest.schema.json` allows:

| Field | Type | Notes |
|-------|------|-------|
| `map_checksum` | string\|null | sha256 of map bytes or name+declared |
| `controller_version` | string\|null | e.g. `PlaybotSparBot/1` |
| `provider_model_snapshot` | string\|object\|null | No secrets |
| `parameters` | object\|null | Canonical parameter bag |
| `timing_policy` | object\|null | e.g. decision cadence |

Builder: `scplay.run_manifest.build_run_manifest`. Fingerprint docs:
[`docs/RUN_MANIFEST.md`](../../docs/RUN_MANIFEST.md).

