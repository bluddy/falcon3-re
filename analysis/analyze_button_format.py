"""
Analyze BUTTON file format to understand structure.
"""
import struct

def analyze_button_file(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"=== {filepath} ===")
    print(f"File size: {len(data)} bytes")
    print(f"First 32 bytes (hex): {' '.join(f'{b:02X}' for b in data[:32])}")
    print()
    
    # Try different header interpretations
    print("Header interpretations:")
    
    # Try: count (1B), magic (2B), then records
    if len(data) >= 3:
        count = data[0]
        magic = struct.unpack('<H', data[1:3])[0]
        print(f"  Interpretation 1: count={count}, magic=0x{magic:04X}")
        if magic == 0x0400:  # Same magic as .DAT files
            print(f"    -> Magic matches .DAT format!")
            # Remaining bytes after header
            remaining = len(data) - 3
            print(f"    -> {remaining} bytes after header")
            if count > 0:
                avg_size = remaining / count
                print(f"    -> Average record size: {avg_size:.1f} bytes")
    
    # Try: magic (2B), count (1B)
    if len(data) >= 3:
        magic = struct.unpack('<H', data[0:2])[0]
        count = data[2]
        print(f"  Interpretation 2: magic=0x{magic:04X}, count={count}")
    
    # Try: magic (2B), width (2B), height (2B) like .DAT
    if len(data) >= 6:
        magic = struct.unpack('<H', data[0:2])[0]
        width = struct.unpack('<H', data[2:4])[0]
        height = struct.unpack('<H', data[4:6])[0]
        print(f"  Interpretation 3: magic=0x{magic:04X}, w={width}, h={height}")
        print(f"    -> Pixel count: {width * height}")
        print(f"    -> Compression ratio: {(len(data) - 6) / (width * height) * 100:.2f}%")
    
    # Try: count (2B), magic (2B), then records with dimensions
    if len(data) >= 4:
        count = struct.unpack('<H', data[0:2])[0]
        magic = struct.unpack('<H', data[2:4])[0]
        print(f"  Interpretation 4: count={count}, magic=0x{magic:04X}")
        if magic == 0x0400 and count < 100:  # Reasonable count
            print(f"    -> Could be {count} records with magic 0x0400")
            remaining = len(data) - 4
            print(f"    -> {remaining} bytes for {count} records")
            if count > 0:
                avg_size = remaining / count
                print(f"    -> Average record size: {avg_size:.1f} bytes")
                
                # Try to parse first record
                offset = 4
                print(f"\n    First record structure:")
                if offset + 6 <= len(data):
                    w = struct.unpack('<H', data[offset:offset+2])[0]
                    h = struct.unpack('<H', data[offset+2:offset+4])[0]
                    print(f"      w={w}, h={h}, pixels={w*h}")
    
    print()

# Analyze all BUTTON files
for i in [1, 2, 3]:
    analyze_button_file(f'../game/BUTTON{i}')
