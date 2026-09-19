# Research validator (Day 5)

One local command that validates research configuration, schemas, manifests,
JSONL records, privacy rules, and required run-bundle artifacts.

## How to run

From the repository root (with the project venv active, or `PYTHONPATH=.`):

```bash
python scripts/validate_research.py tests/fixtures/validator/clean_bundle
python -m scplay.research_validator tests/fixtures/validator/clean_bundle
```

Expected-failure examples:

```bash
python scripts/validate_research.py tests/fixtures/validator/bad_schema
python scripts/validate_research.py tests/fixtures/validator/privacy_unsafe
python scripts/validate_research.py tests/fixtures/validator/incomplete_bundle
```

Options:

| Flag | Meaning |
|------|---------|
| `--json` | Emit issues as a JSON array |
| `--no-privacy` | Skip privacy heuristics (not for committed fixtures) |
| `--no-schemas` | Skip `schemas/v2` presence check on directories |

## Exit codes

| Code | Meaning |
|-----:|---------|
| 0 | No error-severity issues |
| 1 | One or more errors (malformed, incomplete, or privacy-unsafe) |

Warnings (if any) do not alone force a nonzero exit.

## Library API

```python
from scplay.research_validator import validate_path, validate_bundle, Issue

issues: list[Issue] = validate_bundle("path/to/run_bundle")
# Issue(severity="error"|"warning", code="...", path="...", message="...")
```

`validate_path` accepts a file or directory. Directories that look like run
bundles (contain a manifest and/or events JSONL, or have `bundle` in the name)
use the bundle checklist.

## What it checks

1. **Schemas present** — when validating a repo root (directory containing
   `schemas/v2`), every required `*.schema.json` must exist and load as JSON.
2. **Manifest** — `run_manifest.json` / `manifest.json` validates as schema v2
   `event_type=run_manifest` via `validate_record`.
3. **Conditions** (optional) — `condition.json` / `experimental_condition.json`
   validates via the Day 2 condition registry (`validate_condition`).
4. **JSONL records** — each non-empty line of an events JSONL validates against
   the v2 schema selected by the `event_type` discriminator; failures report
   `path:line N`.
5. **Required artifacts (run bundle checklist)** — a bundle directory must have:
   - a manifest (`run_manifest.json` or `manifest.json`)
   - at least one events file (`events.jsonl`, `records.jsonl`,
     `gameplay_events.jsonl`, or `*.events.jsonl`)
   Missing files produce actionable `bundle.missing_*` errors.
6. **Privacy rules** — see heuristics below.

## Privacy heuristics

The validator **fails** (error) when scanned text contains any of:

### API key-like patterns

| Pattern | Code |
|---------|------|
| `sk-` + ≥20 chars of `[A-Za-z0-9_-]` | `privacy.api_key_sk` |
| `OPENAI_API_KEY=` | `privacy.openai_api_key_assign` |
| `ANTHROPIC_API_KEY=` | `privacy.anthropic_api_key_assign` |
| `Bearer ` + ≥20 token chars | `privacy.bearer_token` |

Fixtures must **not** contain real secrets. Obviously fake tokens such as
`sk-test-fake-key-do-not-use-0001` are used only in the `privacy_unsafe`
expected-failure fixture (they still match the detector on purpose). Short
placeholders like `sk-short` do **not** match.

### Absolute personal home paths

| Pattern | Code |
|---------|------|
| `/home/<user>/...` | `privacy.home_path_posix` |
| `C:\Users\<user>\...` or `C:/Users/<user>/...` | `privacy.home_path_windows` |

**Allowed** synthetic placeholders (examples): `/path/to/SC2`, `/tmp/...`,
`/workspace/...`. A small allowlist of synthetic usernames (`user`, `alice`,
`bob`, `runner`, `ci`, `placeholder`, `example`, `test`, `sc2`) is exempt;
**`someone` is not exempt** so `/home/someone/...` fails as required.

## Fixtures

Under `tests/fixtures/validator/`:

| Fixture | Expected |
|---------|----------|
| `clean_bundle/` | Pass (exit 0) |
| `bad_schema/` | Fail schema on JSONL line 2 |
| `privacy_unsafe/` | Fail privacy (fake key + `/home/someone/...`) |
| `incomplete_bundle/` | Fail missing events file |

## Related

- Day 2: [`CONDITION_REGISTRY.md`](CONDITION_REGISTRY.md)
- Day 3: [`LOG_SCHEMA.md`](LOG_SCHEMA.md), `schemas/v2/`
- Day 4: [`RUN_MANIFEST.md`](RUN_MANIFEST.md)
