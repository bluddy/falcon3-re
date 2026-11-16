"""
Try different decompression approaches on FTITLE1.
"""

import struct
from pathlib import Path

def read_word_le(data, offset):
    if offset + 2 > len(data):
        return None
    return struct.unpack('<H', data[offset:offset+2])[0]

def try_rle_at_offset(data, offset, name):
    """Try RLE decompression starting at offset."""
    print(f"\n{name}:")
    
    if offset + 4 > len(data):
        print(f"  Not enough data")
        return False
    
    width = read_word_le(data, offset)
    height = read_word_le(data, offset + 2)
    
    print(f"  Width: {width}, Height: {height}")
    
    # Sanity check
    if width == 0 or height == 0:
        print(f"  -> Zero dimension")
        return False
    
    if width > 640 or height > 480:
        print(f"  -> Too large")
        return False
    
    # Calculate expected compressed size (very rough estimate)
    # VGA planar needs width/8 bytes per row per plane
    width_bytes = (width + 7) // 8
    min_compressed = width_bytes * height * 4 // 10  # Assume at least 10:1 compression
    max_compressed = width_bytes * height * 4 * 2    # Assume at most 2:1 expansion
    
    available = len(data) - offset - 4
    
    print(f"  Available data: {available} bytes")
    print(f"  Expected range: {min_compressed} to {max_compressed} bytes")
    
    if available < min_compressed:
        print(f"  -> Not enough data for this size")
        return False
    
    if available > max_compressed:
        print(f"  -> Too much data for this size")
        return False
    
    print(f"  -> POSSIBLE! Size is reasonable")
    return True

def scan_for_dimensions(data):
    """Scan file for reasonable VGA dimensions."""
    print("Scanning for VGA dimension pairs...")
    
    candidates = []
    
    for offset in range(0, min(len(data) - 4, 100)):
        w = read_word_le(data, offset)
        h = read_word_le(data, offset + 2)
        
        if w and h and 16 <= w <= 320 and 16 <= h <= 200:
            candidates.append((offset, w, h))
            print(f"  Offset {offset}: {w}x{h}")
    
    return candidates

def main():
    filepath = Path("..") / "game" / "FTITLE1"
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"FTITLE1: {len(data)} bytes")
    print("="*80)
    
    # Try different offsets
    try_rle_at_offset(data, 0, "Offset 0 (no header)")
    try_rle_at_offset(data, 2, "Offset 2 (skip 1 word)")
    try_rle_at_offset(data, 4, "Offset 4 (skip 2 words)")  
    try_rle_at_offset(data, 6, "Offset 6 (skip 3 words)")
    
    # Scan for reasonable dimensions
    print("\n" + "="*80)
    candidates = scan_for_dimensions(data)
    
    if candidates:
        print(f"\nFound {len(candidates)} possible dimension pairs")
    else:
        print("\nNo reasonable VGA dimensions found in first 100 bytes")
    
    # Try interpreting as different format
    print("\n" + "="*80)
    print("Other format possibilities:")
    
    # Maybe it's a reference/pointer file?
    print("\nFirst 16 words as integers:")
    for i in range(16):
        if i * 2 + 2 <= len(data):
            val = read_word_le(data, i * 2)
            print(f"  Word {i}: {val:5d} (0x{val:04X})")

if __name__ == "__main__":
    main()
