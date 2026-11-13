#!/usr/bin/env python3
"""
Decode 3D object file format (FALCOBJ.BIN, HORNOBJ.BIN, etc.)

Based on inspection, these appear to be wireframe 3D models with:
- Header with counts
- Vertex table (X, Y, Z coordinates as signed int16)
- Edge/line list (vertex index pairs)
"""

import struct
import sys

def decode_3d_object(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f"=== 3D Object File: {filename} ===")
    print(f"Total size: {len(data)} bytes (0x{len(data):X})")
    print()
    
    # Parse header (guessing structure)
    print("=== HEADER (first 32 bytes) ===")
    for i in range(0, min(32, len(data)), 2):
        word = struct.unpack('<H', data[i:i+2])[0]
        sword = struct.unpack('<h', data[i:i+2])[0]
        print(f"  +{i:02X} word: 0x{word:04X} ({word:5d}) signed: {sword:6d}")
    print()
    
    # Try to interpret as vertex count + coordinate data
    # Common 3D model format: count, then X,Y,Z triplets
    
    # Guess: first word might be vertex count
    if len(data) >= 2:
        vertex_count_guess = struct.unpack('<H', data[0:2])[0]
        print(f"=== VERTEX DATA HYPOTHESIS ===")
        print(f"If word[0] = vertex count: {vertex_count_guess} vertices")
        print(f"That would need: {vertex_count_guess * 6} bytes (3 words per vertex)")
        print()
        
        # Try parsing as vertices (int16 X, Y, Z)
        if vertex_count_guess < 1000 and vertex_count_guess > 10:
            print(f"First 16 vertices (assuming data starts at offset 8):")
            vertex_start = 8  # Skip potential header
            for v in range(min(16, vertex_count_guess)):
                offset = vertex_start + v * 6
                if offset + 5 < len(data):
                    x = struct.unpack('<h', data[offset:offset+2])[0]
                    y = struct.unpack('<h', data[offset+2:offset+4])[0]
                    z = struct.unpack('<h', data[offset+4:offset+6])[0]
                    print(f"  V{v:3d}: X={x:6d}, Y={y:6d}, Z={z:6d}  (0x{offset:04X})")
            print()
            
            # Calculate where vertex data might end
            vertex_end = vertex_start + vertex_count_guess * 6
            print(f"Vertex data would end at offset: 0x{vertex_end:04X} ({vertex_end})")
            
            if vertex_end < len(data):
                remaining = len(data) - vertex_end
                print(f"Remaining data: {remaining} bytes (0x{remaining:X})")
                print()
                
                # Try to interpret remainder as edge list
                # Edges might be word pairs (vertex indices)
                edge_count = remaining // 4  # 2 words per edge
                print(f"If remainder = edge list: {edge_count} edges")
                print(f"First 16 edges:")
                for e in range(min(16, edge_count)):
                    offset = vertex_end + e * 4
                    if offset + 3 < len(data):
                        v1 = struct.unpack('<H', data[offset:offset+2])[0]
                        v2 = struct.unpack('<H', data[offset+2:offset+4])[0]
                        valid = "✓" if v1 < vertex_count_guess and v2 < vertex_count_guess else "✗"
                        print(f"  E{e:3d}: {v1:3d} → {v2:3d}  {valid}")
    
    # Also dump raw structure for pattern recognition
    print()
    print("=== RAW STRUCTURE (first 512 bytes) ===")
    for offset in range(0, min(512, len(data)), 16):
        hex_bytes = ' '.join(f'{b:02X}' for b in data[offset:offset+16])
        words = []
        for j in range(0, 16, 2):
            if offset + j + 1 < len(data):
                w = struct.unpack('<h', data[offset+j:offset+j+2])[0]
                words.append(f"{w:6d}")
        print(f"  {offset:04X}: {hex_bytes:<48} {' '.join(words)}")

if __name__ == '__main__':
    for filename in ['game/FALCOBJ.BIN', 'game/HORNOBJ.BIN', 'game/FULCOBJ.BIN']:
        try:
            decode_3d_object(filename)
            print("\n" + "="*80 + "\n")
        except FileNotFoundError:
            print(f"File not found: {filename}\n")
