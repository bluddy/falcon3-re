#!/usr/bin/env python3
"""Parse the extended pilot records (10 records at end of squadron file)."""

import struct
import sys

def parse_extended_pilots(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    
    supply_data = data[0x7F8:0xA8F]
    print(f'Extended pilot data: {len(supply_data)} bytes (0x{len(supply_data):X})')
    print()
    
    # Parse 10 records of 66 bytes each (53 data + 13 separator)
    for i in range(10):
        offset = i * 66
        if offset + 66 > len(supply_data):
            print(f'Record {i}: insufficient data ({len(supply_data) - offset} bytes remaining)')
            break
        
        rec = supply_data[offset:offset+66]
        
        # Bytes 0-2: status/header
        header = struct.unpack('<3B', rec[0:3])
        
        # Bytes 3-17: callsign (15 bytes, null-terminated)
        callsign = rec[3:18].decode('ascii', errors='ignore').rstrip('\x00')
        
        # Bytes 19-33: nickname (15 bytes, null-terminated)
        nickname = rec[19:34].decode('ascii', errors='ignore').rstrip('\x00')
        
        # Bytes 35-38: ID (4 bytes)
        pilot_id = rec[35:39].hex().upper()
        
        # Bytes 39-52: additional data (14 bytes before separator)
        extra_data = rec[39:53]
        
        # Bytes 53-65: separator (13 bytes, should start with FF FF or FF FF FF)
        separator = rec[53:66]
        
        print(f'Record {i} @ 0x{0x7F8+offset:04X}:')
        print(f'  Header:    {header[0]:02X} {header[1]:02X} {header[2]:02X}')
        print(f'  Callsign:  "{callsign}"')
        print(f'  Nickname:  "{nickname}"')
        print(f'  ID:        {pilot_id}')
        print(f'  Extra:     {" ".join(f"{b:02X}" for b in extra_data)}')
        print(f'  Separator: {" ".join(f"{b:02X}" for b in separator[:6])}...')
        print()
    
    # Check remaining bytes
    remaining_offset = 10 * 66
    if remaining_offset < len(supply_data):
        remaining = supply_data[remaining_offset:]
        print(f'Remaining {len(remaining)} bytes @ 0x{0x7F8+remaining_offset:04X}:')
        print(' ', ' '.join(f'{b:02X}' for b in remaining))
        print()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = '../game/SQUAD0.SQU'
    
    parse_extended_pilots(filename)
