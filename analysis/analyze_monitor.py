"""
Analyze MONITOR.DAT/IDX - likely the setup/configuration screen graphics.
"""
import struct
from pathlib import Path

def analyze_monitor():
    """Analyze MONITOR files."""
    
    with open('../game/MONITOR.IDX', 'rb') as f:
        idx_data = f.read()
    
    with open('../game/MONITOR.DAT', 'rb') as f:
        dat_data = f.read()
    
    print("MONITOR.DAT/IDX Analysis - Setup Screen Graphics")
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
    
    # Analyze first record in detail
    print("=" * 80)
    print("FIRST RECORD ANALYSIS")
    print("=" * 80)
    
    rec0 = records[0]
    data0 = dat_data[rec0['offset']:rec0['offset']+rec0['size']]
    
    print(f"\nRecord 0: {rec0['size']} bytes")
    print(f"First 64 bytes (hex):")
    for i in range(0, min(64, len(data0)), 16):
        hex_line = ' '.join(f'{b:02X}' for b in data0[i:i+16])
        print(f"  {i:04X}: {hex_line}")
    
    # Parse header
    if len(data0) >= 6:
        magic = struct.unpack('<H', data0[0:2])[0]
        val1 = struct.unpack('<H', data0[2:4])[0]
        val2 = struct.unpack('<H', data0[4:6])[0]
        
        print(f"\nHeader interpretation:")
        print(f"  Magic: 0x{magic:04X}")
        print(f"  Val1:  {val1} (0x{val1:04X})")
        print(f"  Val2:  {val2} (0x{val2:04X})")
        
        # Check if it matches .DAT format
        if magic == 0x0400:
            print(f"  -> Standard .DAT magic! (0x0400)")
            print(f"  -> Val1/Val2 could be: X,Y coords OR width,height")
            
            # Check if they're screen coords
            if val1 <= 320 and val2 <= 200:
                print(f"  -> Both <= 320x200, could be screen coordinates")
            
            # Check if they're dimensions
            pixel_data = data0[6:]
            expected = val1 * val2
            print(f"  -> If dimensions: {val1}x{val2} = {expected} pixels expected")
            print(f"  -> Actual data: {len(pixel_data)} bytes")
            if len(pixel_data) == expected:
                print(f"  -> EXACT MATCH! Uncompressed {val1}x{val2} image!")
            elif len(pixel_data) < expected:
                ratio = len(pixel_data) / expected * 100 if expected > 0 else 0
                print(f"  -> Compressed ({ratio:.1f}% of expected)")
        
        # Try planar interpretation
        if len(data0) >= 6:
            pixel_data = data0[6:]
            print(f"\n  VGA planar 4-bit check:")
            for h in [8, 12, 16, 20, 24, 32]:
                for w in [40, 48, 56, 64, 80, 96, 112, 128, 160]:
                    expected_bytes = ((w * h) + 7) // 8 * 4
                    if expected_bytes == len(pixel_data):
                        print(f"    -> Could be {w}x{h} planar (needs {expected_bytes} bytes)")

if __name__ == '__main__':
    analyze_monitor()
