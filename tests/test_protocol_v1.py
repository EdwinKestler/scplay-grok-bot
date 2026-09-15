"""Day 1 evidence: Protocol v1 document contract and reviewer checklist."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs" / "PROTOCOL_V1.md"
CHECKLIST = ROOT / "docs" / "PROTOCOL_V1_REVIEW_CHECKLIST.md"
WORK_TODO = ROOT / "docs" / "RESEARCH_WORK_TODO.md"
ROADMAP = ROOT / "docs" / "RESEARCH_ROADMAP.md"
DOCS_INDEX = ROOT / "docs" / "README.md"

REQUIRED_HEADINGS = [
    r"^## 1\. Primary research question",
    r"^## 2\. Primary hypothesis",
    r"^## 3\. Controller tiers \(T0 / T1 / T2\)",
    r"^## 4\. Primary endpoint",
    r"^## 5\. Exploratory metrics",
    r"^## 6\. Unit of analysis",
    r"^## 7\. Experimental conditions",
    r"^## 8\. Exclusions",
]

# Acceptance criterion phrasing (must be unmistakable)
T1_DISCLAIMER_PATTERNS = [
    r"T1 banter must never be interpreted as strategic model control",
    r"not be interpreted as strategic model control",
]


@pytest.fixture(scope="module")
def protocol_text() -> str:
    assert PROTOCOL.is_file(), f"missing {PROTOCOL}"
    return PROTOCOL.read_text(encoding="utf-8")


def test_protocol_file_exists():
    assert PROTOCOL.is_file()


def test_checklist_file_exists():
    assert CHECKLIST.is_file()


def test_required_sections_present(protocol_text: str):
    for pat in REQUIRED_HEADINGS:
        assert re.search(pat, protocol_text, flags=re.M), f"missing section matching {pat}"


def test_t0_t1_t2_defined(protocol_text: str):
    for tier in ("T0", "T1", "T2"):
        assert tier in protocol_text
    assert "Scripted" in protocol_text or "scripted" in protocol_text
    assert "banter" in protocol_text.lower()
    assert "macro" in protocol_text.lower()


def test_t1_banter_not_strategic_control_disclaimer(protocol_text: str):
    found = any(re.search(p, protocol_text, flags=re.I) for p in T1_DISCLAIMER_PATTERNS)
    assert found, (
        "PROTOCOL_V1.md must explicitly state that T1 banter cannot be "
        "interpreted as strategic model control"
    )


def test_checklist_mentions_t1_rule():
    text = CHECKLIST.read_text(encoding="utf-8")
    assert "T1" in text
    assert "strategic model control" in text.lower() or "strategic model control" in text


def test_docs_link_to_protocol():
    todo = WORK_TODO.read_text(encoding="utf-8")
    assert "PROTOCOL_V1.md" in todo
    roadmap = ROADMAP.read_text(encoding="utf-8")
    # Roadmap should reference the protocol once Day 1 lands
    assert "PROTOCOL_V1" in roadmap or "protocol_v1" in roadmap.lower() or "PROTOCOL_V1.md" in roadmap
    index = DOCS_INDEX.read_text(encoding="utf-8")
    assert "PROTOCOL_V1.md" in index


def test_protocol_links_checklist(protocol_text: str):
    assert "PROTOCOL_V1_REVIEW_CHECKLIST.md" in protocol_text


def test_exclusions_include_chaos_and_tier_mislabel(protocol_text: str):
    lower = protocol_text.lower()
    assert "chaos" in lower
    assert "t1" in lower and "t2" in lower
