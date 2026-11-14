#!/usr/bin/env python3
"""Analyze the supply data block in squadron files."""

import struct
import sys

def analyze_supply_data(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    
    supply_data = data[0x7F8:0xA8F]
    print(f'Supply data: {len(supply_data)} bytes (0x{len(supply_data):X})')
    print()
    
    # Check if this is actually more pilot data
    # Pattern seems to be: FF XX 00 CALLSIGN(15) NICKNAME(15) ID(4) ...
    # That's 3 + 15 + 15 + 4 = 37 bytes, but we see repeats every ~22 bytes?
    # Or maybe: XX XX 00 CALLSIGN(up to 15) 00-pad NICKNAME(up to 15) 00-pad ID(4)
    
    print('Interpreting as 21-byte pilot records (21*30=630, leaves 33 bytes):')
    for i in range(30):
        offset = i * 21
        if offset + 21 > len(supply_data):
            break
        rec = supply_data[offset:offset+21]
        
        # Try to extract callsign (look for null terminator)
        callsign_end = rec[3:].find(b'\x00')
        if callsign_end >= 0:
            callsign = rec[3:3+callsign_end].decode('ascii', errors='ignore')
        else:
            callsign = rec[3:18].decode('ascii', errors='ignore').rstrip('\x00')
        
        print(f'  [{i:2d}] 0x{0x7F8+offset:04X}: {rec[0]:02X} {rec[1]:02X} {rec[2]:02X} "{callsign}"')
    print()
    
    # Show first 128 bytes
    print('First 128 bytes:')
    for i in range(0, 128, 16):
        line = ' '.join(f'{supply_data[i+j]:02X}' for j in range(16))
        ascii_line = ''.join(chr(b) if 32 <= b < 127 else '.' for b in supply_data[i:i+16])
        print(f'0x{0x7F8+i:04X}: {line}  {ascii_line}')
    print()
    
    # Look for text strings
    print('Scanning for text strings in supply area...')
    i = 0
    strings_found = []
    while i < len(supply_data):
        if 65 <= supply_data[i] <= 90 or 97 <= supply_data[i] <= 122:  # A-Z or a-z
            end = i
            while end < len(supply_data) and supply_data[end] != 0 and end < i + 20:
                if not (32 <= supply_data[end] < 127):
                    break
                end += 1
            if end > i + 2 and end < len(supply_data) and supply_data[end] == 0:
                text = supply_data[i:end].decode('ascii', errors='ignore')
                if len(text) >= 3:
                    strings_found.append((0x7F8 + i, text))
                    print(f'  0x{0x7F8+i:04X}: "{text}"')
            i = end + 1
        else:
            i += 1
    print()
    
    # Look for 16-bit integers that might be counts
    print('Looking for potential count fields (uint16 values 0-1000):')
    for i in range(0, len(supply_data) - 1, 2):
        val = struct.unpack('<H', supply_data[i:i+2])[0]
        if 0 < val <= 1000:
            print(f'  0x{0x7F8+i:04X}: {val:5d} (0x{val:04X})')
    print()
    
    # Show last 64 bytes
    print('Last 64 bytes:')
    start = len(supply_data) - 64
    for i in range(start, len(supply_data), 16):
        line = ' '.join(f'{supply_data[i+j]:02X}' if i+j < len(supply_data) else '  ' for j in range(16))
        ascii_line = ''.join(chr(supply_data[i+j]) if i+j < len(supply_data) and 32 <= supply_data[i+j] < 127 else '.' for j in range(16) if i+j < len(supply_data))
        print(f'0x{0x7F8+i:04X}: {line}  {ascii_line}')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = '../game/SQUAD0.SQU'
    
    analyze_supply_data(filename)
