#!/usr/bin/env python3
"""Parse .MIS mission file structure."""

import struct
import sys

def parse_mission_header(data):
    """Parse the mission file header."""
    
    print('=== MISSION FILE HEADER ===')
    print()
    
    # First bytes likely contain counts
    if len(data) < 8:
        print('File too small')
        return {}
    
    # Try to interpret as counts
    header = {}
    
    # Byte 0: Often 0x03 in our example
    header['byte_0'] = data[0]
    print(f'Byte 0: {data[0]} (might be flight count or mission type)')
    
    # Bytes 1-2: uint16?
    val = struct.unpack('<H', data[1:3])[0]
    header['uint16_1'] = val
    print(f'Bytes 1-2: {val} (0x{val:04X})')
    
    # More header bytes
    print(f'Bytes 3-7: {" ".join(f"{data[i]:02X}" for i in range(3, min(8, len(data))))}')
    print()
    
    return header

def find_flight_structures(data):
    """Try to identify flight record structures."""
    
    print('=== FLIGHT STRUCTURE ANALYSIS ===')
    print()
    
    # Looking for pattern: ID 00 VALUE1 00 VALUE2 80/81
    # This is a 6-byte structure, not 12-byte
    
    offset = 8  # Skip header
    flights = []
    
    print('Scanning for 6-byte flight records (ID 00 VAL1 00 VAL2 FLAG):')
    print()
    
    while offset + 6 <= len(data):
        # Check for the 00 padding pattern
        if data[offset+1] == 0x00 and data[offset+3] == 0x00:
            flight = {
                'offset': offset,
                'id': data[offset],
                'value1': data[offset+2],
                'value2': data[offset+4],
                'flag': data[offset+5],
            }
            flights.append(flight)
            offset += 6
        else:
            # End of flight records
            print(f'Flight records end at offset 0x{offset:04X}')
            break
    
    if flights:
        print(f'Found {len(flights)} flight records:')
        for i, f in enumerate(flights[:20]):  # Show first 20
            print(f'  [{i:2d}] 0x{f["offset"]:04X}: ID={f["id"]:3d} ({f["id"]:02X}), '
                  f'V1={f["value1"]:3d}, V2={f["value2"]:3d}, Flag=0x{f["flag"]:02X}')
    
    print()
    return flights, offset

def find_waypoint_data(data):
    """Try to identify waypoint data (1-byte coordinates)."""
    
    print('=== WAYPOINT DATA ANALYSIS ===')
    print()
    
    # Waypoints likely near end of file
    # Look for regions with mostly non-zero, non-FF bytes
    # Coordinates are 1 byte each (0-255)
    
    # Scan last 300 bytes
    start = max(0, len(data) - 300)
    section = data[start:]
    
    print(f'Scanning last {len(section)} bytes for waypoint patterns:')
    print()
    
    # Look for sequences that could be coordinates
    # Pattern might be: X Y [altitude?] [speed?] [action?]
    
    # Show sections with high byte diversity (not all zeros or FFs)
    window = 16
    for i in range(0, len(section) - window, window):
        chunk = section[i:i+window]
        
        # Count non-zero, non-FF
        useful = sum(1 for b in chunk if 0 < b < 0xFF)
        
        if useful > 8:  # At least half are useful data
            hex_str = ' '.join(f'{b:02X}' for b in chunk)
            print(f'  0x{start+i:04X}: {hex_str}')
    
    print()

def parse_mission_file(filename):
    """Parse a complete mission file."""
    
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f'Mission file: {filename}')
    print(f'Size: {len(data)} bytes')
    print()
    
    # Parse header
    header = parse_mission_header(data)
    
    # Find flight structures
    flights, waypoint_start = find_flight_structures(data)
    
    # Find waypoint data
    find_waypoint_data(data)
    
    # Summary
    print('=== SUMMARY ===')
    print()
    if flights:
        print(f'Detected {len(flights)} flight records')
        print(f'Average flight fields: {sum(f["field1"] for f in flights)/len(flights):.1f}, '
              f'{sum(f["field2"] for f in flights)/len(flights):.1f}, '
              f'{sum(f["field3"] for f in flights)/len(flights):.1f}')
    
    print()
    print('Structure hypothesis:')
    print('  - Header: First ~8 bytes (counts, mission type)')
    print('  - Flight records: 12 bytes each (ID, waypoint refs, flags)')
    print('  - Waypoint data: 1-byte coords + metadata')
    print('  - Variable size due to different flight/waypoint counts')

def main():
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = '../game/SQUAD0.MIS'
    
    parse_mission_file(filename)

if __name__ == '__main__':
    main()
