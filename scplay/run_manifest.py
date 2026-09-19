"""Reproducible run manifest builder (Day 4 research contract).

Builds schema-v2 ``run_manifest`` records with a stable ``config_fingerprint``
over configuration-relevant fields while assigning a unique ``run_id`` per
launch.

Fingerprint inputs (canonical JSON, sorted keys, compact separators)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Included:

- ``map_name``, ``map_checksum``
- ``controller_tier``, ``controller_version``
- ``chaos``, ``realtime``, ``mode``, ``opponent``, ``seed``
- ``analysis_intent``, ``llm_provider``
- ``prompt_hash``, ``provider_model_snapshot``
- ``sc2_version``, ``python_packages``
- ``git_sha``, ``git_dirty``
- ``parameters``, ``timing_policy``

Excluded (per-launch uniqueness / envelope bookkeeping):

- ``run_id``, ``started_at_utc``, ``seq``, ``game_loop``, ``game_time_s``
- ``source``, ``event_type``, ``schema_version``
- ``config_fingerprint`` itself, ``notes``
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import uuid
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any, Callable, Final, Mapping, MutableMapping, Sequence

from scplay.schema_v2 import SCHEMA_VERSION, validate_record

DEFAULT_CONTROLLER_VERSION: Final[str] = "PlaybotSparBot/1"

# Packages probed for python_packages when not overridden.
DEFAULT_PACKAGE_NAMES: Final[tuple[str, ...]] = (
    "burnysc2",
    "sc2",
    "numpy",
    "scplay-grok-bot",
    "scplay",
)

# Fields that enter the configuration fingerprint (order is documentation only;
# canonical JSON sorts keys).
FINGERPRINT_FIELDS: Final[tuple[str, ...]] = (
    "map_name",
    "map_checksum",
    "controller_tier",
    "controller_version",
    "chaos",
    "realtime",
    "mode",
    "opponent",
    "seed",
    "analysis_intent",
    "llm_provider",
    "prompt_hash",
    "provider_model_snapshot",
    "sc2_version",
    "python_packages",
    "git_sha",
    "git_dirty",
    "parameters",
    "timing_policy",
)


@dataclass
class RunManifestConfig:
    """Configuration input for :func:`build_run_manifest`.

    Prefer this dataclass; a plain ``dict`` with the same keys is also accepted.
    """

    map_name: str
    controller_tier: str
    chaos: bool
    realtime: bool
    mode: str
    opponent: str | None = None
    seed: int | None = None
    analysis_intent: str | None = None
    llm_provider: str | None = None
    map_path: str | Path | None = None
    map_checksum_declared: str | None = None
    sc2_version: str | None = None
    controller_version: str = DEFAULT_CONTROLLER_VERSION
    prompt_text: str | None = None
    prompt_hash: str | None = None
    provider_model_snapshot: str | dict[str, Any] | None = None
    parameters: dict[str, Any] | None = None
    timing_policy: dict[str, Any] | None = None
    decision_cadence_s: float | None = None
    # Injectables for offline/deterministic tests
    git_sha: str | None = None
    git_dirty: bool | None = None
    python_packages: dict[str, str] | None = None
    run_id: str | None = None
    started_at_utc: str | None = None
    notes: dict[str, Any] | None = None
    # When True, skip live git/package probes even if injectables are None.
    skip_probes: bool = False
    repo_root: str | Path | None = None


def _as_mapping(config: RunManifestConfig | Mapping[str, Any]) -> dict[str, Any]:
    if is_dataclass(config) and not isinstance(config, type):
        return asdict(config)
    if isinstance(config, Mapping):
        return dict(config)
    raise TypeError(
        "config must be RunManifestConfig or a mapping, "
        f"got {type(config).__name__}"
    )


def sha256_hex(data: bytes | str) -> str:
    """Return lowercase sha256 hex digest of bytes or UTF-8 text."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def canonical_json(obj: Any) -> str:
    """Stable JSON for fingerprinting: sorted keys, compact, UTF-8 safe."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_config_fingerprint(payload: Mapping[str, Any]) -> str:
    """sha256 of canonical JSON over :data:`FINGERPRINT_FIELDS` only."""
    subset: dict[str, Any] = {}
    for key in FINGERPRINT_FIELDS:
        if key in payload:
            subset[key] = payload[key]
    return sha256_hex(canonical_json(subset))


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _started_at_utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def generate_run_id(*, map_name: str = "unknown") -> str:
    """Unique run id: UTC stamp + sanitized map token + short uuid."""
    stamp = _utc_now_z()
    token = "".join(ch for ch in map_name if ch.isalnum())[:32] or "map"
    short = uuid.uuid4().hex[:8]
    return f"{stamp}_{token}_{short}"


def probe_git(
    repo_root: str | Path | None = None,
) -> tuple[str | None, bool | None]:
    """Return ``(git_sha, git_dirty)`` or ``(None, None)`` if unavailable.

    Never raises: missing ``.git`` or git binary yields nulls.
    """
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[1]
    git_dir = root / ".git"
    if not git_dir.exists():
        return None, None
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if sha.returncode != 0:
            return None, None
        git_sha = (sha.stdout or "").strip() or None
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if status.returncode != 0:
            return git_sha, None
        dirty = bool((status.stdout or "").strip())
        return git_sha, dirty
    except (OSError, subprocess.SubprocessError):
        return None, None


def probe_python_packages(
    names: Sequence[str] = DEFAULT_PACKAGE_NAMES,
) -> dict[str, str]:
    """Collect importlib.metadata versions for known package names.

    Also records a placeholder ``scplay`` entry from local package metadata or
    ``"workspace"`` when the distribution is not installed.
    """
    out: dict[str, str] = {}
    for name in names:
        try:
            out[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            continue
        except Exception:
            continue
    if "scplay" not in out and "scplay-grok-bot" not in out:
        out["scplay"] = "workspace"
    # Prefer burnysc2 over bare sc2 when both resolve (burnysc2 provides sc2).
    return dict(sorted(out.items()))


def compute_map_checksum(
    *,
    map_name: str,
    map_path: str | Path | None = None,
    map_checksum_declared: str | None = None,
) -> str:
    """sha256 of map file bytes if ``map_path`` is a readable file.

    Otherwise sha256 of ``map_name`` + ``"\\0"`` + declared checksum (or empty).
    Never requires a live SC2 install.
    """
    if map_path is not None:
        path = Path(map_path)
        if path.is_file():
            return sha256_hex(path.read_bytes())
    declared = map_checksum_declared or ""
    return sha256_hex(f"{map_name}\0{declared}")


def compute_prompt_hash(prompt_text: str | None, prompt_hash: str | None = None) -> str | None:
    """Return provided ``prompt_hash`` or sha256 of ``prompt_text``; else None."""
    if prompt_hash is not None:
        return prompt_hash
    if prompt_text is None:
        return None
    return sha256_hex(prompt_text)


def _default_parameters(cfg: Mapping[str, Any]) -> dict[str, Any]:
    params = {
        "controller_tier": cfg.get("controller_tier"),
        "chaos": cfg.get("chaos"),
        "realtime": cfg.get("realtime"),
        "mode": cfg.get("mode"),
        "opponent": cfg.get("opponent"),
        "seed": cfg.get("seed"),
        "analysis_intent": cfg.get("analysis_intent"),
        "llm_provider": cfg.get("llm_provider"),
        "map_name": cfg.get("map_name"),
    }
    return params


def _default_timing_policy(cfg: Mapping[str, Any]) -> dict[str, Any]:
    policy: dict[str, Any] = {"realtime": cfg.get("realtime")}
    cadence = cfg.get("decision_cadence_s")
    if cadence is not None:
        policy["decision_cadence_s"] = cadence
    return policy


def build_run_manifest(
    config: RunManifestConfig | Mapping[str, Any],
    *,
    git_probe: Callable[[Path | None], tuple[str | None, bool | None]] | None = None,
    package_probe: Callable[[], dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Build a schema-v2 ``run_manifest`` dict that validates via schema_v2.

    ``run_id`` is unique every call unless explicitly injected. ``config_fingerprint``
    is stable for identical configuration-relevant fields (see module docstring).
    """
    cfg = _as_mapping(config)
    map_name = str(cfg["map_name"])
    controller_tier = str(cfg["controller_tier"])
    chaos = bool(cfg["chaos"])
    realtime = bool(cfg["realtime"])
    mode = str(cfg["mode"])

    skip_probes = bool(cfg.get("skip_probes", False))
    repo_root = cfg.get("repo_root")
    root_path = Path(repo_root) if repo_root is not None else None

    # Git
    git_sha = cfg.get("git_sha", None)
    git_dirty = cfg.get("git_dirty", None)
    # Distinguish "key absent" vs explicit None when using dataclass (always present).
    # For injectables: if skip_probes, keep provided values (including None).
    # If not skip_probes and both are None, probe.
    if not skip_probes and git_sha is None and git_dirty is None:
        probe = git_probe or (lambda r: probe_git(r))
        git_sha, git_dirty = probe(root_path)

    # Packages
    python_packages = cfg.get("python_packages")
    if python_packages is None and not skip_probes:
        probe_pkg = package_probe or probe_python_packages
        python_packages = probe_pkg()
    elif python_packages is not None:
        python_packages = dict(sorted(dict(python_packages).items()))

    map_checksum = compute_map_checksum(
        map_name=map_name,
        map_path=cfg.get("map_path"),
        map_checksum_declared=cfg.get("map_checksum_declared"),
    )
    prompt_hash = compute_prompt_hash(cfg.get("prompt_text"), cfg.get("prompt_hash"))

    controller_version = cfg.get("controller_version") or DEFAULT_CONTROLLER_VERSION
    sc2_version = cfg.get("sc2_version")
    provider_model_snapshot = cfg.get("provider_model_snapshot")

    parameters = cfg.get("parameters")
    if parameters is None:
        parameters = _default_parameters(
            {
                "controller_tier": controller_tier,
                "chaos": chaos,
                "realtime": realtime,
                "mode": mode,
                "opponent": cfg.get("opponent"),
                "seed": cfg.get("seed"),
                "analysis_intent": cfg.get("analysis_intent"),
                "llm_provider": cfg.get("llm_provider"),
                "map_name": map_name,
            }
        )

    timing_policy = cfg.get("timing_policy")
    if timing_policy is None:
        timing_policy = _default_timing_policy(cfg)

    run_id = cfg.get("run_id") or generate_run_id(map_name=map_name)
    started_at_utc = cfg.get("started_at_utc") or _started_at_utc_now()

    # Fingerprint payload (configuration only)
    fp_payload: dict[str, Any] = {
        "map_name": map_name,
        "map_checksum": map_checksum,
        "controller_tier": controller_tier,
        "controller_version": controller_version,
        "chaos": chaos,
        "realtime": realtime,
        "mode": mode,
        "opponent": cfg.get("opponent"),
        "seed": cfg.get("seed"),
        "analysis_intent": cfg.get("analysis_intent"),
        "llm_provider": cfg.get("llm_provider"),
        "prompt_hash": prompt_hash,
        "provider_model_snapshot": provider_model_snapshot,
        "sc2_version": sc2_version,
        "python_packages": python_packages,
        "git_sha": git_sha,
        "git_dirty": git_dirty,
        "parameters": parameters,
        "timing_policy": timing_policy,
    }
    config_fingerprint = compute_config_fingerprint(fp_payload)

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "seq": 0,
        "game_loop": 0,
        "source": "logger",
        "event_type": "run_manifest",
        "map_name": map_name,
        "controller_tier": controller_tier,
        "chaos": chaos,
        "realtime": realtime,
        "mode": mode,
        "started_at_utc": started_at_utc,
        "opponent": cfg.get("opponent"),
        "seed": cfg.get("seed"),
        "analysis_intent": cfg.get("analysis_intent"),
        "llm_provider": cfg.get("llm_provider"),
        "git_sha": git_sha,
        "git_dirty": git_dirty,
        "config_fingerprint": config_fingerprint,
        "prompt_hash": prompt_hash,
        "sc2_version": sc2_version,
        "python_packages": python_packages,
        "map_checksum": map_checksum,
        "controller_version": controller_version,
        "provider_model_snapshot": provider_model_snapshot,
        "parameters": parameters,
        "timing_policy": timing_policy,
    }
    notes = cfg.get("notes")
    if notes is not None:
        manifest["notes"] = notes

    validate_record(manifest, event_type="run_manifest")
    return manifest


def write_run_manifest(path: str | Path, manifest: Mapping[str, Any]) -> Path:
    """Write ``manifest`` as pretty JSON; parent dirs created as needed."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(dict(manifest), indent=2, sort_keys=False, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return out


__all__ = [
    "DEFAULT_CONTROLLER_VERSION",
    "FINGERPRINT_FIELDS",
    "RunManifestConfig",
    "build_run_manifest",
    "canonical_json",
    "compute_config_fingerprint",
    "compute_map_checksum",
    "compute_prompt_hash",
    "generate_run_id",
    "probe_git",
    "probe_python_packages",
    "sha256_hex",
    "write_run_manifest",
]
