#!/usr/bin/env python3
"""
Final 3D object decoder - Based on pattern observation

From hex dumps, I see:
- 0x00-0x1F: Header (32 bytes)
- 0x20-0x9x: Variable metadata/features
- 0x9x: Aircraft name (e.g. "F16    " at 0x98)
- 0xA0+: Likely start of actual coordinate data

Looking at F-16 @ 0xA0:
  7C 00 00 00 F3 FF F8 00 = 124, 0, -13, 248
These look more like aircraft coordinates than header values!
"""

import struct
import sys

def decode_final(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f"=== {filename} ===")
    print(f"Size: {len(data)} bytes\n")
    
    # Parse header
    file_size_minus_10 = struct.unpack('<H', data[0:2])[0]
    vertex_count = struct.unpack('<H', data[2:4])[0]
    line_count = struct.unpack('<H', data[4:6])[0]
    word_6 = struct.unpack('<H', data[12:14])[0]
    
    print("=== HEADER ===")
    print(f"word[0]: {file_size_minus_10} (= {len(data)} - 10)")
    print(f"word[1]: {vertex_count} vertices")
    print(f"word[2]: {line_count} lines")
    print(f"word[6]: {word_6} (polygons?)")
    
    # Find aircraft name
    for offset in range(0x90, 0xA0):
        if offset + 7 < len(data):
            try:
                s = data[offset:offset+8].decode('ascii', errors='ignore').rstrip('\x00 ')
                if len(s) >= 3 and any(c.isalpha() for c in s):
                    print(f"\nAircraft: '{s}' @ 0x{offset:02X}")
                    vertex_start = (offset + 12) & ~1  # Round to even, add some padding
                    break
            except:
                pass
    else:
        vertex_start = 0xA0  # Default guess
    
    # Try different vertex start locations
    for test_start in [0xA0, 0xA8, 0xB0, 0xB8, 0xC0]:
        print(f"\n=== Testing vertex start @ 0x{test_start:02X} ===")
        
        # Show first 5 vertices
        all_reasonable = True
        for v in range(5):
            offset = test_start + v * 6
            if offset + 5 < len(data):
                x = struct.unpack('<h', data[offset:offset+2])[0]
                y = struct.unpack('<h', data[offset+2:offset+4])[0]
                z = struct.unpack('<h', data[offset+4:offset+6])[0]
                
                # Vertices should be in reasonable range for aircraft model
                reasonable = (-5000 < x < 5000 and 
                            -5000 < y < 5000 and 
                            -5000 < z < 5000)
                all_reasonable = all_reasonable and reasonable
                
                marker = "OK" if reasonable else "??"
                print(f"  V{v}: X={x:6d}, Y={y:6d}, Z={z:6d}  [{marker}]")
        
        if all_reasonable:
            print("  ^^ This looks good! ^^")
            vertex_start = test_start
            break
    
    # Use best vertex start
    print(f"\n=== FINAL DECODE (vertex @ 0x{vertex_start:02X}) ===")
    print(f"\nFirst 15 vertices:")
    for v in range(min(15, vertex_count)):
        offset = vertex_start + v * 6
        if offset + 5 < len(data):
            x = struct.unpack('<h', data[offset:offset+2])[0]
            y = struct.unpack('<h', data[offset+2:offset+4])[0]
            z = struct.unpack('<h', data[offset+4:offset+6])[0]
            print(f"  V{v:3d}: X={x:6d}, Y={y:6d}, Z={z:6d}")
    
    vertex_end = vertex_start + vertex_count * 6
    print(f"\nVertex region: 0x{vertex_start:04X} - 0x{vertex_end:04X} ({vertex_count * 6} bytes)")
    
    # Try to parse lines
    print(f"\nFirst 15 lines (starting @ 0x{vertex_end:04X}):")
    line_start = vertex_end
    valid_count = 0
    
    for e in range(min(15, line_count)):
        offset = line_start + e * 4
        if offset + 3 < len(data):
            v1 = struct.unpack('<H', data[offset:offset+2])[0]
            v2 = struct.unpack('<H', data[offset+2:offset+4])[0]
            valid = (v1 < vertex_count and v2 < vertex_count)
            if valid:
                valid_count += 1
            marker = "OK" if valid else "!!"
            print(f"  E{e:3d}: V{v1:3d} -> V{v2:3d}  [{marker}]")
    
    print(f"\nLine validation: {valid_count}/{min(15, line_count)} have valid indices")
    
    line_end = line_start + line_count * 4
    print(f"Line region: 0x{line_start:04X} - 0x{line_end:04X} ({line_count * 4} bytes)")
    
    if line_end < len(data):
        print(f"Remaining: {len(data) - line_end} bytes (polygon data / features / metadata)")

if __name__ == '__main__':
    for filename in ['game/FALCOBJ.BIN', 'game/HORNOBJ.BIN', 'game/FULCOBJ.BIN']:
        try:
            decode_final(filename)
            print("\n" + "="*80 + "\n")
        except Exception as e:
            print(f"Error: {e}\n")
            import traceback
            traceback.print_exc()
