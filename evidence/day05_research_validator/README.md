# Day 5 evidence — Repository research validator

**Date:** 2026-09-19 (America/Guatemala / box local)  
**Feature:** One local command validating schemas, manifests, conditions,
JSONL records, privacy heuristics, and run-bundle required artifacts.

## Acceptance

Exits **nonzero** with **actionable errors** for malformed, incomplete, or
privacy-unsafe fixtures. Verified by `tests/test_research_validator.py` and
CLI captures below.

## Commands

```bash
python scripts/validate_research.py tests/fixtures/validator/clean_bundle
python scripts/validate_research.py tests/fixtures/validator/privacy_unsafe
pytest tests/ -v
```

## Result

See `pytest_output.txt` — **68 passed** (Days 1–4 green + Day 5).

| Capture | Role |
|---------|------|
| `clean_validation.txt` | Clean fixture → exit 0 |
| `expected_failure.txt` | Privacy-unsafe fixture → exit 1, actionable codes |
| `pytest_output.txt` | Full suite |

## Artifacts

| Path | Role |
|------|------|
| `scplay/research_validator.py` | Library + `main()` CLI |
| `scripts/validate_research.py` | Script entry |
| `tests/test_research_validator.py` | Acceptance tests |
| `tests/fixtures/validator/` | clean / bad_schema / privacy_unsafe / incomplete |
| `docs/RESEARCH_VALIDATOR.md` | How to run, checks, privacy heuristics, exit codes |

## Run-bundle checklist

1. `run_manifest.json` or `manifest.json`
2. At least one events JSONL (`events.jsonl`, `records.jsonl`,
   `gameplay_events.jsonl`, or `*.events.jsonl`)
3. Optional `condition.json` validated via condition registry

## Privacy heuristics (summary)

- `sk-` + ≥20 token chars; `OPENAI_API_KEY=`; `ANTHROPIC_API_KEY=`; `Bearer ` + long token
- `/home/<user>/...` and `C:\Users\<user>\...` (synthetic `/path/to/SC2` allowed)

## Defaults chosen

- Bundle detection: manifest and/or events present, or directory name contains `bundle`
- Privacy on by default; `--no-privacy` available for debugging only
- Library kept out of `scplay/__init__` eager imports so `python -m scplay.research_validator` stays clean

## Follow-ups (not Day 5)

- Day 6: correct game-loop / iteration capture
- Day 10: artifact hashing / tamper detection via validator
- Live MatchLogger still emits legacy v1 (untouched)
