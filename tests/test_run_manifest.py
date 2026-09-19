"""Day 4 acceptance: reproducible run manifests and config fingerprints."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scplay.run_manifest import (
    DEFAULT_CONTROLLER_VERSION,
    FINGERPRINT_FIELDS,
    RunManifestConfig,
    build_run_manifest,
    compute_config_fingerprint,
    compute_map_checksum,
    sha256_hex,
    write_run_manifest,
)
from scplay.schema_v2 import validate_record

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "manifests"
EXAMPLE_PATH = FIXTURE_DIR / "example_run_manifest.json"


def _base_cfg(**overrides) -> RunManifestConfig:
    data = dict(
        map_name="AbyssalReefLE",
        controller_tier="T2",
        chaos=False,
        realtime=False,
        mode="defense_only",
        opponent="built_in_ai_hard",
        seed=42,
        analysis_intent="confirmatory",
        llm_provider="mock-provider",
        map_checksum_declared="fixture-map-v1",
        sc2_version="5.0.14.93333",
        controller_version=DEFAULT_CONTROLLER_VERSION,
        prompt_text="Hold the line. Do not expand early.",
        provider_model_snapshot={"provider": "mock-provider", "model": "mock-model-1"},
        decision_cadence_s=15.0,
        git_sha="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        git_dirty=False,
        python_packages={"numpy": "2.0.0", "scplay": "workspace", "burnysc2": "7.0.0"},
        skip_probes=True,
        notes={"synthetic": True, "privacy": "fixture"},
    )
    data.update(overrides)
    return RunManifestConfig(**data)


def test_identical_config_same_fingerprint_different_run_ids():
    a = build_run_manifest(_base_cfg())
    b = build_run_manifest(_base_cfg())
    assert a["config_fingerprint"] == b["config_fingerprint"]
    assert a["run_id"] != b["run_id"]
    assert len(a["config_fingerprint"]) == 64
    assert a["seq"] == 0 and a["game_loop"] == 0
    assert a["source"] == "logger"
    assert a["event_type"] == "run_manifest"
    assert a["schema_version"] == "2.0"


def test_seed_change_alters_fingerprint():
    a = build_run_manifest(_base_cfg(seed=42))
    b = build_run_manifest(_base_cfg(seed=99))
    assert a["config_fingerprint"] != b["config_fingerprint"]


def test_chaos_change_alters_fingerprint():
    a = build_run_manifest(_base_cfg(chaos=False))
    b = build_run_manifest(_base_cfg(chaos=True, analysis_intent="exploratory"))
    assert a["config_fingerprint"] != b["config_fingerprint"]


def test_manifest_validates_via_schema_v2():
    manifest = build_run_manifest(_base_cfg())
    validate_record(manifest, event_type="run_manifest")
    assert manifest["map_checksum"]
    assert manifest["controller_version"] == DEFAULT_CONTROLLER_VERSION
    assert manifest["prompt_hash"] == sha256_hex("Hold the line. Do not expand early.")
    assert isinstance(manifest["parameters"], dict)
    assert isinstance(manifest["timing_policy"], dict)
    assert manifest["timing_policy"]["decision_cadence_s"] == 15.0
    assert manifest["timing_policy"]["realtime"] is False


def test_map_checksum_from_temp_file(tmp_path: Path):
    map_file = tmp_path / "FakeMap.SC2Map"
    map_file.write_bytes(b"SC2MAP-FIXTURE-BYTES")
    expected = sha256_hex(b"SC2MAP-FIXTURE-BYTES")
    got = compute_map_checksum(map_name="FakeMap", map_path=map_file)
    assert got == expected
    manifest = build_run_manifest(_base_cfg(map_path=map_file, map_name="FakeMap"))
    assert manifest["map_checksum"] == expected


def test_map_checksum_without_path_uses_name_and_declared():
    a = compute_map_checksum(map_name="AbyssalReefLE", map_checksum_declared="v1")
    b = compute_map_checksum(map_name="AbyssalReefLE", map_checksum_declared="v2")
    assert a != b
    assert a == sha256_hex("AbyssalReefLE\0v1")


def test_fingerprint_fields_documented():
    assert "run_id" not in FINGERPRINT_FIELDS
    assert "started_at_utc" not in FINGERPRINT_FIELDS
    assert "map_name" in FINGERPRINT_FIELDS
    assert "seed" in FINGERPRINT_FIELDS
    assert "parameters" in FINGERPRINT_FIELDS


def test_dict_config_accepted():
    cfg = {
        "map_name": "AbyssalReefLE",
        "controller_tier": "T0",
        "chaos": False,
        "realtime": True,
        "mode": "default",
        "opponent": "built_in_ai_easy",
        "seed": 1,
        "skip_probes": True,
        "git_sha": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "git_dirty": False,
        "python_packages": {"numpy": "1.26.0"},
    }
    manifest = build_run_manifest(cfg)
    validate_record(manifest)
    assert manifest["controller_tier"] == "T0"


def test_injected_run_id_and_started_at():
    m = build_run_manifest(
        _base_cfg(
            run_id="fixed_run_id_for_fixture",
            started_at_utc="2026-09-17T20:00:00Z",
        )
    )
    assert m["run_id"] == "fixed_run_id_for_fixture"
    assert m["started_at_utc"] == "2026-09-17T20:00:00Z"


def test_write_and_example_fixture(tmp_path: Path):
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    manifest = build_run_manifest(
        _base_cfg(
            run_id="20260917T200000Z_AbyssalReefLE_deadbeef",
            started_at_utc="2026-09-17T20:00:00Z",
        )
    )
    # Ensure privacy-safe (no absolute personal paths)
    blob = json.dumps(manifest)
    assert "/home/" not in blob
    assert "kestl" not in blob.lower()

    write_run_manifest(EXAMPLE_PATH, manifest)
    assert EXAMPLE_PATH.is_file()
    reloaded = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
    validate_record(reloaded)
    assert reloaded["config_fingerprint"] == manifest["config_fingerprint"]

    out = write_run_manifest(tmp_path / "m.json", manifest)
    assert out.is_file()


def test_fingerprint_excludes_run_id_and_started_at():
    a = build_run_manifest(
        _base_cfg(run_id="run_a", started_at_utc="2026-09-17T20:00:00Z")
    )
    b = build_run_manifest(
        _base_cfg(run_id="run_b", started_at_utc="2026-09-17T21:00:00Z")
    )
    assert a["config_fingerprint"] == b["config_fingerprint"]
    # Sanity: compute_config_fingerprint ignores extras
    fp = compute_config_fingerprint(
        {"map_name": "X", "seed": 1, "run_id": "should-ignore", "chaos": False}
    )
    fp2 = compute_config_fingerprint({"map_name": "X", "seed": 1, "chaos": False})
    assert fp == fp2


def test_git_probe_mocked():
    calls = {"n": 0}

    def fake_git(_root):
        calls["n"] += 1
        return ("cccccccccccccccccccccccccccccccccccccccc", True)

    m = build_run_manifest(
        RunManifestConfig(
            map_name="AbyssalReefLE",
            controller_tier="T1",
            chaos=False,
            realtime=False,
            mode="default",
            llm_provider="mock",
            python_packages={"numpy": "2.0.0"},
            skip_probes=False,
            # leave git unset so probe runs
        ),
        git_probe=fake_git,
        package_probe=lambda: {"numpy": "2.0.0"},
    )
    assert calls["n"] == 1
    assert m["git_sha"].startswith("cccc")
    assert m["git_dirty"] is True
