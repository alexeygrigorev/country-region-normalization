#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Country normalization CLI tool
- Reads a CSV file and normalizes country columns
- Creates an output file with '_out' suffix containing normalized countries
- Reports unmapped values with counts >= 2

Usage:
  python normalize.py input.csv
"""

import argparse
import re
import unicodedata
import difflib
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


# Load data files from script directory
script_dir = Path(__file__).parent
region_df = pd.read_csv(script_dir / "country_region.csv")
alias_df = pd.read_csv(script_dir / "alias_to_canonical.csv")


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


def detect_country_columns(df):
    """Detect columns that likely contain country data."""
    country_keywords = ['country', 'nation', 'pais', 'land', 'location', 'origin']
    potential_columns = []
    
    for col in df.columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in country_keywords):
            potential_columns.append(col)
    
    # If no obvious country columns, look for columns with country-like values
    if not potential_columns:
        for col in df.columns:
            if df[col].dtype == 'object':  # Text columns only
                sample_values = df[col].dropna().head(20).astype(str)
                country_like_count = 0
                for val in sample_values:
                    normalized, _, _ = normalize_country(val, ALIAS)
                    if normalized:
                        country_like_count += 1
                
                # If more than 30% of sample values look like countries
                if len(sample_values) > 0 and country_like_count / len(sample_values) > 0.3:
                    potential_columns.append(col)
    
    return potential_columns


def process_csv(input_path):
    """Process a CSV file and normalize country columns."""
    print(f"Processing: {input_path}")
    
    # Read the CSV
    df = pd.read_csv(input_path)
    
    # Detect country columns
    country_columns = detect_country_columns(df)
    
    if not country_columns:
        print("No country columns detected in the CSV file.")
        return None, {}
    
    print(f"Detected country column(s): {', '.join(country_columns)}")
    
    # Process each country column
    unmapped_counts = Counter()
    df_normalized = df.copy()
    
    for col in country_columns:
        print(f"Normalizing column: {col}")
        normalized_values = []
        region_values = []
        
        for value in df[col]:
            normalized, region, status = normalize_country(value, ALIAS)
            
            if status == "unmapped" and pd.notna(value) and str(value).strip():
                cleaned_value = clean_text(str(value))
                if cleaned_value:  # Only count non-empty cleaned values
                    unmapped_counts[cleaned_value] += 1
            
            normalized_values.append(normalized if normalized else value)
            region_values.append(region if region else None)
        
        # Update the country column with normalized values
        df_normalized[col] = normalized_values
        
        # Add a new region column (insert it right after the country column)
        col_index = df_normalized.columns.get_loc(col)
        region_col_name = f"{col}_region"
        
        # Insert the region column after the country column
        df_normalized.insert(col_index + 1, region_col_name, region_values)
    
    return df_normalized, unmapped_counts


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Normalize country names in CSV files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python normalize.py data.csv
  python normalize.py /path/to/my_data.csv
        """
    )
    
    parser.add_argument(
        'input_csv',
        help='Path to the input CSV file'
    )
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input_csv)
    if not input_path.exists():
        print(f"Error: File '{input_path}' not found.")
        return 1
    
    if not input_path.suffix.lower() == '.csv':
        print(f"Error: File '{input_path}' is not a CSV file.")
        return 1
    
    try:
        # Process the CSV
        df_normalized, unmapped_counts = process_csv(input_path)
        
        if df_normalized is None:
            return 1
        
        # Generate output filename
        output_path = input_path.parent / f"{input_path.stem}_out{input_path.suffix}"
        
        # Save normalized CSV
        df_normalized.to_csv(output_path, index=False)
        print(f"Normalized CSV saved to: {output_path}")
        
        # Generate report for unmapped values with count >= 2
        significant_unmapped = {k: v for k, v in unmapped_counts.items() if v >= 2}
        
        if significant_unmapped:
            print("\n" + "="*50)
            print("UNMAPPED VALUES REPORT (count >= 2)")
            print("="*50)
            
            # Sort by count (descending)
            for value, count in sorted(significant_unmapped.items(), key=lambda x: x[1], reverse=True):
                print(f"{count:4d} | {value}")
            
            print(f"\nTotal unmapped values with count >= 2: {len(significant_unmapped)}")
            print(f"Total unmapped occurrences: {sum(significant_unmapped.values())}")
        else:
            print("\nNo unmapped values with count >= 2 found.")
        
        return 0
        
    except Exception as e:
        print(f"Error processing file: {e}")
        return 1


if __name__ == "__main__":
    exit(main())

