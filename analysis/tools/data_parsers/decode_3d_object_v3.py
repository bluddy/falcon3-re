#!/usr/bin/env python3
"""
Decode 3D object format - Pattern search approach

Looking at the hex dumps, I noticed:
- Aircraft name appears around 0x91-0x99 (e.g. "F16    ")
- After name, coordinates might start
- Need to find patterns of reasonable int16 values

Strategy: Search for sections with many values in range [-10000, +10000]
"""

import struct
import sys

def find_vertex_candidates(data, min_count=50):
    """Find offsets where vertex-like data might start"""
    candidates = []
    
    # Scan every 2-byte offset looking for stretches of reasonable coords
    for offset in range(0, len(data) - 100, 2):
        valid_count = 0
        for i in range(50):  # Check 50 consecutive words
            if offset + i*2 + 1 >= len(data):
                break
            val = struct.unpack('<h', data[offset+i*2:offset+i*2+2])[0]
            if -10000 <= val <= 10000:
                valid_count += 1
        
        if valid_count >= 40:  # 80% of values in range
            candidates.append((offset, valid_count))
    
    return candidates

def decode_3d_object_v3(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f"=== {filename} ===")
    print(f"Size: {len(data)} bytes\n")
    
    # Parse header
    vertex_count = struct.unpack('<H', data[2:4])[0]
    line_count = struct.unpack('<H', data[4:6])[0]
    
    print(f"Header says: {vertex_count} vertices, {line_count} lines\n")
    
    # Find aircraft name
    for offset in range(0x90, 0xA0):
        if offset + 7 < len(data):
            try:
                s = data[offset:offset+8].decode('ascii', errors='ignore').rstrip('\x00 ')
                if len(s) >= 3 and s.isalnum():
                    print(f"Aircraft name @ 0x{offset:02X}: '{s}'\n")
                    break
            except:
                pass
    
    # Search for vertex data
    print("Searching for vertex data patterns...\n")
    candidates = find_vertex_candidates(data)
    
    if candidates:
        print(f"Found {len(candidates)} candidate locations with vertex-like data:")
        for offset, score in candidates[:5]:  # Show top 5
            print(f"  Offset 0x{offset:04X} ({offset}): {score}/50 valid words")
        
        # Use first candidate as vertex start
        vertex_start = candidates[0][0]
        print(f"\nUsing offset 0x{vertex_start:04X} as vertex data start\n")
        
        # Parse vertices
        print(f"First 20 vertices:")
        for v in range(min(20, vertex_count)):
            offset = vertex_start + v * 6
            if offset + 5 < len(data):
                x = struct.unpack('<h', data[offset:offset+2])[0]
                y = struct.unpack('<h', data[offset+2:offset+4])[0]
                z = struct.unpack('<h', data[offset+4:offset+6])[0]
                print(f"  V{v:3d}: X={x:6d}, Y={y:6d}, Z={z:6d}")
        
        # Calculate bounds
        print(f"\nVertex data region:")
        vertex_end = vertex_start + vertex_count * 6
        print(f"  Start: 0x{vertex_start:04X} ({vertex_start})")
        print(f"  End:   0x{vertex_end:04X} ({vertex_end})")
        print(f"  Size:  {vertex_count * 6} bytes")
        
        # Parse lines/edges
        if vertex_end + line_count * 4 <= len(data):
            print(f"\nFirst 20 lines/edges:")
            valid_lines = 0
            for e in range(min(20, line_count)):
                offset = vertex_end + e * 4
                if offset + 3 < len(data):
                    v1 = struct.unpack('<H', data[offset:offset+2])[0]
                    v2 = struct.unpack('<H', data[offset+2:offset+4])[0]
                    valid = v1 < vertex_count and v2 < vertex_count
                    if valid:
                        valid_lines += 1
                    marker = "✓" if valid else "✗"
                    print(f"  Line{e:3d}: V{v1:3d} → V{v2:3d}  {marker}")
            
            print(f"\nLine validation: {valid_lines}/20 valid vertex indices")
            
            line_end = vertex_end + line_count * 4
            print(f"\nLine data region:")
            print(f"  Start: 0x{vertex_end:04X} ({vertex_end})")
            print(f"  End:   0x{line_end:04X} ({line_end})")
            print(f"  Size:  {line_count * 4} bytes")
            
            if line_end < len(data):
                print(f"\nRemaining: {len(data) - line_end} bytes (polygons/features/metadata)")

if __name__ == '__main__':
    for filename in ['game/FALCOBJ.BIN', 'game/HORNOBJ.BIN', 'game/FULCOBJ.BIN']:
        try:
            decode_3d_object_v3(filename)
            print("\n" + "="*80 + "\n")
        except Exception as e:
            print(f"Error: {e}\n")
