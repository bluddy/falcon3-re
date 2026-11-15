"""
Examine raw PEOPLE.DAT data to understand the actual format.
If faces are "pixellated messes", we're reading the format wrong.
"""
import struct
from pathlib import Path

def examine_raw_data():
    """Look at raw bytes to find patterns."""
    
    with open('../game/PEOPLE.IDX', 'rb') as f:
        idx_data = f.read()
    
    with open('../game/PEOPLE.DAT', 'rb') as f:
        dat_data = f.read()
    
    print("RAW DATA EXAMINATION - PEOPLE.DAT")
    print("=" * 80)
    
    # Get first face
    offset, size = struct.unpack('<HH', idx_data[0:4])
    face0 = dat_data[offset:offset+size]
    
    print(f"Face 0: {size} bytes at offset {offset}")
    print(f"\nFirst 100 bytes (hex):")
    for i in range(0, min(100, len(face0)), 16):
        hex_line = ' '.join(f'{b:02X}' for b in face0[i:i+16])
        asc_line = ''.join(chr(b) if 32 <= b < 127 else '.' for b in face0[i:i+16])
        print(f"{i:04X}: {hex_line:<48} {asc_line}")
    
    print(f"\n" + "=" * 80)
    print("BYTE VALUE ANALYSIS")
    print("=" * 80)
    
    # Analyze byte distribution
    from collections import Counter
    
    # Skip header, look at "pixel" data
    pixel_data = face0[6:]
    counts = Counter(pixel_data)
    
    print(f"\nPixel data: {len(pixel_data)} bytes")
    print(f"Unique values: {len(counts)}")
    print(f"Min: {min(pixel_data)}, Max: {max(pixel_data)}")
    
    print(f"\nMost common bytes:")
    for val, count in counts.most_common(20):
        pct = count / len(pixel_data) * 100
        print(f"  0x{val:02X} ({val:3}): {count:4} times ({pct:5.1f}%)")
    
    # Check if it looks like compressed data
    print(f"\n" + "=" * 80)
    print("COMPRESSION CHECK")
    print("=" * 80)
    
    # If data is compressed, we'd expect:
    # - Repeated patterns
    # - Control bytes
    # - Lower entropy
    
    # Check for runs
    runs = 0
    for i in range(len(pixel_data) - 1):
        if pixel_data[i] == pixel_data[i+1]:
            runs += 1
    
    print(f"Adjacent identical bytes: {runs} / {len(pixel_data)-1} ({runs/(len(pixel_data)-1)*100:.1f}%)")
    print(f"Expected for random: ~0.4%")
    print(f"Expected for uncompressed image: 5-20%")
    print(f"Expected for RLE compressed: very low")
    
    # Look at the header more carefully
    print(f"\n" + "=" * 80)
    print("HEADER ANALYSIS")
    print("=" * 80)
    
    print(f"\nFirst 20 bytes as different interpretations:")
    print(f"  Hex: {face0[:20].hex()}")
    print(f"  Dec: {list(face0[:20])}")
    
    # Try different header lengths
    for header_len in [6, 8, 10, 12, 16, 20]:
        remaining = len(face0) - header_len
        print(f"\n  If header is {header_len} bytes:")
        print(f"    Remaining data: {remaining} bytes")
        
        # Try to find dimensions
        for h in range(10, 40):
            if remaining % h == 0:
                w = remaining // h
                if 10 <= w <= 50:
                    print(f"      Could be {w}x{h}")

if __name__ == '__main__':
    examine_raw_data()
