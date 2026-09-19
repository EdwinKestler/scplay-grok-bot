# Run manifest (Day 4)

Per-run metadata for reproducible research launches. Builder:
`scplay.run_manifest.build_run_manifest`.

Schema: [`schemas/v2/run_manifest.schema.json`](../schemas/v2/run_manifest.schema.json).  
Example fixture: [`tests/fixtures/manifests/example_run_manifest.json`](../tests/fixtures/manifests/example_run_manifest.json).

## Acceptance

Two launches with the **same configuration** produce the **same**
`config_fingerprint` while retaining **unique** `run_id` values.

## Building a manifest

```python
from scplay import RunManifestConfig, build_run_manifest

manifest = build_run_manifest(
    RunManifestConfig(
        map_name="AbyssalReefLE",
        controller_tier="T2",
        chaos=False,
        realtime=False,
        mode="defense_only",
        opponent="built_in_ai_hard",
        seed=42,
        analysis_intent="confirmatory",
        llm_provider="mock-provider",
        decision_cadence_s=15.0,
        prompt_text="Hold the line.",
        provider_model_snapshot={"provider": "mock", "model": "m1"},
        sc2_version="5.0.14.93333",  # optional; no live SC2 required
    )
)
assert manifest["event_type"] == "run_manifest"
assert manifest["seq"] == 0
```

Inject `git_sha` / `git_dirty` / `python_packages` and set `skip_probes=True`
for offline deterministic tests. Live probes use `git rev-parse` /
`git status --porcelain` when `.git` exists and never fail hard (nulls on
missing git).

## `config_fingerprint` inputs

Stable **sha256** over **canonical JSON** (`sort_keys=True`, compact
separators) of these fields only:

| Field | Role |
|-------|------|
| `map_name` | Map identity |
| `map_checksum` | sha256 of map file bytes, or of `map_name + "\\0" + declared` |
| `controller_tier` | T0 / T1 / T2 |
| `controller_version` | e.g. `PlaybotSparBot/1` |
| `chaos` | Chaos flag |
| `realtime` | Real-time flag |
| `mode` | Instruction / mode id |
| `opponent` | Opponent id |
| `seed` | RNG seed |
| `analysis_intent` | confirmatory / exploratory / demo |
| `llm_provider` | Provider id (or null for T0) |
| `prompt_hash` | sha256 of prompt text |
| `provider_model_snapshot` | Provider/model snapshot (string or object; no secrets) |
| `sc2_version` | SC2 build string (nullable) |
| `python_packages` | Key dependency versions |
| `git_sha` | Commit SHA (nullable if unavailable) |
| `git_dirty` | Working tree dirty flag |
| `parameters` | Canonical parameter bag |
| `timing_policy` | e.g. `{decision_cadence_s, realtime}` |

**Excluded** from the fingerprint (per-launch uniqueness / envelope):

`run_id`, `started_at_utc`, `seq`, `game_loop`, `game_time_s`, `source`,
`event_type`, `schema_version`, `config_fingerprint`, `notes`.

Constant: `scplay.run_manifest.FINGERPRINT_FIELDS`.

## Map checksum

1. If `map_path` points at a readable file → sha256 of file bytes.
2. Else → sha256 of `map_name + "\\0" + (map_checksum_declared or "")`.

Fixtures must use temp files or declared checksums — never absolute personal
paths.

## Schema extensions (Day 4)

Optional fields added to the Day 3 schema (required envelope + Day 3 required
fields unchanged):

- `map_checksum`
- `controller_version`
- `provider_model_snapshot`
- `parameters`
- `timing_policy`

See also [`LOG_SCHEMA.md`](LOG_SCHEMA.md) and [`schemas/v2/README.md`](../schemas/v2/README.md).
