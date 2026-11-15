"""
Analyze .DAT file headers to understand what the width/height values represent.
Since decompressed size << width*height, these are NOT pixel dimensions.
"""
import struct
from pathlib import Path
from rle_decompress import parse_idx_dat, extract_dat_record, rle_decompress

def analyze_all_dat_headers():
    """Analyze headers from all .IDX/.DAT file pairs."""
    game_dir = Path('../game')
    
    # Find all .IDX files
    idx_files = sorted(game_dir.glob('*.IDX'))
    
    print("Analyzing .DAT file headers")
    print("=" * 80)
    print()
    
    all_records = []
    
    for idx_file in idx_files:
        dat_file = idx_file.with_suffix('.DAT')
        if not dat_file.exists():
            continue
        
        name = idx_file.stem
        print(f"{name}:")
        
        records = parse_idx_dat(idx_file, dat_file)
        print(f"  Records: {len(records)}")
        
        # Analyze each record
        for rec in records:
            extracted = extract_dat_record(rec['data'])
            if extracted:
                rec['extracted'] = extracted
                all_records.append({
                    'file': name,
                    **rec
                })
        
        print()
    
    # Statistical analysis
    print("\n" + "=" * 80)
    print("STATISTICAL ANALYSIS")
    print("=" * 80)
    
    # Collect all width/height values
    widths = [r['extracted']['width'] for r in all_records if 'extracted' in r]
    heights = [r['extracted']['height'] for r in all_records if 'extracted' in r]
    
    print(f"\nTotal records analyzed: {len(all_records)}")
    print(f"\nWidth values:")
    print(f"  Min: {min(widths)}, Max: {max(widths)}")
    print(f"  Unique values: {len(set(widths))}")
    print(f"  Most common: {sorted(set(widths), key=widths.count, reverse=True)[:10]}")
    
    print(f"\nHeight values:")
    print(f"  Min: {min(heights)}, Max: {max(heights)}")
    print(f"  Unique values: {len(set(heights))}")
    print(f"  Most common: {sorted(set(heights), key=heights.count, reverse=True)[:10]}")
    
    # Check if they could be coordinates
    print(f"\n" + "-" * 80)
    print("HYPOTHESIS: Width/Height are VGA screen coordinates")
    print("-" * 80)
    
    # VGA mode 13h is 320x200
    # Check if values make sense as coordinates
    print(f"\nWidth <= 320: {sum(1 for w in widths if w <= 320)} / {len(widths)}")
    print(f"Height <= 200: {sum(1 for h in heights if h <= 200)} / {len(heights)}")
    
    # Check decompressed sizes
    print(f"\n" + "-" * 80)
    print("DECOMPRESSED SIZE ANALYSIS")
    print("-" * 80)
    
    decomp_sizes = [r['extracted']['decompressed_size'] for r in all_records if 'extracted' in r]
    print(f"\nDecompressed sizes:")
    print(f"  Min: {min(decomp_sizes)}, Max: {max(decomp_sizes)}")
    print(f"  Average: {sum(decomp_sizes) / len(decomp_sizes):.1f}")
    
    # Show some examples
    print(f"\n" + "-" * 80)
    print("SAMPLE RECORDS")
    print("-" * 80)
    
    for i, rec in enumerate(all_records[:20]):
        if 'extracted' not in rec:
            continue
        ex = rec['extracted']
        w, h = ex['width'], ex['height']
        comp = ex['compressed_size']
        decomp = ex['decompressed_size']
        
        print(f"{rec['file']:12} Record {rec['index']:2}: "
              f"header=({w:3},{h:3}) "
              f"comp={comp:4}B "
              f"decomp={decomp:4}B")
    
    # Check if decompressed size correlates with anything
    print(f"\n" + "-" * 80)
    print("PATTERN SEARCH")
    print("-" * 80)
    
    # Group by width to see patterns
    from collections import defaultdict
    by_width = defaultdict(list)
    for rec in all_records:
        if 'extracted' not in rec:
            continue
        w = rec['extracted']['width']
        decomp = rec['extracted']['decompressed_size']
        by_width[w].append(decomp)
    
    print(f"\nDecompressed sizes grouped by 'width' value:")
    for w in sorted(by_width.keys())[:15]:
        sizes = by_width[w]
        avg = sum(sizes) / len(sizes)
        print(f"  Width={w:3}: {len(sizes):3} records, avg decomp={avg:6.1f}B, range={min(sizes)}-{max(sizes)}")

if __name__ == '__main__':
    analyze_all_dat_headers()
