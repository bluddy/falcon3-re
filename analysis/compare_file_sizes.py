"""
Compare actual file sizes with loader expectations.
"""

import os
from pathlib import Path

# From IDA analysis
EXPECTED_SIZES = {
    'PICFONT': {'idx': 28, 'dat': 427},
    'MADFONT': {'idx': 364, 'dat': 5649},
}

def analyze_files(game_dir):
    """Compare actual vs expected sizes."""
    print("="*80)
    print("FILE SIZE COMPARISON: Expected vs Actual")
    print("="*80)
    print()
    
    game_path = Path(game_dir)
    
    # Find all .IDX files
    idx_files = list(game_path.glob("*.IDX"))
    dat_files = list(game_path.glob("*.DAT"))
    
    print(f"Found {len(idx_files)} .IDX files and {len(dat_files)} .DAT files")
    print()
    
    # Group by base name
    pairs = {}
    for idx_file in idx_files:
        base_name = idx_file.stem
        pairs[base_name] = {'idx': idx_file, 'dat': None}
    
    for dat_file in dat_files:
        base_name = dat_file.stem
        if base_name not in pairs:
            pairs[base_name] = {'idx': None, 'dat': dat_file}
        else:
            pairs[base_name]['dat'] = dat_file
    
    # Analyze each pair
    print("Base Name         | IDX Actual | IDX Expected | DAT Actual | DAT Expected | Match")
    print("-" * 90)
    
    for base_name in sorted(pairs.keys()):
        pair = pairs[base_name]
        
        idx_actual = pair['idx'].stat().st_size if pair['idx'] else 0
        dat_actual = pair['dat'].stat().st_size if pair['dat'] else 0
        
        idx_expected = EXPECTED_SIZES.get(base_name, {}).get('idx', '?')
        dat_expected = EXPECTED_SIZES.get(base_name, {}).get('dat', '?')
        
        idx_match = "OK" if isinstance(idx_expected, int) and idx_actual == idx_expected else "NO" if isinstance(idx_expected, int) else "-"
        dat_match = "OK" if isinstance(dat_expected, int) and dat_actual == dat_expected else "NO" if isinstance(dat_expected, int) else "-"
        
        match_str = f"{idx_match} / {dat_match}"
        
        print(f"{base_name:17} | {idx_actual:10} | {str(idx_expected):12} | {dat_actual:10} | {str(dat_expected):12} | {match_str}")
    
    # Detailed analysis of mismatches
    print()
    print("="*80)
    print("DETAILED MISMATCH ANALYSIS")
    print("="*80)
    print()
    
    for base_name in ['PICFONT', 'MADFONT']:
        if base_name in pairs:
            pair = pairs[base_name]
            expected = EXPECTED_SIZES[base_name]
            
            print(f"\n{base_name}:")
            
            if pair['idx']:
                idx_actual = pair['idx'].stat().st_size
                idx_expected = expected['idx']
                idx_diff = idx_actual - idx_expected
                print(f"  IDX: {idx_actual} bytes (expected {idx_expected})")
                if idx_diff != 0:
                    print(f"    MISMATCH: {'+' if idx_diff > 0 else ''}{idx_diff} bytes")
                else:
                    print(f"    *** MATCH ***")
            
            if pair['dat']:
                dat_actual = pair['dat'].stat().st_size
                dat_expected = expected['dat']
                dat_diff = dat_actual - dat_expected
                print(f"  DAT: {dat_actual} bytes (expected {dat_expected})")
                if dat_diff != 0:
                    print(f"    MISMATCH: {'+' if dat_diff > 0 else ''}{dat_diff} bytes")
                    print(f"    Percentage: {dat_actual/dat_expected*100:.1f}% of expected")
                else:
                    print(f"    *** MATCH ***")
    
    # Check for files with no loaders
    print()
    print("="*80)
    print("FILES WITH NO KNOWN LOADERS")
    print("="*80)
    print()
    
    for base_name in sorted(pairs.keys()):
        if base_name not in EXPECTED_SIZES:
            pair = pairs[base_name]
            idx_size = pair['idx'].stat().st_size if pair['idx'] else 0
            dat_size = pair['dat'].stat().st_size if pair['dat'] else 0
            print(f"{base_name:17} | IDX: {idx_size:6} | DAT: {dat_size:6}")
    
    print()
    print("These files might be:")
    print("  1. Loaded by a generic loader (no specific string reference)")
    print("  2. Loaded by overlay code (not in main executable)")
    print("  3. Unused/deprecated files")

if __name__ == "__main__":
    game_dir = r"C:\Users\ybarnoy\projects\falcon3\game"
    analyze_files(game_dir)
