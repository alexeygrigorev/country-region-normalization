#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Country normalization audit
- Reads alias_to_canonical.csv (columns: alias, country_normalized)
- Extends alias map with extra rules (ISO-ish codes, common variants, whitespace-removed forms)
- Scans all CSV/XLS/XLSX in a ZIP or a directory
- Detects likely "country" columns
- Prints only the cleaned/normalized UNMAPPED strings (with counts)
- Saves a CSV "unmapped_normalized_counts.csv"

Usage:
  python normalize_audit.py --zip /path/to/data.zip --alias /path/to/alias_to_canonical.csv
  # or scan a folder already extracted:
  python normalize_audit.py --dir /path/to/folder --alias /path/to/alias_to_canonical.csv
"""

import argparse
import os
import re
import unicodedata
import difflib
import zipfile
from collections import Counter
from pathlib import Path

import pandas as pd


# ------------------------
# Cleaning helper (same core as your code)
# ------------------------
def clean_text(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).lower().strip()
    s = re.sub(r"^the\s+", "", s)
    s = re.sub(r"\b(republica|república|republic|rep|of)\b", " ", s)
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


region_df = pd.read_csv("country_region.csv")
alias_df = pd.read_csv("alias_to_canonical.csv")


CANONICAL_TO_REGION = dict(
    zip(region_df["country"], region_df["region"])
)
CANONICAL_NAMES = sorted(set(CANONICAL_TO_REGION.keys()))

ALIAS = dict(
    zip(alias_df["alias"], alias_df["country_normalized"])
)


# ------------------------
# Normalization function
# ------------------------
def normalize_country(raw: str, alias_map: dict):
    if pd.isna(raw) or (isinstance(raw, str) and raw.strip() == ""):
        return None, None, "empty"

    raw_clean = clean_text(str(raw))
    no_space = raw_clean.replace(" ", "")

    # 1. Alias lookup (clean + no-space)
    for cand in (raw_clean, no_space):
        if cand in alias_map and alias_map[cand]:
            canon = alias_map[cand]
            return canon, CANONICAL_TO_REGION.get(canon), "alias"

    # 2. First word fallback
    tokens = raw_clean.split()
    if tokens:
        first = tokens[0]
        if first in alias_map and alias_map[first]:
            canon = alias_map[first]
            return canon, CANONICAL_TO_REGION.get(canon), "firstword"

    # 3. Fuzzy match against canonical country list (no spaces)
    matches = difflib.get_close_matches(
        no_space,
        [clean_text(n).replace(" ", "") for n in CANONICAL_NAMES],
        n=1,
        cutoff=0.85,
    )
    if matches:
        matched = matches[0]
        for name in CANONICAL_NAMES:
            if clean_text(name).replace(" ", "") == matched:
                return name, CANONICAL_TO_REGION.get(name), "fuzzy"

    return None, None, "unmapped"

