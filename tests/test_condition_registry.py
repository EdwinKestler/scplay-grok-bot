"""Day 2 evidence: experimental condition registry validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scplay.conditions import (
    ConditionValidationError,
    ExperimentalCondition,
    condition_from_dict,
    condition_to_dict,
    load_condition,
    validate_condition,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "conditions"

VALID_FILES = sorted(FIXTURES.glob("valid_*.json"))
INVALID_FILES = sorted(FIXTURES.glob("invalid_*.json"))

# Expected substrings in ConditionValidationError messages (rule fingerprints).
INVALID_MESSAGE_HINTS: dict[str, tuple[str, ...]] = {
    "invalid_confirmatory_chaos.json": ("chaos", "confirmatory"),
    "invalid_unknown_mode.json": ("unknown mode",),
    "invalid_bad_tier.json": ("controller_tier",),
    "invalid_empty_map.json": ("map_name",),
    "invalid_t0_with_provider.json": ("T0", "llm_provider"),
    "invalid_t2_missing_provider.json": ("T2", "llm_provider"),
    "invalid_t1_claims_strategic.json": ("T1", "strategic"),
    "invalid_t2_confirmatory_no_cadence.json": ("decision_cadence_s",),
    "invalid_unknown_intent.json": ("analysis_intent",),
}


def test_fixture_directories_populated():
    assert FIXTURES.is_dir()
    assert len(VALID_FILES) >= 4
    assert len(INVALID_FILES) >= 5


@pytest.mark.parametrize("path", VALID_FILES, ids=lambda p: p.name)
def test_valid_fixtures_parse(path: Path):
    condition = load_condition(path)
    assert isinstance(condition, ExperimentalCondition)
    assert condition.schema_version == "1"
    # Round-trip through dict keeps the same validated values.
    again = condition_from_dict(condition_to_dict(condition))
    assert again == condition


def test_valid_confirmatory_have_chaos_off():
    for name in ("valid_confirmatory_t0.json", "valid_confirmatory_t2.json"):
        cond = load_condition(FIXTURES / name)
        assert cond.analysis_intent == "confirmatory"
        assert cond.chaos is False


def test_valid_exploratory_or_demo_may_enable_chaos():
    exploratory = load_condition(FIXTURES / "valid_exploratory_chaos.json")
    demo = load_condition(FIXTURES / "valid_demo_chaos.json")
    assert exploratory.chaos is True
    assert exploratory.analysis_intent == "exploratory"
    assert demo.chaos is True
    assert demo.analysis_intent == "demo"


def test_valid_t1_exploratory():
    cond = load_condition(FIXTURES / "valid_t1_exploratory.json")
    assert cond.controller_tier == "T1"
    assert cond.analysis_intent == "exploratory"
    assert cond.llm_provider is not None
    assert cond.decision_cadence_s is not None and cond.decision_cadence_s > 0


@pytest.mark.parametrize("path", INVALID_FILES, ids=lambda p: p.name)
def test_invalid_fixtures_raise(path: Path):
    hints = INVALID_MESSAGE_HINTS.get(path.name, ())
    with pytest.raises(ConditionValidationError) as exc_info:
        load_condition(path)
    message = str(exc_info.value).lower()
    for hint in hints:
        assert hint.lower() in message, (
            f"{path.name}: expected message to mention {hint!r}, got {exc_info.value!r}"
        )


def test_confirmatory_chaos_message_explicit():
    data = json.loads(
        (FIXTURES / "invalid_confirmatory_chaos.json").read_text(encoding="utf-8")
    )
    with pytest.raises(ConditionValidationError) as exc_info:
        validate_condition(data)
    msg = str(exc_info.value).lower()
    assert "chaos" in msg and "confirmatory" in msg


def test_reject_tier_alias_t0_lowercase():
    data = {
        "schema_version": "1",
        "controller_tier": "t0",
        "map_name": "Acid Plant LE",
        "opponent": "built_in",
        "mode": "default",
        "chaos": False,
        "realtime": False,
        "decision_cadence_s": None,
        "analysis_intent": "confirmatory",
        "llm_provider": None,
    }
    with pytest.raises(ConditionValidationError) as exc_info:
        validate_condition(data)
    assert "controller_tier" in str(exc_info.value)


def test_reject_non_boolean_chaos():
    data = {
        "schema_version": "1",
        "controller_tier": "T0",
        "map_name": "Acid Plant LE",
        "opponent": "built_in",
        "mode": "default",
        "chaos": 1,
        "realtime": False,
        "decision_cadence_s": None,
        "analysis_intent": "confirmatory",
        "llm_provider": None,
    }
    with pytest.raises(ConditionValidationError) as exc_info:
        validate_condition(data)
    assert "chaos" in str(exc_info.value).lower()
