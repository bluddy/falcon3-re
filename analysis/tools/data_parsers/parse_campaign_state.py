#!/usr/bin/env python3
"""Parse campaign state bytes that follow supply data."""

import struct
import sys

def parse_campaign_state(data):
    """Parse the campaign state section after supply data."""
    
    # Supply data ends around 0x2DCC, state bytes start at 0x2DCE
    offset = 0x2DCE
    
    if offset + 100 > len(data):
        print(f'Error: File too small')
        return None
    
    section = data[offset:min(offset+200, len(data))]
    
    print('=== CAMPAIGN STATE BYTES ===')
    print()
    print(f'Location: 0x{offset:04X} to 0x{offset+len(section):04X}')
    print()
    
    # Show hex dump
    print('Hex dump:')
    for i in range(0, min(120, len(section)), 16):
        hex_str = ' '.join(f'{section[i+j]:02X}' for j in range(min(16, len(section)-i)))
        print(f'  0x{offset+i:04X}: {hex_str}')
    print()
    
    # Parse specific known sections
    print('Decoded fields:')
    print()
    
    # Bytes 0x00-0x2B are mostly zeros with a few values
    if section[2] != 0:
        print(f'  +0x02 (0x{offset+2:04X}): {section[2]:3d} - Counter')
    
    # Major data cluster at 0x2C-0x3F (looks like an array)
    print('  Array at +0x2C (0x2DFA):')
    array1 = section[0x2C:0x40]
    for i in range(0, len(array1), 8):
        hex_str = ' '.join(f'{array1[i+j]:02X}' for j in range(min(8, len(array1)-i)))
        vals = ', '.join(f'{array1[i+j]:3d}' for j in range(min(8, len(array1)-i)))
        print(f'    +0x{0x2C+i:02X}: {hex_str}  ({vals})')
    
    # These might be target capture counts by type
    if len(array1) >= 10:
        print()
        print('  Interpretation (if target counts):')
        print(f'    Type 0: {array1[0]:2d}')
        print(f'    Type 1: {array1[1]:2d}')
        print(f'    Type 2: {array1[2]:2d}')
        print(f'    Type 3: {array1[3]:2d}')
        print(f'    Type 4: {array1[4]:2d}')
        print(f'    Type 5: {array1[5]:2d}')
    
    print()
    
    # More data at 0x38-0x40
    if len(section) > 0x40:
        print('  Flags/Status bytes:')
        for i in range(0x38, min(0x60, len(section))):
            if section[i] != 0 and section[i] != 0xFF:
                print(f'    +0x{i:02X} (0x{offset+i:04X}): 0x{section[i]:02X} = {section[i]:3d}')
    
    print()
    
    # Look for FF markers (boundaries)
    print('  0xFF markers (potential boundaries):')
    ff_positions = []
    for i in range(len(section)):
        if section[i] == 0xFF:
            ff_positions.append(i)
            if i < 100:
                print(f'    +0x{i:02X} (0x{offset+i:04X})')
    
    print()
    
    # Calculate distances between FF markers
    if len(ff_positions) > 1:
        print('  Distances between FF markers:')
        for i in range(1, min(10, len(ff_positions))):
            dist = ff_positions[i] - ff_positions[i-1]
            print(f'    Marker {i-1} to {i}: {dist} bytes')
    
    return section

def compare_with_supply(data):
    """Show transition from supply data to state bytes."""
    print()
    print('=== TRANSITION: SUPPLY TO STATE ===')
    print()
    
    # Show last bytes of supply and first bytes of state
    supply_end = 0x2DCE
    transition = data[supply_end-16:supply_end+48]
    
    print('Last 16 bytes of supply + first 48 bytes of state:')
    for i in range(0, len(transition), 16):
        offset = supply_end - 16 + i
        hex_str = ' '.join(f'{transition[i+j]:02X}' for j in range(min(16, len(transition)-i)))
        
        # Mark the boundary
        marker = ''
        if offset == supply_end:
            marker = ' <-- STATE BEGINS HERE'
        elif offset == supply_end - 16:
            marker = ' <-- SUPPLY ENDS NEAR HERE'
            
        print(f'  0x{offset:04X}: {hex_str}{marker}')

def main():
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = '../game/SQUAD0.CAM'
    
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f'Campaign file: {filename}')
    print(f'Size: {len(data)} bytes')
    print()
    
    parse_campaign_state(data)
    compare_with_supply(data)

if __name__ == '__main__':
    main()
