#!/usr/bin/env python3
"""
Decode 3D object file format - Revised

Pattern analysis shows:
- word[0] = Total file size - 10
- word[1] = Vertex count (202 for F-16, 228 for F/A-18, 216 for MiG-29)
- word[2] = Line/edge count  
- word[8] = Large offset (likely to vertex data start)
- word[12] = Another count (possibly polygon or feature count)

Header appears to be variable length with aircraft name at ~0x91-0x99
"""

import struct
import sys

def decode_3d_object_v2(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f"=== 3D Object: {filename} ===")
    print(f"File size: {len(data)} bytes")
    
    # Parse header
    size_minus_10 = struct.unpack('<H', data[0:2])[0]
    vertex_count = struct.unpack('<H', data[2:4])[0]
    line_count = struct.unpack('<H', data[4:6])[0]
    offset_large = struct.unpack('<H', data[8:10])[0]
    feature_count = struct.unpack('<H', data[12:14])[0]
    
    print(f"\n=== HEADER ===")
    print(f"word[0]: {size_minus_10} (file_size - 10 = {len(data)} - 10 = {len(data) - 10})")
    print(f"word[1]: {vertex_count} vertices")
    print(f"word[2]: {line_count} lines/edges")
    print(f"word[4]: 0x{offset_large:04X} ({offset_large}) - likely vertex data offset")
    print(f"word[6]: {feature_count} features/polys?")
    
    # Find aircraft name (appears around 0x91-0x99)
    for offset in [0x91, 0x92, 0x93, 0x94]:
        if offset + 8 < len(data):
            try:
                name = data[offset:offset+8].decode('ascii').strip('\x00 ')
                if len(name) >= 3:
                    print(f"\nAircraft name @ 0x{offset:02X}: '{name}'")
                    break
            except:
                pass
    
    # Try to locate vertex data
    # Vertices likely stored as int16 triplets (X, Y, Z)
    print(f"\n=== VERTEX DATA (assuming @ 0x{offset_large:X}, count={vertex_count}) ===")
    vertex_start = offset_large
    
    if vertex_start + vertex_count * 6 <= len(data):
        print(f"First 10 vertices:")
        for v in range(min(10, vertex_count)):
            offset = vertex_start + v * 6
            x = struct.unpack('<h', data[offset:offset+2])[0]
            y = struct.unpack('<h', data[offset+2:offset+4])[0]
            z = struct.unpack('<h', data[offset+4:offset+6])[0]
            print(f"  V{v:3d}: X={x:6d}, Y={y:6d}, Z={z:6d}")
        
        vertex_end = vertex_start + vertex_count * 6
        print(f"\nVertex data: 0x{vertex_start:04X} - 0x{vertex_end:04X} ({vertex_count * 6} bytes)")
        
        # Look for line/edge data after vertices
        if vertex_end < len(data):
            remaining = len(data) - vertex_end
            print(f"Remaining: {remaining} bytes")
            
            # Lines might be stored as word pairs (v1_index, v2_index)
            possible_lines = remaining // 4
            print(f"\nIf lines stored as word pairs: {possible_lines} possible lines")
            print(f"Header says {line_count} lines")
            
            print(f"\nFirst 10 line records:")
            for e in range(min(10, line_count)):
                offset = vertex_end + e * 4
                if offset + 3 < len(data):
                    v1 = struct.unpack('<H', data[offset:offset+2])[0]
                    v2 = struct.unpack('<H', data[offset+2:offset+4])[0]
                    valid = "✓" if (v1 < vertex_count and v2 < vertex_count) else "✗"
                    print(f"  Line{e:3d}: {v1:3d} → {v2:3d}  {valid}")
            
            line_end = vertex_end + line_count * 4
            if line_end < len(data):
                print(f"\nLine data: 0x{vertex_end:04X} - 0x{line_end:04X} ({line_count * 4} bytes)")
                print(f"Still {len(data) - line_end} bytes remaining (likely polygon/surface data)")
    else:
        print(f"ERROR: Vertex data would extend beyond file (need {vertex_start + vertex_count * 6}, have {len(data)})")
        
        # Try different offset interpretations
        print(f"\nTrying alternate offsets...")
        for test_offset in [0x9C, 0xA0, 0xA8, 0xB0, 0xC0]:
            if test_offset + 60 < len(data):
                print(f"\nTest @ 0x{test_offset:04X}:")
                for v in range(3):
                    offset = test_offset + v * 6
                    x = struct.unpack('<h', data[offset:offset+2])[0]
                    y = struct.unpack('<h', data[offset+2:offset+4])[0]
                    z = struct.unpack('<h', data[offset+4:offset+6])[0]
                    # Check if values look reasonable (typical aircraft model coords -10000 to +10000)
                    if abs(x) < 15000 and abs(y) < 15000 and abs(z) < 15000:
                        print(f"  V{v}: X={x:6d}, Y={y:6d}, Z={z:6d}  ✓ plausible")
                    else:
                        print(f"  V{v}: X={x:6d}, Y={y:6d}, Z={z:6d}  ✗ unlikely")

if __name__ == '__main__':
    for filename in ['game/FALCOBJ.BIN', 'game/HORNOBJ.BIN', 'game/FULCOBJ.BIN']:
        try:
            decode_3d_object_v2(filename)
            print("\n" + "="*80 + "\n")
        except Exception as e:
            print(f"Error processing {filename}: {e}\n")
