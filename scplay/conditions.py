"""Machine-readable experimental condition registry (Protocol v1 / Day 2).

Validates controller tier, map, opponent, mode, chaos, realtime, decision
cadence, and analysis intent. Invalid or ambiguous combinations raise
``ConditionValidationError``.

v1 defaults (documented):
- Strict literal enums only (``T0``/``T1``/``T2``; no aliases like ``0``).
- ``llm_provider`` must be ``None`` for T0; required non-empty for T1/T2.
- Tier alone encodes strategy vs language: T1 is never strategic. An explicit
  ``claims_strategic_control=true`` field with T1 is rejected.
- ``decision_cadence_s`` may be ``None`` for T0; T1/T2 require a positive
  cadence. Confirmatory T2 likewise requires a positive cadence.
- Known modes: instruction ids under ``gameplay/instructions/`` plus the
  Protocol v1 baseline allowlist (``default``, ``defense_only``).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Final, Literal, Mapping

ControllerTier = Literal["T0", "T1", "T2"]
AnalysisIntent = Literal["confirmatory", "exploratory", "demo"]

SCHEMA_VERSION: Final[str] = "1"
CONTROLLER_TIERS: Final[frozenset[str]] = frozenset({"T0", "T1", "T2"})
ANALYSIS_INTENTS: Final[frozenset[str]] = frozenset(
    {"confirmatory", "exploratory", "demo"}
)
# Baseline allowlist even if instruction files are absent on disk.
BASELINE_KNOWN_MODES: Final[frozenset[str]] = frozenset({"default", "defense_only"})


class ConditionValidationError(ValueError):
    """Raised when an experimental condition is invalid or ambiguous."""


@dataclass(frozen=True)
class ExperimentalCondition:
    """One Protocol v1 experimental condition cell."""

    schema_version: str
    controller_tier: ControllerTier
    map_name: str
    opponent: str
    mode: str
    chaos: bool
    realtime: bool
    decision_cadence_s: float | None
    analysis_intent: AnalysisIntent
    llm_provider: str | None = None
    seed: int | None = None


def known_modes() -> frozenset[str]:
    """Return allowlisted gameplay instruction ids for mode validation."""
    modes = set(BASELINE_KNOWN_MODES)
    try:
        from scplay.gameplay import list_instruction_ids

        modes.update(list_instruction_ids())
    except Exception:
        # Registry must validate fixtures even if gameplay helpers fail.
        pass
    return frozenset(modes)


def _require_mapping(data: Any) -> Mapping[str, Any]:
    if not isinstance(data, Mapping):
        raise ConditionValidationError(
            "condition must be a JSON object / mapping, not "
            f"{type(data).__name__}"
        )
    return data


def _require_str(data: Mapping[str, Any], key: str, *, allow_empty: bool = False) -> str:
    if key not in data:
        raise ConditionValidationError(f"missing required field: {key}")
    value = data[key]
    if not isinstance(value, str):
        raise ConditionValidationError(
            f"{key} must be a string, got {type(value).__name__}"
        )
    if not allow_empty and not value.strip():
        raise ConditionValidationError(f"{key} must be a non-empty string")
    return value.strip() if not allow_empty else value


def _require_bool(data: Mapping[str, Any], key: str) -> bool:
    if key not in data:
        raise ConditionValidationError(f"missing required field: {key}")
    value = data[key]
    if not isinstance(value, bool):
        raise ConditionValidationError(
            f"{key} must be a boolean (true/false), got {type(value).__name__}; "
            "ambiguous truthy/falsy values are rejected"
        )
    return value


def _optional_float(data: Mapping[str, Any], key: str) -> float | None:
    if key not in data or data[key] is None:
        return None
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConditionValidationError(
            f"{key} must be a number or null, got {type(value).__name__}"
        )
    return float(value)


def _optional_int(data: Mapping[str, Any], key: str) -> int | None:
    if key not in data or data[key] is None:
        return None
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConditionValidationError(
            f"{key} must be an integer or null, got {type(value).__name__}"
        )
    return value


def _optional_str(data: Mapping[str, Any], key: str) -> str | None:
    if key not in data or data[key] is None:
        return None
    value = data[key]
    if not isinstance(value, str):
        raise ConditionValidationError(
            f"{key} must be a string or null, got {type(value).__name__}"
        )
    return value


def condition_from_dict(data: Any) -> ExperimentalCondition:
    """Parse and validate a condition mapping into ``ExperimentalCondition``."""
    return validate_condition(data)


def condition_to_dict(condition: ExperimentalCondition) -> dict[str, Any]:
    """Serialize a validated condition to a plain JSON-ready dict."""
    return asdict(condition)


def load_condition(path: str | Path) -> ExperimentalCondition:
    """Load and validate a condition JSON file."""
    p = Path(path)
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConditionValidationError(f"condition file not found: {p}") from exc
    except json.JSONDecodeError as exc:
        raise ConditionValidationError(
            f"condition file is not valid JSON: {p}: {exc}"
        ) from exc
    return validate_condition(raw)


def validate_condition(data: Any) -> ExperimentalCondition:
    """Validate experimental condition fields and cross-field rules.

    Raises:
        ConditionValidationError: on any invalid or ambiguous combination.
    """
    mapping = _require_mapping(data)

    schema_version = _require_str(mapping, "schema_version")
    if schema_version != SCHEMA_VERSION:
        raise ConditionValidationError(
            f"unsupported schema_version {schema_version!r}; "
            f"expected {SCHEMA_VERSION!r}"
        )

    controller_tier_raw = _require_str(mapping, "controller_tier")
    if controller_tier_raw not in CONTROLLER_TIERS:
        raise ConditionValidationError(
            f"unknown controller_tier {controller_tier_raw!r}; "
            f"expected one of {sorted(CONTROLLER_TIERS)} "
            "(aliases such as '0' or 't0' are rejected for v1 clarity)"
        )
    controller_tier: ControllerTier = controller_tier_raw  # type: ignore[assignment]

    analysis_intent_raw = _require_str(mapping, "analysis_intent")
    if analysis_intent_raw not in ANALYSIS_INTENTS:
        raise ConditionValidationError(
            f"unknown analysis_intent {analysis_intent_raw!r}; "
            f"expected one of {sorted(ANALYSIS_INTENTS)}"
        )
    analysis_intent: AnalysisIntent = analysis_intent_raw  # type: ignore[assignment]

    map_name = _require_str(mapping, "map_name")
    opponent = _require_str(mapping, "opponent")
    mode = _require_str(mapping, "mode")
    chaos = _require_bool(mapping, "chaos")
    realtime = _require_bool(mapping, "realtime")
    decision_cadence_s = _optional_float(mapping, "decision_cadence_s")
    llm_provider = _optional_str(mapping, "llm_provider")
    seed = _optional_int(mapping, "seed")

    allowed_modes = known_modes()
    if mode not in allowed_modes:
        raise ConditionValidationError(
            f"unknown mode {mode!r}; known modes: {sorted(allowed_modes)}"
        )

    # Chaos must not mix with confirmatory cells.
    if chaos and analysis_intent == "confirmatory":
        raise ConditionValidationError(
            "chaos must be false when analysis_intent is confirmatory "
            "(chaos is only allowed for exploratory or demo intents)"
        )

    # llm_provider rules by tier.
    if controller_tier == "T0":
        if llm_provider is not None:
            raise ConditionValidationError(
                "T0 scripted tier requires llm_provider to be null "
                f"(ambiguous non-null value {llm_provider!r})"
            )
    else:
        # T1 / T2
        if llm_provider is None or not llm_provider.strip():
            raise ConditionValidationError(
                f"{controller_tier} requires a non-empty llm_provider"
            )
        llm_provider = llm_provider.strip()

    # T1 must never claim strategic control.
    if "claims_strategic_control" in mapping:
        claims = mapping["claims_strategic_control"]
        if not isinstance(claims, bool):
            raise ConditionValidationError(
                "claims_strategic_control must be a boolean if present"
            )
        if controller_tier == "T1" and claims is True:
            raise ConditionValidationError(
                "T1 must never be treated as strategy: "
                "claims_strategic_control=true with controller_tier=T1 is rejected "
                "(tier alone encodes language-only ablation)"
            )
        if controller_tier != "T1" and claims is True and controller_tier == "T0":
            raise ConditionValidationError(
                "claims_strategic_control=true is incompatible with T0 "
                "(scripted controller has no LLM strategic control)"
            )

    # Decision cadence.
    if decision_cadence_s is not None and decision_cadence_s <= 0:
        raise ConditionValidationError(
            f"decision_cadence_s must be > 0 when provided, got {decision_cadence_s}"
        )

    if controller_tier in ("T1", "T2"):
        if decision_cadence_s is None or decision_cadence_s <= 0:
            raise ConditionValidationError(
                f"{controller_tier} requires a positive decision_cadence_s "
                "(seconds between advisor/banter decisions)"
            )

    if (
        analysis_intent == "confirmatory"
        and controller_tier == "T2"
        and (decision_cadence_s is None or decision_cadence_s <= 0)
    ):
        raise ConditionValidationError(
            "confirmatory T2 requires a positive decision_cadence_s"
        )

    return ExperimentalCondition(
        schema_version=schema_version,
        controller_tier=controller_tier,
        map_name=map_name,
        opponent=opponent,
        mode=mode,
        chaos=chaos,
        realtime=realtime,
        decision_cadence_s=decision_cadence_s,
        analysis_intent=analysis_intent,
        llm_provider=llm_provider,
        seed=seed,
    )
