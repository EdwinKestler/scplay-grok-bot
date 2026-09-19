#!/usr/bin/env python3
"""CLI entry for the Day 5 repository research validator.

Examples
--------
Validate a clean run-bundle fixture (expect exit 0)::

    python scripts/validate_research.py tests/fixtures/validator/clean_bundle

Validate a privacy-unsafe fixture (expect exit 1)::

    python scripts/validate_research.py tests/fixtures/validator/privacy_unsafe

Module form::

    python -m scplay.research_validator tests/fixtures/validator/clean_bundle
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running from a checkout without PYTHONPATH when invoked as a script.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scplay.research_validator import main


if __name__ == "__main__":
    raise SystemExit(main())
