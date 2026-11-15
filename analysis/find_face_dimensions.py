"""
Figure out how dimensions are stored for PEOPLE.DAT faces.
Maybe there's additional metadata after the header?
"""
import struct
from pathlib import Path

def analyze_face_headers():
    """Look for dimension data in face records."""
    
    with open('../game/PEOPLE.IDX', 'rb') as f:
        idx_data = f.read()
    
    with open('../game/PEOPLE.DAT', 'rb') as f:
        dat_data = f.read()
    
    print("Analyzing PEOPLE.DAT headers for dimension storage")
    print("=" * 80)
    
    num_entries = len(idx_data) // 4
    
    for i in range(min(10, num_entries)):
        pos = i * 4
        offset, size = struct.unpack('<HH', idx_data[pos:pos+4])
        
        data = dat_data[offset:offset+size]
        
        print(f"\nFace {i}:")
        print(f"  Total size: {size} bytes")
        print(f"  First 20 bytes: {data[:20].hex()}")
        print(f"  As words: {[struct.unpack('<H', data[j:j+2])[0] for j in range(0, min(20, len(data)), 2)]}")
        
        # Parse standard header
        magic = struct.unpack('<H', data[0:2])[0]
        val1 = struct.unpack('<H', data[2:4])[0]
        val2 = struct.unpack('<H', data[4:6])[0]
        
        print(f"  Standard: magic=0x{magic:04X}, val1={val1}, val2={val2}")
        
        # Check if there are more header bytes
        if len(data) >= 10:
            val3 = struct.unpack('<H', data[6:8])[0]
            val4 = struct.unpack('<H', data[8:10])[0]
            print(f"  Extended: val3={val3}, val4={val4}")
            
            # Try interpreting val3/val4 as dimensions
            pixels_after_10 = size - 10
            if val3 * val4 == pixels_after_10:
                print(f"  *** MATCH: {val3}x{val4} image with 10-byte header! ***")
        
        # Calculate what dimensions would work
        pixel_data_size = size - 6  # After standard header
        print(f"  Pixel data: {pixel_data_size} bytes")
        
        matches = []
        for h in range(15, 30):
            if pixel_data_size % h == 0:
                w = pixel_data_size // h
                if 20 <= w <= 45:
                    matches.append(f"{w}x{h}")
        
        if matches:
            print(f"  Possible dims (6-byte header): {', '.join(matches)}")

if __name__ == '__main__':
    analyze_face_headers()
