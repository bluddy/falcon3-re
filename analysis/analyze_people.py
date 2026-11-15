"""
Analyze PEOPLE.DAT to see if it contains uncompressed pilot face images.
"""
import struct
from pathlib import Path
from PIL import Image

def analyze_people_records():
    """Analyze PEOPLE.IDX/DAT as potentially uncompressed images."""
    
    # Parse index
    with open('../game/PEOPLE.IDX', 'rb') as f:
        idx_data = f.read()
    
    with open('../game/PEOPLE.DAT', 'rb') as f:
        dat_data = f.read()
    
    print("PEOPLE.DAT Analysis")
    print("=" * 80)
    print(f"IDX size: {len(idx_data)} bytes")
    print(f"DAT size: {len(dat_data)} bytes")
    
    num_entries = len(idx_data) // 4
    print(f"Index entries: {num_entries}")
    print()
    
    # Parse all entries
    records = []
    for i in range(num_entries):
        pos = i * 4
        offset, size = struct.unpack('<HH', idx_data[pos:pos+4])
        records.append({
            'index': i,
            'offset': offset,
            'size': size
        })
    
    # Show all records
    print(f"{'Idx':<4} {'Offset':>6} {'Size':>6} {'End':>6}")
    print("-" * 30)
    for rec in records:
        end = rec['offset'] + rec['size']
        print(f"{rec['index']:<4} {rec['offset']:>6} {rec['size']:>6} {end:>6}")
    
    print()
    
    # Check coverage
    total_indexed = sum(r['size'] for r in records)
    print(f"Total indexed: {total_indexed} bytes")
    print(f"DAT file size: {len(dat_data)} bytes")
    print(f"Coverage: {total_indexed / len(dat_data) * 100:.1f}%")
    print()
    
    # Analyze sizes
    sizes = [r['size'] for r in records]
    print(f"Record sizes:")
    print(f"  Min: {min(sizes)}, Max: {max(sizes)}, Avg: {sum(sizes)/len(sizes):.1f}")
    print(f"  Unique sizes: {sorted(set(sizes))}")
    print()
    
    # Check if sizes could be image dimensions
    print("Checking if sizes match common image dimensions:")
    print("-" * 80)
    
    # Common pilot face sizes might be: 32x32, 40x40, 48x48, 64x64, etc.
    # With 4-byte header: 32×32+4=1028, 40×40+4=1604, 48×48+4=2308, 64×64+4=4100
    
    common_sizes = {
        1028: "32×32 + 4 byte header",
        1604: "40×40 + 4 byte header",
        2308: "48×48 + 4 byte header",
        4100: "64×64 + 4 byte header",
        1024: "32×32 no header",
        1600: "40×40 no header",
        2304: "48×48 no header",
        4096: "64×64 no header",
    }
    
    for size in sorted(set(sizes)):
        if size in common_sizes:
            print(f"  Size {size:4} = {common_sizes[size]}")
        else:
            # Try to find dimensions that match
            # Check with 4-byte header
            pixels = size - 4
            if pixels > 0:
                sqrt = int(pixels ** 0.5)
                if sqrt * sqrt == pixels:
                    print(f"  Size {size:4} = {sqrt}x{sqrt} + 4 byte header")
                else:
                    # Try common aspect ratios
                    for h in range(10, 100):
                        if pixels % h == 0:
                            w = pixels // h
                            if w <= 100 and abs(w - h) < 20:  # Reasonable face dimensions
                                print(f"  Size {size:4} = {w}x{h} + 4 byte header")
                                break
    
    print()
    
    # Check first record header
    print("First record analysis:")
    print("-" * 80)
    rec0 = records[0]
    data0 = dat_data[rec0['offset']:rec0['offset']+rec0['size']]
    
    print(f"Record 0: {rec0['size']} bytes")
    print(f"First 16 bytes (hex): {data0[:16].hex()}")
    print(f"First 16 bytes (dec): {list(data0[:16])}")
    
    # Try interpreting as width/height header
    if len(data0) >= 4:
        w = struct.unpack('<H', data0[0:2])[0]
        h = struct.unpack('<H', data0[2:4])[0]
        print(f"\nIf bytes 0-1 are width, 2-3 are height:")
        print(f"  Width: {w}, Height: {h}")
        print(f"  Expected size: {w * h + 4} bytes")
        print(f"  Actual size: {rec0['size']} bytes")
        print(f"  Match: {w * h + 4 == rec0['size']}")

if __name__ == '__main__':
    analyze_people_records()
