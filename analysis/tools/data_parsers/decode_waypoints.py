#!/usr/bin/env python3
"""Decode waypoint structures from mission files."""

import struct
import sys

def scan_for_10byte_pattern(data, name):
    """
    Scan for 10-byte waypoint pattern (no leading flag byte).
    
    Pattern: uint16 uint16 int16 uint16 int16 uint16
    Or maybe: int16 int16 int16 int16 uint16
    
    Example: B8 94 FE FF D8 DA F7 FF 10 00
    """
    
    print(f'=== SCANNING FOR 10-BYTE WAYPOINTS: {name} ===')
    print()
    
    waypoints = []
    
    # Look for patterns ending with 10 00 that have negative int16s before
    i = 0
    while i < len(data) - 10:
        if data[i+8] == 0x10 and data[i+9] == 0x00:
            # Check if we have FE FF and F7 FF markers
            marker1 = struct.unpack('<h', data[i+2:i+4])[0]
            marker2 = struct.unpack('<h', data[i+6:i+8])[0]
            
            if marker1 < 0 and marker2 < 0:
                waypoint = {
                    'offset': i,
                    'val1': struct.unpack('<H', data[i:i+2])[0],
                    'marker1': marker1,
                    'val2': struct.unpack('<H', data[i+4:i+6])[0],
                    'marker2': marker2,
                    'constant': 16,
                }
                
                raw = ' '.join(f'{data[i+j]:02X}' for j in range(10))
                waypoint['raw'] = raw
                
                waypoints.append(waypoint)
                i += 10
                continue
        
        i += 1
    
    if waypoints:
        print(f'Found {len(waypoints)} waypoint structures (10 bytes each):')
        print()
        print('Off    | Raw Data                         | Decoded')
        print('-------|----------------------------------|-----------------------------')
        
        for wp in waypoints:
            print(f'0x{wp["offset"]:04X} | {wp["raw"]} | v1={wp["val1"]:5d} '
                  f'm1={wp["marker1"]:4d} v2={wp["val2"]:5d} m2={wp["marker2"]:4d}')
        
        print()
    else:
        print('No 10-byte waypoint structures found')
    
    print()
    return waypoints

def scan_for_11byte_pattern(data, name):
    """
    Scan for 11-byte waypoint pattern observed at end of files.
    
    Pattern: byte1 byte2 marker1(int16) byte3 byte4 marker2(int16) uint16 byte5
    
    Markers appear to be constant: -8 (F8 FF) and -12 (F4 FF)
    """
    
    print(f'=== SCANNING FOR 11-BYTE WAYPOINTS: {name} ===')
    print()
    
    # Look for the characteristic markers: F8 FF and F4 FF
    waypoints = []
    
    i = 0
    while i < len(data) - 11:
        # Look for F8 FF followed later by F4 FF
        if data[i+2] == 0xF8 and data[i+3] == 0xFF:
            # Check if F4 FF appears 4 bytes later
            if i + 7 < len(data) and data[i+6] == 0xF4 and data[i+7] == 0xFF:
                # Found pattern!
                waypoint = {
                    'offset': i,
                    'flag': data[i],
                    'byte1': data[i+1],
                    'marker1': struct.unpack('<h', data[i+2:i+4])[0],
                    'byte2': data[i+4],
                    'byte3': data[i+5],
                    'marker2': struct.unpack('<h', data[i+6:i+8])[0],
                    'value': struct.unpack('<H', data[i+8:i+10])[0],
                    'byte4': data[i+10],
                }
                
                # Show raw bytes
                raw = ' '.join(f'{data[i+j]:02X}' for j in range(11))
                waypoint['raw'] = raw
                
                waypoints.append(waypoint)
                i += 11  # Skip this waypoint
                continue
        
        i += 1
    
    if waypoints:
        print(f'Found {len(waypoints)} waypoint structures (11 bytes each):')
        print()
        print('Off    | Raw Data                                | Decoded')
        print('-------|----------------------------------------|------------------------------')
        
        for wp in waypoints:
            print(f'0x{wp["offset"]:04X} | {wp["raw"]} | flag={wp["flag"]:3d} '
                  f'b1={wp["byte1"]:3d} m1={wp["marker1"]:4d} '
                  f'b2={wp["byte2"]:3d} b3={wp["byte3"]:3d} '
                  f'm2={wp["marker2"]:4d} val={wp["value"]:4d} b4={wp["byte4"]:3d}')
        
        print()
        
        # Analyze patterns
        flags = [w['flag'] for w in waypoints]
        b1s = [w['byte1'] for w in waypoints]
        b2s = [w['byte2'] for w in waypoints]
        b3s = [w['byte3'] for w in waypoints]
        m1s = [w['marker1'] for w in waypoints]
        m2s = [w['marker2'] for w in waypoints]
        vals = [w['value'] for w in waypoints]
        b4s = [w['byte4'] for w in waypoints]
        
        print('Field analysis:')
        print(f'  flag:    {set(flags)} (unique: {len(set(flags))})')
        print(f'  byte1:   {min(b1s)}-{max(b1s)} (unique: {len(set(b1s))})')
        print(f'  marker1: {set(m1s)} (constant: {len(set(m1s)) == 1})')
        print(f'  byte2:   {min(b2s)}-{max(b2s)} (unique: {len(set(b2s))})')
        print(f'  byte3:   {min(b3s)}-{max(b3s)} (unique: {len(set(b3s))})')
        print(f'  marker2: {set(m2s)} (constant: {len(set(m2s)) == 1})')
        print(f'  value:   {set(vals)} (unique: {len(set(vals))})')
        print(f'  byte4:   {set(b4s)} (unique: {len(set(b4s))})')
        
        print()
        
        # If byte1 and byte2/byte3 look like coordinates (0-255 range)
        if max(b1s) <= 255 and max(b2s) <= 255:
            print('byte1, byte2 could be X, Y coordinates (0-255 = 1/256 theater size)')
            print()
            
            # Show as coordinate pairs
            print('Waypoint coordinates:')
            for i, wp in enumerate(waypoints):
                print(f'  WP{i:2d}: ({wp["byte1"]:3d}, {wp["byte2"]:3d}) flag={wp["flag"]}')
    else:
        print('No waypoint structures found')
    
    print()
    return waypoints

def compare_waypoint_counts(wp1, wp2):
    """Compare waypoint counts between files."""
    
    print('=== WAYPOINT COUNT COMPARISON ===')
    print()
    print(f'File 1: {len(wp1)} waypoints × 11 bytes = {len(wp1) * 11} bytes')
    print(f'File 2: {len(wp2)} waypoints × 11 bytes = {len(wp2) * 11} bytes')
    print(f'Waypoint data size difference: {(len(wp1) - len(wp2)) * 11} bytes')
    print()

def main():
    if len(sys.argv) < 3:
        file1 = '../game/SQUAD0.MIS'
        file2 = '../game/SQUAD1.MIS'
    else:
        file1 = sys.argv[1]
        file2 = sys.argv[2]
    
    print('Mission File Waypoint Decoder')
    print('=' * 70)
    print()
    
    with open(file1, 'rb') as f:
        data1 = f.read()
    
    with open(file2, 'rb') as f:
        data2 = f.read()
    
    wp11_f1 = scan_for_11byte_pattern(data1, f'{file1} ({len(data1)} bytes)')
    wp11_f2 = scan_for_11byte_pattern(data2, f'{file2} ({len(data2)} bytes)')
    
    wp10_f1 = scan_for_10byte_pattern(data1, f'{file1} ({len(data1)} bytes)')
    wp10_f2 = scan_for_10byte_pattern(data2, f'{file2} ({len(data2)} bytes)')
    
    # Use whichever format was found
    wp1 = wp11_f1 if wp11_f1 else wp10_f1
    wp2 = wp11_f2 if wp11_f2 else wp10_f2
    
    if wp1 and wp2:
        compare_waypoint_counts(wp1, wp2)

if __name__ == '__main__':
    main()
