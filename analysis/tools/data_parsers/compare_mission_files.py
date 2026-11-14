#!/usr/bin/env python3
"""Compare two mission files to understand structure."""

import struct
import sys

def load_mission(filename):
    """Load a mission file."""
    with open(filename, 'rb') as f:
        return f.read()

def compare_headers(data1, data2):
    """Compare headers of two mission files."""
    
    print('=== HEADER COMPARISON ===')
    print()
    
    # Show first 32 bytes side by side
    print('First 32 bytes:')
    print()
    print('Offset | File 1 (824b)                           | File 2 (451b)')
    print('-------|----------------------------------------|----------------------------------------')
    
    for i in range(0, min(32, len(data1), len(data2)), 16):
        hex1 = ' '.join(f'{data1[i+j]:02X}' for j in range(min(16, len(data1)-i)))
        hex2 = ' '.join(f'{data2[i+j]:02X}' for j in range(min(16, len(data2)-i)))
        print(f'0x{i:04X}  | {hex1:39s} | {hex2}')
    
    print()
    
    # Decode header fields
    print('Header field comparison:')
    print(f'  Byte 0:    {data1[0]:3d} vs {data2[0]:3d}')
    print(f'  Bytes 1-2: {struct.unpack("<H", data1[1:3])[0]:5d} vs {struct.unpack("<H", data2[1:3])[0]:5d}')
    print(f'  Byte 3:    {data1[3]:3d} vs {data2[3]:3d}')
    print(f'  Byte 4:    {data1[4]:3d} vs {data2[4]:3d}')
    print()

def find_common_patterns(data1, data2):
    """Find patterns that appear in both files."""
    
    print('=== COMMON PATTERNS ===')
    print()
    
    # Look for common byte sequences
    common = []
    
    # Check 4-byte sequences
    for i in range(len(data1) - 4):
        seq = data1[i:i+4]
        if seq in data2:
            # Avoid all-zero or all-FF
            if seq not in (b'\x00\x00\x00\x00', b'\xFF\xFF\xFF\xFF'):
                idx2 = data2.index(seq)
                common.append((i, idx2, seq))
    
    print(f'Found {len(common)} common 4-byte sequences:')
    for i, (off1, off2, seq) in enumerate(common[:10]):
        hex_str = ' '.join(f'{b:02X}' for b in seq)
        print(f'  [{i}] File1@0x{off1:04X}, File2@0x{off2:04X}: {hex_str}')
    print()

def analyze_size_difference(data1, data2):
    """Analyze what accounts for size difference."""
    
    size_diff = len(data1) - len(data2)
    
    print('=== SIZE DIFFERENCE ANALYSIS ===')
    print()
    print(f'File 1: {len(data1)} bytes')
    print(f'File 2: {len(data2)} bytes')
    print(f'Difference: {size_diff} bytes ({size_diff*100/len(data1):.1f}% larger)')
    print()
    
    # Check if it's a multiple of common record sizes
    for record_size in [6, 8, 10, 12, 16, 20, 24]:
        records = size_diff / record_size
        if records == int(records):
            print(f'  Difference = {int(records)} records of {record_size} bytes')
    
    print()

def compare_end_sections(data1, data2):
    """Compare the end sections (waypoint data)."""
    
    print('=== END SECTION COMPARISON (Waypoints) ===')
    print()
    
    # Show last 64 bytes of each
    print('Last 64 bytes:')
    print()
    print('File 1:')
    start1 = len(data1) - 64
    for i in range(0, 64, 16):
        hex_str = ' '.join(f'{data1[start1+i+j]:02X}' for j in range(16))
        print(f'  0x{start1+i:04X}: {hex_str}')
    
    print()
    print('File 2:')
    start2 = len(data2) - 64
    for i in range(0, 64, 16):
        hex_str = ' '.join(f'{data2[start2+i+j]:02X}' for j in range(16))
        print(f'  0x{start2+i:04X}: {hex_str}')
    
    print()

def scan_for_waypoint_structures(data, name):
    """Scan for 12-byte waypoint structures."""
    
    print(f'=== WAYPOINT SCAN: {name} ===')
    print()
    
    # Look for the characteristic pattern: coord, int16, coord, int16, uint16, byte
    # Pattern: XX F8 FF YY F4 FF 10 00 ZZ
    
    waypoints = []
    
    for i in range(len(data) - 12):
        # Check for the F8 FF and F4 FF markers
        if (data[i+1] == 0xF8 and data[i+2] == 0xFF and
            data[i+4] == 0xF4 and data[i+5] == 0xFF):
            
            waypoint = {
                'offset': i,
                'x': data[i],
                'alt_offset': struct.unpack('<h', data[i+1:i+3])[0],
                'y': data[i+3],
                'speed_offset': struct.unpack('<h', data[i+4:i+6])[0],
                'flags': struct.unpack('<H', data[i+6:i+8])[0],
                'action': data[i+8],
            }
            waypoints.append(waypoint)
    
    if waypoints:
        print(f'Found {len(waypoints)} potential waypoint structures:')
        for i, wp in enumerate(waypoints[:10]):
            print(f'  [{i:2d}] 0x{wp["offset"]:04X}: X={wp["x"]:3d}, Y={wp["y"]:3d}, '
                  f'Alt={wp["alt_offset"]:4d}, Spd={wp["speed_offset"]:4d}, '
                  f'Flags=0x{wp["flags"]:04X}, Action={wp["action"]:3d}')
        
        print()
        print(f'Coordinate ranges: X: {min(w["x"] for w in waypoints)}-{max(w["x"] for w in waypoints)}, '
              f'Y: {min(w["y"] for w in waypoints)}-{max(w["y"] for w in waypoints)}')
    else:
        print('No waypoint structures found with this pattern')
    
    print()
    return waypoints

def main():
    file1 = '../game/SQUAD0.MIS'
    file2 = '../game/SQUAD1.MIS'
    
    print('Mission File Comparison')
    print('=' * 70)
    print()
    
    data1 = load_mission(file1)
    data2 = load_mission(file2)
    
    compare_headers(data1, data2)
    analyze_size_difference(data1, data2)
    find_common_patterns(data1, data2)
    compare_end_sections(data1, data2)
    
    # Scan for waypoints
    wp1 = scan_for_waypoint_structures(data1, 'File 1 (824b)')
    wp2 = scan_for_waypoint_structures(data2, 'File 2 (451b)')
    
    if wp1 and wp2:
        print('=== WAYPOINT COUNT COMPARISON ===')
        print()
        print(f'File 1: {len(wp1)} waypoints')
        print(f'File 2: {len(wp2)} waypoints')
        print(f'Difference: {len(wp1) - len(wp2)} waypoints')
        print()
        print(f'Expected size difference: {(len(wp1) - len(wp2)) * 12} bytes')
        print(f'Actual size difference: {len(data1) - len(data2)} bytes')

if __name__ == '__main__':
    main()
