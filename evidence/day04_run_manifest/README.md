# Day 4 evidence — Reproducible run manifest

**Date:** 2026-09-17 (America/Guatemala / box local)  
**Feature:** Per-run manifest with stable `config_fingerprint`, unique `run_id`,
git/package/SC2/map/prompt/provider metadata, and schema-v2 validation.

## Acceptance

Two launches with the same configuration produce the **same**
`config_fingerprint` while retaining **unique** `run_id`s.
Verified by `tests/test_run_manifest.py`.

## Command

```bash
pytest tests/test_run_manifest.py tests/test_schema_v2.py \
  tests/test_condition_registry.py tests/test_protocol_v1.py -v
```

## Result

See `pytest_output.txt` — **53 passed**.

## Artifacts

| Path | Role |
|------|------|
| `scplay/run_manifest.py` | Builder + fingerprint |
| `schemas/v2/run_manifest.schema.json` | Day 4 optional fields |
| `tests/test_run_manifest.py` | Acceptance tests |
| `tests/fixtures/manifests/example_run_manifest.json` | Privacy-safe example |
| `docs/RUN_MANIFEST.md` | Fingerprint field list |

## Fingerprint fields

`map_name`, `map_checksum`, `controller_tier`, `controller_version`, `chaos`,
`realtime`, `mode`, `opponent`, `seed`, `analysis_intent`, `llm_provider`,
`prompt_hash`, `provider_model_snapshot`, `sc2_version`, `python_packages`,
`git_sha`, `git_dirty`, `parameters`, `timing_policy`.

Excluded: `run_id`, `started_at_utc`, `seq`, `game_loop`, envelope bookkeeping,
`notes`.

## Defaults chosen

- Controller version default: `PlaybotSparBot/1`
- Map checksum without file: sha256(`map_name + "\\0" + declared`)
- Git/package probes never fail hard (nulls / skip when injected)
- Schema: additive optional fields only (`additionalProperties: false` still)

## Follow-ups (not Day 4)

- Day 5: repository research validator
- Live MatchLogger still emits legacy v1 (optional thin hook deferred)
