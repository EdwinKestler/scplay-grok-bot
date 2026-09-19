"""Repository research validator (Day 5).

Validates configuration (condition registry), schemas, manifests, JSONL
records, privacy rules, and required run-bundle artifacts.

Library API
-----------
- ``Issue`` — structured finding (severity, code, path, message)
- ``validate_path(path)`` — validate a file or directory tree
- ``validate_bundle(bundle_dir)`` — validate a run-bundle directory

CLI
---
``python -m scplay.research_validator PATH`` or ``scripts/validate_research.py``
Exit 0 on clean (no error-severity issues), exit 1 when any error is present.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Final, Iterable, Literal, Mapping, Sequence

from scplay.conditions import ConditionValidationError, validate_condition
from scplay.schema_v2 import (
    EVENT_TYPES,
    SchemaV2Error,
    load_schema,
    schemas_dir,
    validate_record,
)

Severity = Literal["error", "warning"]

# ---------------------------------------------------------------------------
# Required schema files (schemas/v2)
# ---------------------------------------------------------------------------
REQUIRED_SCHEMA_FILES: Final[tuple[str, ...]] = (
    "envelope.schema.json",
    "run_manifest.schema.json",
    "gameplay_event.schema.json",
    "chat_event.schema.json",
    "snapshot.schema.json",
    "llm_decision.schema.json",
)

# ---------------------------------------------------------------------------
# Run-bundle checklist
# ---------------------------------------------------------------------------
# A "run bundle" directory must contain:
#   1. A run manifest JSON named one of MANIFEST_NAMES
#   2. At least one events JSONL named matching EVENTS_JSONL_GLOBS / names
MANIFEST_NAMES: Final[tuple[str, ...]] = (
    "run_manifest.json",
    "manifest.json",
)
EVENTS_JSONL_NAMES: Final[tuple[str, ...]] = (
    "events.jsonl",
    "records.jsonl",
    "gameplay_events.jsonl",
)
EVENTS_JSONL_SUFFIX: Final[str] = ".events.jsonl"

# Condition JSON filenames (optional companion in a bundle)
CONDITION_NAMES: Final[tuple[str, ...]] = (
    "condition.json",
    "experimental_condition.json",
)

# Text extensions scanned for privacy when walking a path
_TEXT_SUFFIXES: Final[frozenset[str]] = frozenset(
    {
        ".json",
        ".jsonl",
        ".md",
        ".txt",
        ".py",
        ".yml",
        ".yaml",
        ".toml",
        ".cfg",
        ".ini",
        ".env",
        ".sh",
        ".csv",
    }
)



@dataclass(frozen=True)
class Issue:
    """One validator finding."""

    severity: Severity
    code: str
    path: str
    message: str

    def format_line(self) -> str:
        return f"[{self.severity.upper()}] {self.code}: {self.path}: {self.message}"


# ---------------------------------------------------------------------------
# Privacy heuristics (documented in docs/RESEARCH_VALIDATOR.md)
# ---------------------------------------------------------------------------
#
# Fail (error) when content contains ANY of:
#
# 1. API key-like patterns
#    - sk-<token> where token is >= 20 chars of [A-Za-z0-9_-]
#      (covers OpenAI-style keys; fixtures must use sk-test-fake... that still
#      match, or deliberately short tokens that do NOT match)
#    - OPENAI_API_KEY=... or ANTHROPIC_API_KEY=... (assignment form)
#    - Bearer <token> where token is >= 20 chars of [A-Za-z0-9._~+/=-]
#
# 2. Absolute personal home paths in committed fixtures
#    - /home/<user>/... where <user> is not a known synthetic placeholder
#    - C:\Users\<user>\... or C:/Users/<user>/...
#    Allowed synthetic placeholders: /path/to/SC2, /tmp/..., /workspace/...
#
_RE_SK_KEY = re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")
_RE_OPENAI_ASSIGN = re.compile(r"\bOPENAI_API_KEY\s*=")
_RE_ANTHROPIC_ASSIGN = re.compile(r"\bANTHROPIC_API_KEY\s*=")
_RE_BEARER = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{20,}")
_RE_HOME_POSIX = re.compile(r"(?<![\w])/home/([A-Za-z0-9._-]+)(/[^\s\"']*)?")
_RE_HOME_WIN = re.compile(
    r"(?i)\b([A-Z]:)\\Users\\([A-Za-z0-9._-]+)(\\+[^\s\"']*)?"
)
_RE_HOME_WIN_FWD = re.compile(
    r"(?i)\b([A-Z]:)/Users/([A-Za-z0-9._-]+)(/[^\s\"']*)?"
)

# Usernames treated as synthetic placeholders (not personal home leaks).
# NOTE: "someone" is intentionally NOT exempt — Day 5 requires
# `/home/someone/...` to fail the privacy check.
_SYNTHETIC_HOME_USERS: Final[frozenset[str]] = frozenset(
    {
        "user",
        "alice",
        "bob",
        "runner",
        "ci",
        "placeholder",
        "example",
        "test",
        "sc2",
    }
)


def scan_privacy(text: str, *, rel_path: str = "<content>") -> list[Issue]:
    """Return privacy issues found in ``text`` (empty if clean)."""
    issues: list[Issue] = []

    if _RE_SK_KEY.search(text):
        issues.append(
            Issue(
                "error",
                "privacy.api_key_sk",
                rel_path,
                "content matches sk-<long-token> API-key heuristic; "
                "remove secrets (use obviously redacted placeholders that "
                "do not match sk-[A-Za-z0-9_-]{20,})",
            )
        )
    if _RE_OPENAI_ASSIGN.search(text):
        issues.append(
            Issue(
                "error",
                "privacy.openai_api_key_assign",
                rel_path,
                "content contains OPENAI_API_KEY= assignment; "
                "never commit API keys (use env vars / .env.example only)",
            )
        )
    if _RE_ANTHROPIC_ASSIGN.search(text):
        issues.append(
            Issue(
                "error",
                "privacy.anthropic_api_key_assign",
                rel_path,
                "content contains ANTHROPIC_API_KEY= assignment; "
                "never commit API keys (use env vars / .env.example only)",
            )
        )
    if _RE_BEARER.search(text):
        issues.append(
            Issue(
                "error",
                "privacy.bearer_token",
                rel_path,
                "content matches Bearer <long-token> heuristic; "
                "remove authorization secrets from fixtures",
            )
        )

    for m in _RE_HOME_POSIX.finditer(text):
        user = m.group(1)
        full = m.group(0)
        # Allow if the full match is under an allowed synthetic prefix
        if any(full.startswith(p.rstrip("/")) or p in full for p in ("/path/to",)):
            continue
        if user.lower() in _SYNTHETIC_HOME_USERS:
            continue
        issues.append(
            Issue(
                "error",
                "privacy.home_path_posix",
                rel_path,
                f"absolute personal home path {full!r}; "
                "use repository-relative or synthetic placeholders "
                "like /path/to/SC2 (not /home/<user>/...)",
            )
        )

    for m in _RE_HOME_WIN.finditer(text):
        user = m.group(2)
        full = m.group(0)
        if user.lower() in _SYNTHETIC_HOME_USERS:
            continue
        issues.append(
            Issue(
                "error",
                "privacy.home_path_windows",
                rel_path,
                f"absolute personal home path {full!r}; "
                "use repository-relative or synthetic placeholders "
                r"like C:\path\to\SC2 (not C:\Users\<user>\...)",
            )
        )

    for m in _RE_HOME_WIN_FWD.finditer(text):
        user = m.group(2)
        full = m.group(0)
        if user.lower() in _SYNTHETIC_HOME_USERS:
            continue
        issues.append(
            Issue(
                "error",
                "privacy.home_path_windows",
                rel_path,
                f"absolute personal home path {full!r}; "
                "use repository-relative or synthetic placeholders "
                "like C:/path/to/SC2 (not C:/Users/<user>/...)",
            )
        )

    return issues


def _rel(path: Path, root: Path | None) -> str:
    if root is None:
        return str(path)
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def validate_schemas_present(
    schemas_root: Path | None = None,
    *,
    rel_root: Path | None = None,
) -> list[Issue]:
    """Check that required ``schemas/v2/*.schema.json`` files exist and load."""
    issues: list[Issue] = []
    root = schemas_root if schemas_root is not None else schemas_dir()
    display = _rel(root, rel_root) if rel_root else str(root)

    if not root.is_dir():
        issues.append(
            Issue(
                "error",
                "schemas.missing_dir",
                display,
                f"schemas directory not found: {root}",
            )
        )
        return issues

    for name in REQUIRED_SCHEMA_FILES:
        path = root / name
        rel = _rel(path, rel_root) if rel_root else str(path)
        if not path.is_file():
            issues.append(
                Issue(
                    "error",
                    "schemas.missing_file",
                    rel,
                    f"required schema file missing: {name}",
                )
            )
            continue
        try:
            # Prefer schema_v2.load_schema when using the default dir so cache hits
            if schemas_root is None or Path(schemas_root).resolve() == schemas_dir().resolve():
                doc = load_schema(name)
            else:
                doc = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(doc, dict):
                issues.append(
                    Issue(
                        "error",
                        "schemas.not_object",
                        rel,
                        f"schema {name} must be a JSON object",
                    )
                )
        except (OSError, json.JSONDecodeError, SchemaV2Error) as exc:
            issues.append(
                Issue(
                    "error",
                    "schemas.unreadable",
                    rel,
                    f"schema {name} failed to load: {exc}",
                )
            )
    return issues


def validate_manifest_file(
    path: Path,
    *,
    rel_root: Path | None = None,
    check_privacy: bool = True,
) -> list[Issue]:
    """Validate a run_manifest JSON file against schema v2."""
    issues: list[Issue] = []
    rel = _rel(path, rel_root)
    try:
        text = _read_text(path)
    except OSError as exc:
        return [Issue("error", "manifest.unreadable", rel, str(exc))]

    if check_privacy:
        issues.extend(scan_privacy(text, rel_path=rel))

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        issues.append(
            Issue(
                "error",
                "manifest.invalid_json",
                rel,
                f"manifest is not valid JSON: {exc}",
            )
        )
        return issues

    if not isinstance(data, Mapping):
        issues.append(
            Issue(
                "error",
                "manifest.not_object",
                rel,
                "manifest must be a JSON object",
            )
        )
        return issues

    try:
        validate_record(data, event_type="run_manifest")
    except SchemaV2Error as exc:
        issues.append(
            Issue(
                "error",
                "manifest.schema",
                rel,
                f"run_manifest schema validation failed: {exc}",
            )
        )
    return issues


def validate_condition_file(
    path: Path,
    *,
    rel_root: Path | None = None,
    check_privacy: bool = True,
) -> list[Issue]:
    """Validate a condition JSON via the condition registry."""
    issues: list[Issue] = []
    rel = _rel(path, rel_root)
    try:
        text = _read_text(path)
    except OSError as exc:
        return [Issue("error", "condition.unreadable", rel, str(exc))]

    if check_privacy:
        issues.extend(scan_privacy(text, rel_path=rel))

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        issues.append(
            Issue(
                "error",
                "condition.invalid_json",
                rel,
                f"condition is not valid JSON: {exc}",
            )
        )
        return issues

    try:
        validate_condition(data)
    except ConditionValidationError as exc:
        issues.append(
            Issue(
                "error",
                "condition.invalid",
                rel,
                f"condition registry rejected condition: {exc}",
            )
        )
    return issues


def validate_jsonl_file(
    path: Path,
    *,
    rel_root: Path | None = None,
    check_privacy: bool = True,
) -> list[Issue]:
    """Validate each JSONL line against the v2 event schema (by event_type)."""
    issues: list[Issue] = []
    rel = _rel(path, rel_root)
    try:
        text = _read_text(path)
    except OSError as exc:
        return [Issue("error", "jsonl.unreadable", rel, str(exc))]

    if check_privacy:
        issues.extend(scan_privacy(text, rel_path=rel))

    if not text.strip():
        issues.append(
            Issue(
                "error",
                "jsonl.empty",
                rel,
                "JSONL events file is empty; expected at least one record",
            )
        )
        return issues

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        loc = f"{rel}:line {line_no}"
        if check_privacy:
            # Per-line privacy already covered by whole-file scan; skip dupes
            pass
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            issues.append(
                Issue(
                    "error",
                    "jsonl.invalid_json",
                    loc,
                    f"line is not valid JSON: {exc}",
                )
            )
            continue
        if not isinstance(record, Mapping):
            issues.append(
                Issue(
                    "error",
                    "jsonl.not_object",
                    loc,
                    "JSONL record must be a JSON object",
                )
            )
            continue
        et = record.get("event_type")
        if et not in EVENT_TYPES:
            issues.append(
                Issue(
                    "error",
                    "jsonl.unknown_event_type",
                    loc,
                    f"unknown or missing event_type {et!r}; "
                    f"expected one of {sorted(EVENT_TYPES)}",
                )
            )
            continue
        try:
            validate_record(record)
        except SchemaV2Error as exc:
            issues.append(
                Issue(
                    "error",
                    "jsonl.schema",
                    loc,
                    f"schema validation failed for event_type={et!r}: {exc}",
                )
            )
    return issues


def _is_events_jsonl(name: str) -> bool:
    if name in EVENTS_JSONL_NAMES:
        return True
    if name.endswith(EVENTS_JSONL_SUFFIX):
        return True
    return False


def _find_manifest(bundle: Path) -> Path | None:
    for name in MANIFEST_NAMES:
        candidate = bundle / name
        if candidate.is_file():
            return candidate
    return None


def _find_events_files(bundle: Path) -> list[Path]:
    found: list[Path] = []
    for child in sorted(bundle.iterdir()):
        if child.is_file() and _is_events_jsonl(child.name):
            found.append(child)
    return found


def _find_condition(bundle: Path) -> Path | None:
    for name in CONDITION_NAMES:
        candidate = bundle / name
        if candidate.is_file():
            return candidate
    return None


def validate_bundle(
    bundle_dir: str | Path,
    *,
    check_privacy: bool = True,
    rel_root: Path | None = None,
) -> list[Issue]:
    """Validate a run-bundle directory.

    Checklist (documented in docs/RESEARCH_VALIDATOR.md):
    1. Directory exists
    2. A run manifest JSON (``run_manifest.json`` or ``manifest.json``)
    3. At least one events JSONL (``events.jsonl``, ``records.jsonl``,
       ``gameplay_events.jsonl``, or ``*.events.jsonl``)
    4. Optional ``condition.json`` validated via condition registry when present
    5. Privacy scan on all checked files when ``check_privacy`` is True
    """
    bundle = Path(bundle_dir)
    root = rel_root if rel_root is not None else bundle.parent
    try:
        rel = str(bundle.resolve().relative_to(root.resolve()))
        if rel == ".":
            rel = bundle.name
    except ValueError:
        rel = bundle.name
    issues: list[Issue] = []

    if not bundle.is_dir():
        return [
            Issue(
                "error",
                "bundle.not_a_directory",
                rel,
                f"run bundle path is not a directory: {bundle}",
            )
        ]

    manifest = _find_manifest(bundle)
    if manifest is None:
        issues.append(
            Issue(
                "error",
                "bundle.missing_manifest",
                rel,
                "run bundle missing required manifest "
                f"(expected one of {list(MANIFEST_NAMES)}); "
                "add run_manifest.json",
            )
        )
    else:
        issues.extend(
            validate_manifest_file(
                manifest, rel_root=root, check_privacy=check_privacy
            )
        )

    events_files = _find_events_files(bundle)
    if not events_files:
        issues.append(
            Issue(
                "error",
                "bundle.missing_events",
                rel,
                "run bundle missing required events JSONL "
                f"(expected one of {list(EVENTS_JSONL_NAMES)} or *{EVENTS_JSONL_SUFFIX}); "
                "add events.jsonl with at least one v2 record",
            )
        )
    else:
        for ef in events_files:
            issues.extend(
                validate_jsonl_file(ef, rel_root=root, check_privacy=check_privacy)
            )

    condition = _find_condition(bundle)
    if condition is not None:
        issues.extend(
            validate_condition_file(
                condition, rel_root=root, check_privacy=check_privacy
            )
        )

    return issues


def _looks_like_bundle(path: Path) -> bool:
    """Heuristic: directory is a run bundle if it has/should have manifest+events."""
    if not path.is_dir():
        return False
    # Explicit marker or known layout
    if (path / ".run_bundle").is_file():
        return True
    if _find_manifest(path) is not None:
        return True
    if _find_events_files(path):
        return True
    # Named like a fixture bundle
    name = path.name.lower()
    if "bundle" in name:
        return True
    return False


def validate_path(
    path: str | Path,
    *,
    check_privacy: bool = True,
    check_schemas: bool = True,
    rel_root: Path | None = None,
) -> list[Issue]:
    """Validate a file or directory.

    - File: dispatched by name/suffix (manifest, condition, jsonl, or privacy-only)
    - Directory that looks like a run bundle: ``validate_bundle``
    - Other directories: walk children; optionally verify repo ``schemas/v2``
    """
    target = Path(path)
    root = rel_root if rel_root is not None else (
        target if target.is_dir() else target.parent
    )
    issues: list[Issue] = []

    if not target.exists():
        return [
            Issue(
                "error",
                "path.missing",
                str(target),
                f"path does not exist: {target}",
            )
        ]

    if target.is_file():
        return _validate_single_file(
            target, rel_root=root, check_privacy=check_privacy
        )

    # Directory
    if check_schemas:
        # If this looks like a repo root (has schemas/v2), check schemas
        schemas_v2 = target / "schemas" / "v2"
        if schemas_v2.is_dir():
            issues.extend(
                validate_schemas_present(schemas_v2, rel_root=root)
            )
        elif target.name == "v2" and (target / "run_manifest.schema.json").exists():
            issues.extend(validate_schemas_present(target, rel_root=root))

    if _looks_like_bundle(target):
        issues.extend(
            validate_bundle(
                target, check_privacy=check_privacy, rel_root=root
            )
        )
        return issues

    # Generic directory walk: validate known artifacts, privacy-scan text files
    for child in sorted(target.rglob("*")):
        if not child.is_file():
            continue
        # Skip venv / caches
        parts = set(child.parts)
        if any(p in parts for p in (".venv", ".git", "__pycache__", "node_modules")):
            continue
        name = child.name
        suffix = child.suffix.lower()
        if name in MANIFEST_NAMES or (
            name.endswith(".json") and "manifest" in name
        ):
            # Only treat as run_manifest if event_type says so or name matches
            if name in MANIFEST_NAMES:
                issues.extend(
                    validate_manifest_file(
                        child, rel_root=root, check_privacy=check_privacy
                    )
                )
                continue
        if name in CONDITION_NAMES or (
            suffix == ".json" and "condition" in name and "schema" not in name
        ):
            if name in CONDITION_NAMES or child.parent.name in (
                "conditions",
                "validator",
            ):
                # Be conservative: only auto-validate known condition names
                if name in CONDITION_NAMES:
                    issues.extend(
                        validate_condition_file(
                            child, rel_root=root, check_privacy=check_privacy
                        )
                    )
                    continue
        if _is_events_jsonl(name) or suffix == ".jsonl":
            issues.extend(
                validate_jsonl_file(
                    child, rel_root=root, check_privacy=check_privacy
                )
            )
            continue
        if check_privacy and suffix in _TEXT_SUFFIXES:
            try:
                text = _read_text(child)
            except OSError:
                continue
            issues.extend(scan_privacy(text, rel_path=_rel(child, root)))

    return issues


def _validate_single_file(
    path: Path,
    *,
    rel_root: Path,
    check_privacy: bool,
) -> list[Issue]:
    name = path.name
    suffix = path.suffix.lower()
    if name in MANIFEST_NAMES or name.endswith(".manifest.json"):
        return validate_manifest_file(
            path, rel_root=rel_root, check_privacy=check_privacy
        )
    if name in CONDITION_NAMES or (
        suffix == ".json" and "condition" in name.lower()
    ):
        return validate_condition_file(
            path, rel_root=rel_root, check_privacy=check_privacy
        )
    if _is_events_jsonl(name) or suffix == ".jsonl":
        return validate_jsonl_file(
            path, rel_root=rel_root, check_privacy=check_privacy
        )
    if suffix == ".json":
        # Try as manifest if event_type is run_manifest; else privacy only
        issues: list[Issue] = []
        try:
            text = _read_text(path)
        except OSError as exc:
            return [Issue("error", "file.unreadable", _rel(path, rel_root), str(exc))]
        if check_privacy:
            issues.extend(scan_privacy(text, rel_path=_rel(path, rel_root)))
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            issues.append(
                Issue(
                    "error",
                    "file.invalid_json",
                    _rel(path, rel_root),
                    f"not valid JSON: {exc}",
                )
            )
            return issues
        if isinstance(data, Mapping) and data.get("event_type") == "run_manifest":
            try:
                validate_record(data, event_type="run_manifest")
            except SchemaV2Error as exc:
                issues.append(
                    Issue(
                        "error",
                        "manifest.schema",
                        _rel(path, rel_root),
                        f"run_manifest schema validation failed: {exc}",
                    )
                )
        elif isinstance(data, Mapping) and {
            "controller_tier",
            "map_name",
            "analysis_intent",
        }.issubset(data.keys()):
            try:
                validate_condition(data)
            except ConditionValidationError as exc:
                issues.append(
                    Issue(
                        "error",
                        "condition.invalid",
                        _rel(path, rel_root),
                        f"condition registry rejected condition: {exc}",
                    )
                )
        return issues

    # Other text: privacy only
    if check_privacy and suffix in _TEXT_SUFFIXES:
        try:
            text = _read_text(path)
        except OSError as exc:
            return [Issue("error", "file.unreadable", _rel(path, rel_root), str(exc))]
        return scan_privacy(text, rel_path=_rel(path, rel_root))

    return []


def issues_to_dicts(issues: Sequence[Issue]) -> list[dict[str, Any]]:
    return [asdict(i) for i in issues]


def has_errors(issues: Iterable[Issue]) -> bool:
    return any(i.severity == "error" for i in issues)


def format_report(issues: Sequence[Issue], *, path: str | Path) -> str:
    lines: list[str] = [f"Research validator: {path}"]
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    if not issues:
        lines.append("OK — no issues found.")
        return "\n".join(lines) + "\n"
    for issue in issues:
        lines.append(issue.format_line())
    lines.append(
        f"Summary: {len(errors)} error(s), {len(warnings)} warning(s)."
    )
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scplay.research_validator",
        description=(
            "Validate research configuration, schemas, manifests, JSONL "
            "records, privacy rules, and run-bundle artifacts."
        ),
    )
    parser.add_argument(
        "path",
        type=str,
        help="File or directory to validate (run bundle, fixture, or repo root)",
    )
    parser.add_argument(
        "--no-privacy",
        action="store_true",
        help="Skip privacy heuristics (not recommended for committed fixtures)",
    )
    parser.add_argument(
        "--no-schemas",
        action="store_true",
        help="Skip schemas/v2 presence check when validating a directory",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit issues as JSON array instead of human-readable text",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    target = Path(args.path)
    issues = validate_path(
        target,
        check_privacy=not args.no_privacy,
        check_schemas=not args.no_schemas,
    )

    if args.as_json:
        print(json.dumps(issues_to_dicts(issues), indent=2))
    else:
        sys.stdout.write(format_report(issues, path=target))

    return 1 if has_errors(issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
