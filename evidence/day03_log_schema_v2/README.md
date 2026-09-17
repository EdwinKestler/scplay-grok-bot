# Day 3 evidence — Log schema v2

**Date:** 2026-09-16 (America/Guatemala / box local)  
**Feature:** Versioned JSON Schemas (draft 2020-12) for run manifest, gameplay
events, chat events, snapshots, and LLM decisions, plus fixtures and
`scplay.schema_v2` validator.

## Acceptance

Every record has `schema_version`, `run_id`, `seq`, `game_loop`, `source`, and
`event_type`. Committed examples under `tests/fixtures/schema_v2/` validate.

## Command

```bash
pytest tests/test_schema_v2.py tests/test_condition_registry.py tests/test_protocol_v1.py -v
```

## Result

See `pytest_output.txt` — **41 passed**.

## Artifacts

| Path | Role |
|------|------|
| `schemas/v2/*.schema.json` | Draft 2020-12 schemas + envelope |
| `schemas/v2/README.md` | Envelope field list |
| `scplay/schema_v2.py` | `validate_record` / envelope helpers |
| `tests/fixtures/schema_v2/` | Valid examples, invalid fixture, `sample_run.jsonl` |
| `tests/test_schema_v2.py` | Validation tests |
| `docs/LOG_SCHEMA.md` | Human docs (v2 + legacy v1 note) |

## Defaults chosen

- Dialect: JSON Schema draft **2020-12** (`jsonschema` Draft202012Validator).
- `source` enum: `logger|bot|human|sc2|llm|system`.
- `event_type` for chat is `chat` (not `chat_event`) to keep the discriminator short.
- Type schemas set `additionalProperties: false`; envelope meta-schema allows extras.
- Live `MatchLogger` **not** rewritten (Day 4/6).

## Follow-ups (not Day 3)

- Day 4: real run manifests with fingerprints.
- Day 6: nonzero monotonic game-loop capture in live logger.
- Eventual MatchLogger migration to emit v2 envelope fields.
