#!/usr/bin/env python3
"""Decode supply/inventory data from campaign files."""

import struct
import sys

def decode_supply_section(data):
    """Decode the supply data section at end of campaign file."""
    
    # Find the last significant FF padding block
    last_ff = len(data) - 1
    while last_ff > 0:
        if data[last_ff:last_ff+4] == b'\xFF\xFF\xFF\xFF':
            break
        last_ff -= 1
    
    # Find start of final data block
    start = last_ff + 4
    while start < len(data) and data[start] == 0xFF:
        start += 1
    
    print(f'Supply data block: 0x{start:04X} to 0x{len(data):04X} ({len(data) - start} bytes)')
    print()
    
    # Skip the space-padded section (all 0x20)
    # Look for where actual data starts
    actual_start = start
    while actual_start < len(data) - 100:
        # Look for non-space, non-zero data
        if data[actual_start] not in (0x00, 0x20):
            break
        # Also check if we hit a cluster of non-zero values
        if actual_start + 50 < len(data):
            chunk = data[actual_start:actual_start+50]
            non_zero = sum(1 for b in chunk if b not in (0x00, 0x20))
            if non_zero > 10:
                break
        actual_start += 1
    
    print(f'Actual supply data starts at: 0x{actual_start:04X}')
    print()
    
    supply_data = data[actual_start:]
    print(f'Supply data size: {len(supply_data)} bytes')
    print()
    
    # Show hex dump
    print('Hex dump (first 200 bytes):')
    for i in range(0, min(200, len(supply_data)), 16):
        hex_str = ' '.join(f'{supply_data[i+j]:02X}' for j in range(min(16, len(supply_data)-i)))
        print(f'  +0x{i:03X}: {hex_str}')
    print()
    
    # Parse as uint16 array
    print('=== DECODED FIELDS (as uint16) ===')
    print()
    
    u16_array = []
    for i in range(0, min(len(supply_data)-1, 200), 2):
        val = struct.unpack('<H', supply_data[i:i+2])[0]
        u16_array.append(val)
    
    # Identify fields based on patterns
    print('Field analysis:')
    print()
    
    # Skip leading zeros
    first_nonzero = 0
    for i, val in enumerate(u16_array):
        if val != 0:
            first_nonzero = i
            break
    
    print(f'First {first_nonzero} uint16 values are zero (header/padding)')
    print()
    
    # Show all non-zero values with context
    print('Non-zero values:')
    for i in range(first_nonzero, min(len(u16_array), 60)):
        val = u16_array[i]
        offset = i * 2
        
        # Add interpretation hints
        interpretation = ''
        if val == 18:
            interpretation = ' <-- AIRCRAFT COUNT (18 F-16s)'
        elif 100 <= val <= 300 and val not in (6030,):
            interpretation = ' <-- Weapon count?'
        elif val == 6030:
            interpretation = ' <-- Fuel? (appears twice)'
        elif 1 <= val <= 20:
            interpretation = ' <-- Small counter'
        elif val == 65535:
            interpretation = ' <-- 0xFFFF (marker/unused)'
        
        print(f'  +0x{offset:03X} [{i:3d}]: {val:5d} (0x{val:04X}){interpretation}')
    
    print()
    print('=== TENTATIVE FIELD MAPPING ===')
    print()
    
    # Try to map fields based on observed values
    if len(u16_array) > 30:
        base = first_nonzero
        
        print(f'Offset | Value | Interpretation')
        print(f'-------|-------|------------------------------------------')
        
        # Common weapon counts in Falcon: AIM-9, AIM-120, bombs, rockets, etc.
        # Initial loadouts are usually 100-300 range
        
        if base + 5 < len(u16_array):
            print(f'+0x{(base+3)*2:03X}  | {u16_array[base+3]:5d} | Weapon type 1 (possibly AIM-9 Sidewinder)')
        if base + 6 < len(u16_array):
            print(f'+0x{(base+4)*2:03X}  | {u16_array[base+4]:5d} | Weapon type 2 (possibly AIM-120 AMRAAM)')
        if base + 7 < len(u16_array):
            print(f'+0x{(base+5)*2:03X}  | {u16_array[base+5]:5d} | Weapon type 3 (possibly AGM-65 Maverick)')
        if base + 8 < len(u16_array):
            print(f'+0x{(base+6)*2:03X}  | {u16_array[base+6]:5d} | Weapon type 4 (possibly Mk-82 bombs)')
        if base + 9 < len(u16_array):
            print(f'+0x{(base+7)*2:03X}  | {u16_array[base+7]:5d} | Weapon type 5 (possibly Mk-84 bombs)')
        if base + 10 < len(u16_array):
            print(f'+0x{(base+8)*2:03X}  | {u16_array[base+8]:5d} | Weapon type 6 (possibly AGM-88 HARM)')
        if base + 11 < len(u16_array):
            print(f'+0x{(base+9)*2:03X}  | {u16_array[base+9]:5d} | Weapon type 7 (possibly Rockets/CBU)')
        if base + 12 < len(u16_array):
            print(f'+0x{(base+10)*2:03X}  | {u16_array[base+10]:5d} | Weapon type 8')
        
        # Look for the aircraft count (value = 18)
        for i in range(base, min(base + 30, len(u16_array))):
            if u16_array[i] == 18:
                print(f'+0x{i*2:03X}  | {u16_array[i]:5d} | *** AIRCRAFT COUNT (F-16s available) ***')
                
                # Following values might be related
                if i + 1 < len(u16_array):
                    print(f'+0x{(i+1)*2:03X}  | {u16_array[i+1]:5d} | Aircraft damaged?')
                if i + 2 < len(u16_array):
                    print(f'+0x{(i+2)*2:03X}  | {u16_array[i+2]:5d} | Aircraft in maintenance?')
                break
        
        # Look for 6030 (fuel?)
        for i in range(base, min(base + 30, len(u16_array))):
            if u16_array[i] == 6030:
                print(f'+0x{i*2:03X}  | {u16_array[i]:5d} | Fuel reserves? (0x178E)')
                break
    
    print()
    
    # Look for byte patterns (not uint16)
    print('=== BYTE PATTERNS (non-uint16 interpretation) ===')
    print()
    
    # The section after the initial data might have flag arrays
    # Look around offset 0x60+
    if len(supply_data) > 100:
        print('Bytes at offset 0x60-0x80 (might be flags/status):')
        for i in range(0x60, min(0x80, len(supply_data))):
            if supply_data[i] != 0:
                print(f'  +0x{i:03X}: 0x{supply_data[i]:02X} ({supply_data[i]:3d})')

def main():
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = '../game/SQUAD0.CAM'
    
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f'Campaign file: {len(data)} bytes')
    print()
    
    decode_supply_section(data)

if __name__ == '__main__':
    main()
