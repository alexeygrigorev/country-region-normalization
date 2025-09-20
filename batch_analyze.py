#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Batch processor to analyze multiple CSV files for country normalization
"""

import sys
from pathlib import Path
from collections import Counter

# Import from the main normalize script
sys.path.append(str(Path(__file__).parent))
from normalize import process_csv

def analyze_files(file_paths):
    """Analyze multiple CSV files and show unmapped values."""
    all_unmapped = Counter()
    
    for file_path in file_paths:
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            continue
            
        if not file_path.suffix.lower() == '.csv':
            print(f"⚠️  Skipping non-CSV file: {file_path}")
            continue
        
        print(f"\n{'='*80}")
        print(f"Processing: {file_path.name}")
        print(f"{'='*80}")
        
        try:
            df_normalized, unmapped_counts = process_csv(file_path)
            
            if df_normalized is None:
                print("❌ No country columns detected")
                continue
            
            # Collect unmapped values
            significant_unmapped = {k: v for k, v in unmapped_counts.items() if v >= 2}
            
            if significant_unmapped:
                print(f"\n📊 UNMAPPED VALUES (count >= 2):")
                print("-" * 40)
                for value, count in sorted(significant_unmapped.items(), key=lambda x: x[1], reverse=True):
                    print(f"{count:4d} | {value}")
                    all_unmapped[value] += count
                
                print(f"\nFile summary: {len(significant_unmapped)} unique unmapped values, {sum(significant_unmapped.values())} total occurrences")
            else:
                print("✅ No unmapped values with count >= 2")
                
        except Exception as e:
            print(f"❌ Error processing {file_path.name}: {e}")
    
    # Overall summary
    print(f"\n{'='*80}")
    print("OVERALL SUMMARY")
    print(f"{'='*80}")
    
    if all_unmapped:
        print("🔍 All unmapped values across all files:")
        print("-" * 50)
        for value, count in sorted(all_unmapped.items(), key=lambda x: x[1], reverse=True):
            print(f"{count:4d} | {value}")
        
        print(f"\nTotal unique unmapped values: {len(all_unmapped)}")
        print(f"Total unmapped occurrences: {sum(all_unmapped.values())}")
    else:
        print("✅ No unmapped values found across all files!")

def main():
    # List of files to process
    files = [
        r"c:\Users\alexe\Downloads\drive-download-20250920T034933Z-1-001\de-zoomcamp-2025.csv",
        r"c:\Users\alexe\Downloads\drive-download-20250920T034933Z-1-001\llm-zoomcamp-2024.csv", 
        r"c:\Users\alexe\Downloads\drive-download-20250920T034933Z-1-001\llm-zoomcamp-2025.csv",
        r"c:\Users\alexe\Downloads\drive-download-20250920T034933Z-1-001\mlops-zoomcamp-2024.csv",
        r"c:\Users\alexe\Downloads\drive-download-20250920T034933Z-1-001\mlops-zoomcamp-2025.csv",
        r"c:\Users\alexe\Downloads\drive-download-20250920T034933Z-1-001\mlzoomcamp-2024.csv",
    ]
    
    analyze_files(files)

if __name__ == "__main__":
    main()