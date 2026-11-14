#!/usr/bin/env python3
"""
Parse waypoints with 16-bit coordinate interpretation.

The "unknown" bytes are actually the HIGH bytes of 16-bit coordinates.
"""

import struct
import sys

def parse_waypoint_16bit(data, offset):
    """
    Parse waypoint with 16-bit coordinates.
    
    Structure (11 bytes):
      +0x00: marker (0x01)
      +0x01: x_low (uint8)
      +0x02: x_high (uint8)
      +0x03: marker_1 (int16)
      +0x05: y_low (uint8)
      +0x06: y_high (uint8)
      +0x07: marker_2 (int16)
      +0x09: constant (uint16)
    
    Returns 16-bit X and Y coordinates.
    """
    
    if data[offset] != 0x01:
        return None
    
    x_low = data[offset + 1]
    x_high = data[offset + 2]
    x_coord = (x_high << 8) | x_low
    
    y_low = data[offset + 5]
    y_high = data[offset + 6]
    y_coord = (y_high << 8) | y_low
    
    marker_1 = struct.unpack('<h', data[offset+3:offset+5])[0]
    marker_2 = struct.unpack('<h', data[offset+7:offset+9])[0]
    constant = struct.unpack('<H', data[offset+9:offset+11])[0]
    
    return {
        'offset': offset,
        'x': x_coord,
        'y': y_coord,
        'x_low': x_low,
        'x_high': x_high,
        'y_low': y_low,
        'y_high': y_high,
        'marker_1': marker_1,
        'marker_2': marker_2,
        'constant': constant,
    }

def find_waypoints(data):
    """Find all waypoints in mission file."""
    
    waypoints = []
    i = 0
    
    while i <= len(data) - 21:
        if data[i] == 0x01:
            wp = parse_waypoint_16bit(data, i)
            
            if wp and wp['constant'] == 16:
                # Verify duplicate exists
                if i + 11 <= len(data) - 10:
                    # Check if 10-byte duplicate follows
                    dup_matches = True
                    for j in range(10):
                        if data[i + 11 + j] != data[i + 1 + j]:
                            dup_matches = False
                            break
                    
                    if dup_matches:
                        waypoints.append(wp)
                        i += 21  # Skip both copies
                        continue
        
        i += 1
    
    return waypoints

def main():
    if len(sys.argv) < 2:
        print('Usage: parse_waypoint_coords.py <mission_file>')
        return
    
    filename = sys.argv[1]
    
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f'Mission File: {filename}')
    print(f'Size: {len(data)} bytes')
    print()
    
    waypoints = find_waypoints(data)
    
    if not waypoints:
        print('No waypoints found')
        return
    
    print(f'Found {len(waypoints)} waypoints')
    print('=' * 80)
    print()
    
    print('WP | X_16bit | Y_16bit | X_low | X_high | Y_low | Y_high | Markers  | Offset')
    print('---|---------|---------|-------|--------|-------|--------|----------|--------')
    
    for i, wp in enumerate(waypoints):
        print(f'{i:2d} | {wp["x"]:7d} | {wp["y"]:7d} | '
              f'{wp["x_low"]:5d} | {wp["x_high"]:6d} | '
              f'{wp["y_low"]:5d} | {wp["y_high"]:6d} | '
              f'{wp["marker_1"]:3d},{wp["marker_2"]:4d} | '
              f'0x{wp["offset"]:04X}')
    
    print()
    print('Coordinate Analysis:')
    print(f'  X range: {min(w["x"] for w in waypoints)} - {max(w["x"] for w in waypoints)}')
    print(f'  Y range: {min(w["y"] for w in waypoints)} - {max(w["y"] for w in waypoints)}')
    print(f'  Span: {max(w["x"] for w in waypoints) - min(w["x"] for w in waypoints)} × '
          f'{max(w["y"] for w in waypoints) - min(w["y"] for w in waypoints)}')
    print()
    
    # Calculate distances between waypoints
    if len(waypoints) > 1:
        print('Inter-waypoint distances (16-bit coordinate space):')
        for i in range(len(waypoints) - 1):
            dx = waypoints[i+1]['x'] - waypoints[i]['x']
            dy = waypoints[i+1]['y'] - waypoints[i]['y']
            dist = (dx*dx + dy*dy) ** 0.5
            print(f'  WP{i} -> WP{i+1}: dx={dx:5d}, dy={dy:5d}, dist={dist:7.1f}')
        print()
    
    # Show as hex for pattern recognition
    print('Hex values:')
    print('WP | X (hex)  | Y (hex)  ')
    print('---|----------|----------')
    for i, wp in enumerate(waypoints):
        print(f'{i:2d} | 0x{wp["x"]:04X}   | 0x{wp["y"]:04X}')

if __name__ == '__main__':
    main()
