"""Day 3 evidence: schema v2 log records validate against committed schemas."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scplay.schema_v2 import (
    ENVELOPE_FIELDS,
    EVENT_TYPES,
    SCHEMA_VERSION,
    SOURCE_VALUES,
    SchemaV2Error,
    envelope_ok,
    is_valid_record,
    load_schema,
    schemas_dir,
    validate_envelope,
    validate_record,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "schema_v2"

VALID_JSON = sorted(
    p for p in FIXTURES.glob("valid_*.json") if p.name.startswith("valid_")
)
INVALID_JSON = sorted(FIXTURES.glob("invalid_*.json"))
SAMPLE_JSONL = FIXTURES / "sample_run.jsonl"

EVENT_TYPE_TO_VALID_FILE = {
    "run_manifest": "valid_run_manifest.json",
    "gameplay_event": "valid_gameplay_event.json",
    "chat": "valid_chat_event.json",
    "snapshot": "valid_snapshot.json",
    "llm_decision": "valid_llm_decision.json",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_schema_files_exist():
    assert schemas_dir().is_dir()
    for name in (
        "envelope.schema.json",
        "run_manifest.schema.json",
        "gameplay_event.schema.json",
        "chat_event.schema.json",
        "snapshot.schema.json",
        "llm_decision.schema.json",
        "README.md",
    ):
        assert (schemas_dir() / name).is_file(), name
    # Draft marker present
    schema = load_schema("envelope.schema.json")
    assert "2020-12" in schema["$schema"]


def test_fixture_directory_populated():
    assert FIXTURES.is_dir()
    assert len(VALID_JSON) >= 5
    assert len(INVALID_JSON) >= 1
    assert SAMPLE_JSONL.is_file()
    for et, filename in EVENT_TYPE_TO_VALID_FILE.items():
        assert (FIXTURES / filename).is_file(), f"missing fixture for {et}"


@pytest.mark.parametrize("path", VALID_JSON, ids=lambda p: p.name)
def test_valid_fixtures_validate(path: Path):
    record = _load(path)
    validate_record(record)
    assert is_valid_record(record)
    for key in ENVELOPE_FIELDS:
        assert key in record
    assert record["schema_version"] == SCHEMA_VERSION
    assert isinstance(record["run_id"], str) and record["run_id"]
    assert isinstance(record["seq"], int) and record["seq"] >= 0
    assert isinstance(record["game_loop"], int) and record["game_loop"] >= 0
    assert record["source"] in SOURCE_VALUES
    assert record["event_type"] in EVENT_TYPES


@pytest.mark.parametrize("path", INVALID_JSON, ids=lambda p: p.name)
def test_invalid_fixtures_fail(path: Path):
    record = _load(path)
    assert envelope_ok(record)
    with pytest.raises(SchemaV2Error):
        validate_record(record)
    assert not is_valid_record(record)


def test_sample_run_jsonl_monotonic_and_valid():
    rows = [
        json.loads(line)
        for line in SAMPLE_JSONL.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rows) >= 5
    seqs = [r["seq"] for r in rows]
    assert seqs == sorted(seqs)
    assert seqs == list(range(seqs[0], seqs[0] + len(seqs)))
    run_ids = {r["run_id"] for r in rows}
    assert len(run_ids) == 1
    seen_types = {r["event_type"] for r in rows}
    assert EVENT_TYPES <= seen_types or seen_types >= {
        "run_manifest",
        "gameplay_event",
        "chat",
        "snapshot",
        "llm_decision",
    }
    for row in rows:
        validate_record(row)


def test_inline_invalid_dicts():
    base = _load(FIXTURES / "valid_chat_event.json")

    missing_seq = dict(base)
    del missing_seq["seq"]
    with pytest.raises(SchemaV2Error, match="seq"):
        validate_envelope(missing_seq)

    bad_version = dict(base)
    bad_version["schema_version"] = "1.0"
    with pytest.raises(SchemaV2Error, match="schema_version"):
        validate_record(bad_version)

    bad_source = dict(base)
    bad_source["source"] = "telegram"
    with pytest.raises(SchemaV2Error, match="source"):
        validate_record(bad_source)

    # Type-specific: chat without message
    no_message = dict(base)
    del no_message["message"]
    with pytest.raises(SchemaV2Error, match="message"):
        validate_record(no_message)

    # Wrong discriminator vs requested type
    with pytest.raises(SchemaV2Error, match="mismatch"):
        validate_record(base, event_type="snapshot")


def test_envelope_schema_accepts_open_extra_fields():
    """envelope.schema.json allows additionalProperties; type schemas do not."""
    from jsonschema import Draft202012Validator

    envelope = load_schema("envelope.schema.json")
    record = _load(FIXTURES / "valid_chat_event.json")
    Draft202012Validator(envelope).validate(record)
