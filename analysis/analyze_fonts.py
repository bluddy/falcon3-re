"""
Analyze font files (MADFONT, PICFONT) to understand the format.
Fonts should have clear patterns - likely one glyph per record.
"""
import struct
from pathlib import Path
from rle_decompress import parse_idx_dat, extract_dat_record

def analyze_font_file(name):
    """Analyze a specific font file."""
    idx_path = Path(f'../game/{name}.IDX')
    dat_path = Path(f'../game/{name}.DAT')
    
    if not idx_path.exists() or not dat_path.exists():
        print(f"Skipping {name} - files not found")
        return
    
    print(f"\n{'=' * 80}")
    print(f"{name} FONT ANALYSIS")
    print('=' * 80)
    
    records = parse_idx_dat(idx_path, dat_path)
    print(f"Total records: {len(records)}")
    
    # Fonts typically have 96 or so glyphs (ASCII 32-127)
    # Or 256 for extended ASCII
    print(f"Expected for ASCII font: 96 glyphs (space through ~)")
    print(f"Extended ASCII: 256 glyphs")
    
    # Analyze all records
    print(f"\nFirst 20 records:")
    print(f"{'Idx':<4} {'W':>5} {'H':>5} {'Comp':>6} {'Decomp':>6} {'Ratio':>8}")
    print("-" * 45)
    
    for i, rec in enumerate(records[:20]):
        ex = extract_dat_record(rec['data'])
        if not ex:
            continue
        
        w, h = ex['width'], ex['height']
        comp = ex['compressed_size']
        decomp = ex['decompressed_size']
        ratio = decomp / comp if comp > 0 else 0
        
        print(f"{i:<4} {w:>5} {h:>5} {comp:>6} {decomp:>6} {ratio:>8.2f}x")
    
    # Check if widths could be ASCII codes
    print(f"\n" + "-" * 80)
    print("HYPOTHESIS: Width field contains ASCII character code?")
    print("-" * 80)
    
    for i, rec in enumerate(records[:20]):
        ex = extract_dat_record(rec['data'])
        if not ex:
            continue
        
        w = ex['width']
        ascii_char = chr(w) if 32 <= w < 127 else '?'
        print(f"Record {i:2}: width={w:3} (0x{w:02X}) = '{ascii_char}' in ASCII")
    
    # Analyze unique dimensions
    print(f"\n" + "-" * 80)
    print("DIMENSION ANALYSIS")
    print("-" * 80)
    
    widths = []
    heights = []
    decomp_sizes = []
    
    for rec in records:
        ex = extract_dat_record(rec['data'])
        if ex:
            widths.append(ex['width'])
            heights.append(ex['height'])
            decomp_sizes.append(ex['decompressed_size'])
    
    print(f"\nWidths: min={min(widths)}, max={max(widths)}, unique={len(set(widths))}")
    print(f"Heights: min={min(heights)}, max={max(heights)}, unique={len(set(heights))}")
    print(f"Decompressed: min={min(decomp_sizes)}, max={max(decomp_sizes)}, avg={sum(decomp_sizes)/len(decomp_sizes):.1f}")
    
    # Check if decompressed size could be actual glyph data
    print(f"\n" + "-" * 80)
    print("GLYPH SIZE HYPOTHESIS")
    print("-" * 80)
    
    # Typical font glyph: 8x8, 8x12, 8x16, etc.
    # Decompressed size should match width * height for bitmap
    
    matches = 0
    for rec in records[:20]:
        ex = extract_dat_record(rec['data'])
        if not ex:
            continue
        
        # Try different interpretations
        w, h, decomp = ex['width'], ex['height'], ex['decompressed_size']
        
        # Could height be actual height and decomp = width * height?
        if decomp > 0:
            implied_width = decomp // h if h > 0 else 0
            if implied_width * h == decomp:
                print(f"Record {rec['index']:2}: header({w},{h}) but decomp={decomp} suggests {implied_width}x{h} glyph")
                matches += 1
    
    if matches > 0:
        print(f"\nFound {matches} records where decompressed size = implied_width × header_height")

def main():
    print("FONT FILE ANALYSIS")
    print("=" * 80)
    print("\nAnalyzing font formats to understand .DAT structure...")
    
    # Analyze different font files
    analyze_font_file('PICFONT')
    analyze_font_file('MADFONT')
    analyze_font_file('MADFONTF')
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
