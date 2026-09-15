# Condition registry (Protocol v1 / Day 2)

Machine-readable experimental conditions live in `scplay/conditions.py`.
The Protocol v1 research contract remains in [`PROTOCOL_V1.md`](PROTOCOL_V1.md);
this document describes the registry implementation and validation defaults.

## Model

`ExperimentalCondition` (frozen dataclass) fields:

| Field | Type | Notes |
|-------|------|-------|
| `schema_version` | `"1"` | Only `"1"` accepted in v1 |
| `controller_tier` | `T0` \| `T1` \| `T2` | Strict literals; aliases rejected |
| `map_name` | non-empty str | |
| `opponent` | non-empty str | e.g. `human`, `built_in`, `playbot_spar` |
| `mode` | known instruction id | `default`, `defense_only`, … |
| `chaos` | bool | |
| `realtime` | bool | |
| `decision_cadence_s` | float \| null | Seconds between advisor/banter decisions |
| `analysis_intent` | `confirmatory` \| `exploratory` \| `demo` | |
| `llm_provider` | str \| null | Optional |
| `seed` | int \| null | Optional |

API: `validate_condition`, `condition_from_dict`, `condition_to_dict`,
`load_condition(path)`. Failures raise `ConditionValidationError` (a `ValueError`).

## Validation rules (v1)

1. **Chaos × confirmatory:** `chaos=true` with `analysis_intent="confirmatory"` is rejected. Chaos is allowed only for `exploratory` or `demo` (and must stay labeled as such).
2. **Unknown enums:** unknown `controller_tier` or `analysis_intent` → reject. Aliases such as `"0"` / `"t0"` are **not** normalized.
3. **Required strings:** empty or missing `mode`, `map_name`, or `opponent` → reject. Unknown `mode` (not in `gameplay/instructions/` or the baseline allowlist) → reject.
4. **Provider by tier:** T0 requires `llm_provider` is `null`. T1/T2 require a non-empty `llm_provider`.
5. **T1 is language-only:** tier alone encodes this. If `claims_strategic_control=true` is set with T1 → reject.
6. **Cadence:** if `decision_cadence_s` is provided it must be `> 0`. T1 and T2 always require a positive cadence. Confirmatory T2 likewise requires a positive cadence. T0 may use `null`.
7. **Booleans:** `chaos` / `realtime` must be JSON booleans; truthy integers are rejected as ambiguous.

## Fixtures

See `tests/fixtures/conditions/` and `tests/test_condition_registry.py`.

## Example

```python
from scplay.conditions import load_condition, ConditionValidationError

cond = load_condition("tests/fixtures/conditions/valid_confirmatory_t0.json")
# cond.controller_tier == "T0"
```
