#!/usr/bin/env python3
"""
Decode 3D object line/edge format - understand flags and indices.
Focus on FALCOBJ.BIN (F-16).
"""

import struct
from pathlib import Path

def analyze_line_format(filepath):
    """Analyze line records, looking for patterns in 'invalid' indices."""
    data = Path(filepath).read_bytes()
    
    # Read header
    header = struct.unpack('<16H', data[0:32])
    file_size_minus_10 = header[0]
    vertex_count = header[1]
    line_count = header[2]
    
    print(f"=== {Path(filepath).name} ===")
    print(f"Vertices: {vertex_count}, Lines: {line_count}")
    print()
    
    # Vertices start at 0xA0 for F-16
    vertex_offset = 0xA0
    vertex_size = 6  # int16 x, y, z
    line_offset = vertex_offset + (vertex_count * vertex_size)
    
    print(f"Vertex data: 0x{vertex_offset:04X} - 0x{line_offset:04X}")
    print(f"Line data starts: 0x{line_offset:04X}")
    print()
    
    # Analyze line records
    lines = []
    for i in range(line_count):
        offset = line_offset + (i * 4)
        if offset + 4 > len(data):
            break
        v1, v2 = struct.unpack('<HH', data[offset:offset+4])
        lines.append((v1, v2))
    
    # Categorize lines
    valid = []
    high_bits = []
    special = []
    
    for i, (v1, v2) in enumerate(lines):
        # Check if both indices are in valid range
        if v1 < vertex_count and v2 < vertex_count:
            valid.append((i, v1, v2))
        # Check for high bit patterns
        elif v1 >= 0xFF00 or v2 >= 0xFF00:
            special.append((i, v1, v2))
        else:
            high_bits.append((i, v1, v2))
    
    print(f"Line categories:")
    print(f"  Valid (both < {vertex_count}): {len(valid)} / {line_count} ({100*len(valid)//line_count}%)")
    print(f"  Special (>=0xFF00): {len(special)} / {line_count}")
    print(f"  High bits (other): {len(high_bits)} / {line_count}")
    print()
    
    # Show first 20 lines with analysis
    print("First 20 lines:")
    print("  #   |  V1    V2   |  V1_bin            V2_bin            | Notes")
    print("------+-------------+---------------------------------------+------------------")
    for i in range(min(20, len(lines))):
        v1, v2 = lines[i]
        v1_bin = f"{v1:016b}"
        v2_bin = f"{v2:016b}"
        
        note = ""
        if v1 < vertex_count and v2 < vertex_count:
            note = "VALID"
        elif v1 >= 0xFF00:
            note = f"V1=0x{v1:04X}"
        elif v2 >= 0xFF00:
            note = f"V2=0x{v2:04X}"
        elif v1 >= vertex_count:
            note = f"V1 too large"
        elif v2 >= vertex_count:
            note = f"V2 too large"
        
        print(f"{i:4d}  | {v1:5d} {v2:5d} | {v1_bin} {v2_bin} | {note}")
    print()
    
    # Analyze bit patterns in "invalid" values
    print("Analyzing high-value patterns (V >= 0xFF00):")
    high_values = set()
    for i, v1, v2 in special:
        if v1 >= 0xFF00:
            high_values.add(v1)
        if v2 >= 0xFF00:
            high_values.add(v2)
    
    for val in sorted(high_values):
        count_v1 = sum(1 for v1, v2 in lines if v1 == val)
        count_v2 = sum(1 for v1, v2 in lines if v2 == val)
        print(f"  0x{val:04X} ({val:5d}) = {val:016b}")
        print(f"    Appears: {count_v1} times as V1, {count_v2} times as V2, total {count_v1 + count_v2}")
        
        # Try interpreting as flags + index
        if val >= 0x8000:
            # Signed interpretation
            signed = val - 65536
            print(f"    Signed: {signed}")
        
        # Try different bit splits
        idx8 = val & 0xFF
        flags8 = (val >> 8) & 0xFF
        print(f"    As [flags8:idx8]: flags=0x{flags8:02X}, idx={idx8}")
        
        idx9 = val & 0x1FF
        flags7 = (val >> 9) & 0x7F
        print(f"    As [flags7:idx9]: flags=0x{flags7:02X}, idx={idx9}")
        print()
    
    # Check for patterns: maybe every Nth line is special?
    print("Looking for structural patterns:")
    special_positions = [i for i, v1, v2 in special]
    if len(special_positions) > 1:
        gaps = [special_positions[i+1] - special_positions[i] for i in range(len(special_positions)-1)]
        print(f"  Special line positions: {special_positions[:20]}...")
        print(f"  Gaps between special lines: {gaps[:10]}...")
        if len(set(gaps)) == 1:
            print(f"  REGULAR SPACING: every {gaps[0]} lines!")
    print()
    
    # Check if lines cluster into groups
    print("Checking for record groups (lines might be part of polygon records):")
    # Look for 0xFFFF terminators
    terminators = [i for i, (v1, v2) in enumerate(lines) if v1 == 0xFFFF or v2 == 0xFFFF]
    if terminators:
        print(f"  Found {len(terminators)} potential terminators (0xFFFF)")
        print(f"  Positions: {terminators[:20]}")
        if len(terminators) > 1:
            group_sizes = [terminators[i+1] - terminators[i] - 1 for i in range(len(terminators)-1)]
            print(f"  Group sizes: {group_sizes[:10]}")
    else:
        print(f"  No 0xFFFF terminators found")
    print()
    
    # Show sample of valid lines to understand geometry
    if valid:
        print(f"Sample valid lines (connecting real vertices):")
        for i, v1, v2 in valid[:10]:
            # Read actual vertex coords
            v1_offset = vertex_offset + (v1 * 6)
            v2_offset = vertex_offset + (v2 * 6)
            x1, y1, z1 = struct.unpack('<hhh', data[v1_offset:v1_offset+6])
            x2, y2, z2 = struct.unpack('<hhh', data[v2_offset:v2_offset+6])
            
            # Compute edge length
            import math
            length = math.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)
            
            print(f"  Line {i:3d}: V{v1:3d}→V{v2:3d}  " +
                  f"({x1:5d},{y1:5d},{z1:5d}) → ({x2:5d},{y2:5d},{z2:5d})  " +
                  f"len={length:7.1f}")
    
    return {
        'vertex_count': vertex_count,
        'line_count': line_count,
        'valid_lines': len(valid),
        'special_lines': len(special),
        'high_bit_lines': len(high_bits),
        'high_values': high_values,
    }

def main():
    files = [
        'game/FALCOBJ.BIN',
        'game/HORNOBJ.BIN', 
        'game/FULCOBJ.BIN',
    ]
    
    results = {}
    for f in files:
        if Path(f).exists():
            results[f] = analyze_line_format(f)
            print("\n" + "="*80 + "\n")
    
    # Summary
    print("=== SUMMARY ===")
    for f, r in results.items():
        pct = 100 * r['valid_lines'] / r['line_count'] if r['line_count'] > 0 else 0
        print(f"{Path(f).name}: {r['valid_lines']}/{r['line_count']} valid ({pct:.0f}%)")

if __name__ == '__main__':
    main()
