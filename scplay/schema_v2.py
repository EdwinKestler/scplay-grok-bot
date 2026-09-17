"""Schema v2 log-record validation helpers (Day 3 research contract).

Live ``MatchLogger`` still emits legacy schema 1.0. This module validates
versioned v2 dicts against ``schemas/v2/*.schema.json`` (JSON Schema draft
2020-12). Day 4 builds real manifests; Day 6 fixes game-loop capture.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Final, Mapping

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

SCHEMA_VERSION: Final[str] = "2.0"

SOURCE_VALUES: Final[frozenset[str]] = frozenset(
    {"logger", "bot", "human", "sc2", "llm", "system"}
)

EVENT_TYPES: Final[frozenset[str]] = frozenset(
    {
        "run_manifest",
        "gameplay_event",
        "chat",
        "snapshot",
        "llm_decision",
    }
)

ENVELOPE_FIELDS: Final[tuple[str, ...]] = (
    "schema_version",
    "run_id",
    "seq",
    "game_loop",
    "source",
    "event_type",
)

_EVENT_TYPE_TO_SCHEMA_FILE: Final[dict[str, str]] = {
    "run_manifest": "run_manifest.schema.json",
    "gameplay_event": "gameplay_event.schema.json",
    "chat": "chat_event.schema.json",
    "snapshot": "snapshot.schema.json",
    "llm_decision": "llm_decision.schema.json",
}

_SCHEMAS_DIR = Path(__file__).resolve().parents[1] / "schemas" / "v2"


class SchemaV2Error(ValueError):
    """Raised when a schema v2 record is missing envelope fields or fails validation."""


def schemas_dir() -> Path:
    """Return the on-disk ``schemas/v2`` directory."""
    return _SCHEMAS_DIR


@lru_cache(maxsize=16)
def load_schema(name: str) -> dict[str, Any]:
    """Load a schema document by filename (e.g. ``chat_event.schema.json``)."""
    path = _SCHEMAS_DIR / name
    if not path.is_file():
        raise SchemaV2Error(f"schema not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def schema_for_event_type(event_type: str) -> dict[str, Any]:
    """Return the JSON Schema for a v2 ``event_type`` discriminator."""
    try:
        filename = _EVENT_TYPE_TO_SCHEMA_FILE[event_type]
    except KeyError as exc:
        raise SchemaV2Error(
            f"unknown event_type {event_type!r}; expected one of "
            f"{sorted(EVENT_TYPES)}"
        ) from exc
    return load_schema(filename)


def envelope_ok(record: Mapping[str, Any]) -> list[str]:
    """Return a list of envelope problems (empty means OK). Does not raise."""
    problems: list[str] = []
    if not isinstance(record, Mapping):
        return [f"record must be a mapping, got {type(record).__name__}"]
    for key in ENVELOPE_FIELDS:
        if key not in record:
            problems.append(f"missing required envelope field: {key}")
    if problems:
        return problems
    if record.get("schema_version") != SCHEMA_VERSION:
        problems.append(
            f"schema_version must be {SCHEMA_VERSION!r}, "
            f"got {record.get('schema_version')!r}"
        )
    run_id = record.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        problems.append("run_id must be a non-empty string")
    seq = record.get("seq")
    if not isinstance(seq, int) or isinstance(seq, bool) or seq < 0:
        problems.append("seq must be an integer >= 0")
    game_loop = record.get("game_loop")
    if (
        not isinstance(game_loop, int)
        or isinstance(game_loop, bool)
        or game_loop < 0
    ):
        problems.append("game_loop must be an integer >= 0")
    source = record.get("source")
    if source not in SOURCE_VALUES:
        problems.append(
            f"source must be one of {sorted(SOURCE_VALUES)}, got {source!r}"
        )
    event_type = record.get("event_type")
    if event_type not in EVENT_TYPES:
        problems.append(
            f"event_type must be one of {sorted(EVENT_TYPES)}, got {event_type!r}"
        )
    return problems


def validate_envelope(record: Mapping[str, Any]) -> None:
    """Raise ``SchemaV2Error`` if the common envelope is incomplete or invalid."""
    problems = envelope_ok(record)
    if problems:
        raise SchemaV2Error("; ".join(problems))


def validate_record(
    record: Mapping[str, Any],
    *,
    event_type: str | None = None,
) -> None:
    """Validate a full v2 record against its type schema.

    ``event_type`` defaults to ``record['event_type']``. Raises
    ``SchemaV2Error`` (wrapping jsonschema details) on failure.
    """
    validate_envelope(record)
    et = event_type or str(record.get("event_type"))
    if event_type is not None and record.get("event_type") != event_type:
        raise SchemaV2Error(
            f"event_type mismatch: record has {record.get('event_type')!r}, "
            f"expected {event_type!r}"
        )
    schema = schema_for_event_type(et)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(record), key=lambda e: list(e.path))
    if errors:
        msgs = []
        for err in errors[:8]:
            path = ".".join(str(p) for p in err.path) or "<root>"
            msgs.append(f"{path}: {err.message}")
        raise SchemaV2Error(
            f"schema v2 validation failed for event_type={et!r}: "
            + "; ".join(msgs)
        )


def is_valid_record(record: Mapping[str, Any]) -> bool:
    """Return True if ``validate_record`` would succeed."""
    try:
        validate_record(record)
        return True
    except (SchemaV2Error, ValidationError):
        return False
