"""Day 5 — repository research validator tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scplay.research_validator import (
    Issue,
    has_errors,
    main,
    scan_privacy,
    validate_bundle,
    validate_path,
    validate_schemas_present,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "validator"
CLEAN = FIXTURES / "clean_bundle"
BAD_SCHEMA = FIXTURES / "bad_schema"
PRIVACY = FIXTURES / "privacy_unsafe"
INCOMPLETE = FIXTURES / "incomplete_bundle"


def test_schemas_present_in_repo() -> None:
    issues = validate_schemas_present()
    assert issues == [], [i.format_line() for i in issues]


def test_clean_bundle_no_errors() -> None:
    issues = validate_bundle(CLEAN)
    assert not has_errors(issues), [i.format_line() for i in issues]
    assert validate_path(CLEAN) == issues or not has_errors(validate_path(CLEAN))


def test_clean_bundle_cli_exit_0() -> None:
    code = main([str(CLEAN)])
    assert code == 0


def test_bad_schema_fails_with_actionable_message() -> None:
    issues = validate_bundle(BAD_SCHEMA)
    assert has_errors(issues)
    texts = " ".join(i.format_line() for i in issues).lower()
    assert "schema" in texts
    # Line number for the bad JSONL record (line 2)
    assert any("line 2" in i.path for i in issues)


def test_privacy_unsafe_fails_with_privacy_message() -> None:
    issues = validate_bundle(PRIVACY)
    assert has_errors(issues)
    codes = {i.code for i in issues}
    assert any(c.startswith("privacy.") for c in codes)
    texts = " ".join(i.message for i in issues).lower()
    assert "privacy" in texts or "api" in texts or "home" in texts or "key" in texts


def test_privacy_unsafe_cli_exit_nonzero() -> None:
    code = main([str(PRIVACY)])
    assert code == 1


def test_incomplete_bundle_missing_events() -> None:
    issues = validate_bundle(INCOMPLETE)
    assert has_errors(issues)
    assert any(i.code == "bundle.missing_events" for i in issues)
    assert any("events" in i.message.lower() for i in issues)


def test_scan_privacy_sk_key() -> None:
    issues = scan_privacy("token=sk-test-fake-key-do-not-use-0001")
    assert any(i.code == "privacy.api_key_sk" for i in issues)


def test_scan_privacy_openai_assign() -> None:
    issues = scan_privacy("export OPENAI_API_KEY=not-committed")
    assert any(i.code == "privacy.openai_api_key_assign" for i in issues)


def test_scan_privacy_home_someone() -> None:
    issues = scan_privacy("sc2=/home/someone/StarCraftII/Support64")
    assert any(i.code == "privacy.home_path_posix" for i in issues)


def test_scan_privacy_allows_path_to_sc2() -> None:
    issues = scan_privacy('notes={"sc2": "/path/to/SC2"}')
    assert issues == []


def test_scan_privacy_allows_short_sk() -> None:
    # Shorter than 20-char token after sk- → should not match
    issues = scan_privacy("placeholder sk-short")
    assert not any(i.code == "privacy.api_key_sk" for i in issues)


def test_validate_path_missing() -> None:
    issues = validate_path(FIXTURES / "does_not_exist_day05")
    assert has_errors(issues)
    assert any(i.code == "path.missing" for i in issues)


def test_script_subprocess_clean() -> None:
    script = ROOT / "scripts" / "validate_research.py"
    proc = subprocess.run(
        [sys.executable, str(script), str(CLEAN)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "OK" in proc.stdout or "no issues" in proc.stdout.lower()


def test_script_subprocess_privacy_failure() -> None:
    script = ROOT / "scripts" / "validate_research.py"
    proc = subprocess.run(
        [sys.executable, str(script), str(PRIVACY)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
    out = (proc.stdout + proc.stderr).lower()
    assert "privacy" in out or "api" in out or "home" in out
