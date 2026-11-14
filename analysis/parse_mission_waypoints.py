#!/usr/bin/env python3
"""Parse waypoints from mission files."""

import struct
import sys
from pathlib import Path

def parse_waypoint_11byte(data, offset):
    """
    Parse 11-byte waypoint with 0x01 prefix.
    
    Structure:
      +0x00: marker (0x01)
      +0x01: x_coord (uint8)
      +0x02: unknown_1 (uint8)
      +0x03: marker_1 (int16, constant -8 or -2)
      +0x05: y_coord (uint8)
      +0x06: unknown_2 (uint8)
      +0x07: marker_2 (int16, constant -12 or -9)
      +0x09: constant (uint16, always 16)
    """
    
    if data[offset] != 0x01:
        return None
    
    return {
        'offset': offset,
        'marker': data[offset],
        'x': data[offset + 1],
        'unknown_1': data[offset + 2],
        'marker_1': struct.unpack('<h', data[offset+3:offset+5])[0],
        'y': data[offset + 5],
        'unknown_2': data[offset + 6],
        'marker_2': struct.unpack('<h', data[offset+7:offset+9])[0],
        'constant': struct.unpack('<H', data[offset+9:offset+11])[0],
        'size': 11,
    }

def parse_waypoint_10byte(data, offset):
    """
    Parse 10-byte waypoint (duplicate without 0x01 prefix).
    
    Same structure as 11-byte but without leading marker byte.
    """
    
    return {
        'offset': offset,
        'x': data[offset],
        'unknown_1': data[offset + 1],
        'marker_1': struct.unpack('<h', data[offset+2:offset+4])[0],
        'y': data[offset + 4],
        'unknown_2': data[offset + 5],
        'marker_2': struct.unpack('<h', data[offset+6:offset+8])[0],
        'constant': struct.unpack('<H', data[offset+8:offset+10])[0],
        'size': 10,
    }

def find_waypoints(data, debug=False):
    """
    Find all waypoint pairs in a mission file.
    
    Returns list of waypoint pairs, where each pair is (11-byte, 10-byte).
    """
    
    waypoints = []
    i = 0
    
    if debug:
        print(f'[DEBUG] Scanning {len(data)} bytes for waypoints')
        print(f'[DEBUG] Will check offsets 0-{len(data)-21} (0x{len(data)-21:04X})')
        print()
    
    while i <= len(data) - 21:  # Need at least 21 bytes for a pair
        # Look for 0x01 prefix
        if data[i] == 0x01:
            if debug:
                print(f'[DEBUG] Found 0x01 at offset 0x{i:04X}')
            
            # Try to parse as 11-byte waypoint
            wp11 = parse_waypoint_11byte(data, i)
            
            if debug:
                if wp11:
                    print(f'[DEBUG]   Parsed as 11-byte waypoint, constant={wp11["constant"]}')
                else:
                    print(f'[DEBUG]   parse_waypoint_11byte returned None')
            
            if wp11 and wp11['constant'] == 16:
                # Check if followed by 10-byte duplicate
                if i + 11 <= len(data) - 10:
                    wp10 = parse_waypoint_10byte(data, i + 11)
                    
                    if debug:
                        print(f'[DEBUG]   10-byte at 0x{i+11:04X}: wp11={wp11["x"]},{wp11["y"]} wp10={wp10["x"]},{wp10["y"]} m1={wp11["marker_1"]}/{wp10["marker_1"]} m2={wp11["marker_2"]}/{wp10["marker_2"]} const={wp10["constant"]}')
                    
                    # Verify it's a duplicate (same coords and markers and constant)
                    if (wp10['x'] == wp11['x'] and
                        wp10['y'] == wp11['y'] and
                        wp10['marker_1'] == wp11['marker_1'] and
                        wp10['marker_2'] == wp11['marker_2'] and
                        wp10['constant'] == 16):
                        
                        if debug:
                            print(f'[DEBUG]   MATCH! Adding waypoint pair')
                        
                        waypoints.append((wp11, wp10))
                        i += 21  # Skip both waypoints
                        continue
                    else:
                        if debug:
                            print(f'[DEBUG]   NO MATCH')
                else:
                    if debug:
                        print(f'[DEBUG]   Not enough space for 10-byte duplicate: {i+11} < {len(data)-10}')
        
        i += 1
    
    if debug:
        print(f'[DEBUG] Done scanning, found {len(waypoints)} waypoints')
        print()
    
    return waypoints

def print_waypoint(wp_pair, index):
    """Print a waypoint pair in human-readable format."""
    
    wp11, wp10 = wp_pair
    
    print(f'Waypoint {index}:')
    print(f'  Offset:      0x{wp11["offset"]:04X} (11-byte with prefix)')
    print(f'  Coordinates: X={wp11["x"]:3d}, Y={wp11["y"]:3d}')
    print(f'  Position:    {wp11["x"]/256*100:5.1f}% across, {wp11["y"]/256*100:5.1f}% down')
    print(f'  Unknown:     u1={wp11["unknown_1"]:3d}, u2={wp11["unknown_2"]:3d}')
    print(f'  Markers:     {wp11["marker_1"]:4d}, {wp11["marker_2"]:4d}')
    print(f'  Duplicate:   0x{wp10["offset"]:04X} (10-byte)')
    print()

def analyze_waypoints(waypoints):
    """Analyze patterns in waypoints."""
    
    if not waypoints:
        print('No waypoints found')
        return
    
    print('=== WAYPOINT ANALYSIS ===')
    print()
    print(f'Total waypoints: {len(waypoints)}')
    print(f'Total bytes:     {len(waypoints) * 21}')
    print()
    
    # Gather statistics
    x_coords = [wp[0]['x'] for wp in waypoints]
    y_coords = [wp[0]['y'] for wp in waypoints]
    u1_values = [wp[0]['unknown_1'] for wp in waypoints]
    u2_values = [wp[0]['unknown_2'] for wp in waypoints]
    marker1_values = [wp[0]['marker_1'] for wp in waypoints]
    marker2_values = [wp[0]['marker_2'] for wp in waypoints]
    
    print('Coordinate ranges:')
    print(f'  X: {min(x_coords)}-{max(x_coords)} (span: {max(x_coords)-min(x_coords)})')
    print(f'  Y: {min(y_coords)}-{max(y_coords)} (span: {max(y_coords)-min(y_coords)})')
    print()
    
    print('Unknown byte ranges:')
    print(f'  Unknown_1: {min(u1_values)}-{max(u1_values)} (unique: {len(set(u1_values))})')
    print(f'  Unknown_2: {min(u2_values)}-{max(u2_values)} (unique: {len(set(u2_values))})')
    print()
    
    print('Marker patterns:')
    print(f'  Marker_1: {set(marker1_values)} (unique: {len(set(marker1_values))})')
    print(f'  Marker_2: {set(marker2_values)} (unique: {len(set(marker2_values))})')
    print()
    
    # Check for patterns
    if len(set(marker1_values)) == 1 and len(set(marker2_values)) == 1:
        print(f'All waypoints use same markers: {marker1_values[0]}, {marker2_values[0]}')
        print('This likely indicates:')
        print('  - Same mission type or')
        print('  - Same waypoint action type or')
        print('  - Markers encode mission-wide settings')
    else:
        print('Mixed marker values - waypoints may have different types/actions')
    
    print()

def main():
    if len(sys.argv) < 2:
        print('Usage: parse_mission_waypoints.py <mission_file>')
        print()
        print('Example: parse_mission_waypoints.py ../game/SQUAD0.MIS')
        return
    
    filename = sys.argv[1]
    
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f'Mission File Waypoint Parser')
    print('=' * 70)
    print()
    print(f'File: {Path(filename).name}')
    print(f'Size: {len(data)} bytes')
    print()
    
    # Find all waypoints
    waypoints = find_waypoints(data, debug=False)
    
    if not waypoints:
        print('No waypoints found in this file')
        return
    
    print(f'Found {len(waypoints)} waypoint pairs')
    print()
    
    # Print each waypoint
    for i, wp_pair in enumerate(waypoints):
        print_waypoint(wp_pair, i)
    
    # Analyze patterns
    analyze_waypoints(waypoints)

if __name__ == '__main__':
    main()
