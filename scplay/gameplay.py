"""Gameplay instruction presets (system prompts + behavior flags)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
INSTRUCTIONS_DIR = _ROOT / "gameplay" / "instructions"


@dataclass
class GameplayInstructions:
    id: str
    title: str
    behavior: str  # aggressive | defense_only | ...
    body: str
    path: Path | None = None

    @property
    def system_prompt(self) -> str:
        return (
            f"Gameplay mode: {self.title} ({self.id})\n"
            f"Behavior flag: {self.behavior}\n\n"
            f"{self.body.strip()}"
        )


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_raw = text[3:end].strip()
    body = text[end + 4 :].lstrip("\n")
    meta: dict[str, str] = {}
    for line in fm_raw.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, body


def list_instruction_ids() -> list[str]:
    if not INSTRUCTIONS_DIR.is_dir():
        return []
    return sorted(p.stem for p in INSTRUCTIONS_DIR.glob("*.md"))


def load_instructions(name_or_path: str) -> GameplayInstructions:
    """Load by preset id (defense_only) or a filesystem path to a .md file."""
    candidate = Path(name_or_path)
    if candidate.is_file():
        path = candidate
    else:
        path = INSTRUCTIONS_DIR / f"{name_or_path}.md"
        if not path.is_file():
            known = ", ".join(list_instruction_ids()) or "(none)"
            raise FileNotFoundError(
                f"Unknown gameplay instructions {name_or_path!r}. "
                f"Presets: {known}. Or pass a path to a .md file."
            )
    text = path.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(text)
    return GameplayInstructions(
        id=meta.get("id", path.stem),
        title=meta.get("title", path.stem),
        behavior=meta.get("behavior", "aggressive"),
        body=body,
        path=path,
    )
