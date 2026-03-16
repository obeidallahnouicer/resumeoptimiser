#!/usr/bin/env python3
"""Debug entry header detection."""

import re

_DATE_START_RE = re.compile(
    r"^(January|February|March|April|May|June|July|August|September|"
    r"October|November|December|\d{4})\b",
    re.IGNORECASE,
)

_ENTRY_HEADER_RE = re.compile(r".{3,}\s*[|–—]\s*.{2,}")

test_lines = [
    "Jan 2024 – Present | Tunis, Tunisia",
    "Senior AI Engineer | TechCorp",
    "MSc Business Analytics & Generative AI | ESPRIT School of Business",
    "September 2022 – December 2023 | Remote",
    "1 Jan 2024 – Present | Tunis",
]

for line in test_lines:
    s = line.strip()
    date_match = _DATE_START_RE.match(s)
    entry_match = _ENTRY_HEADER_RE.match(s)
    print(f"Line: {s}")
    print(f"  DATE_START_RE match: {bool(date_match)}")
    print(f"  ENTRY_HEADER_RE match: {bool(entry_match)}")
    print()
