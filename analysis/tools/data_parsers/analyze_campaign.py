#!/usr/bin/env python3
"""Initial analysis of .CAM campaign files."""

import struct
import sys

def analyze_campaign(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f'Campaign file: {len(data)} bytes (0x{len(data):X})')
    print()
    
    # Show first 256 bytes
    print('First 256 bytes:')
    for i in range(0, 256, 16):
        hex_str = ' '.join(f'{data[i+j]:02X}' for j in range(16))
        ascii_str = ''.join(chr(data[i+j]) if 32 <= data[i+j] < 127 else '.' for j in range(16))
        print(f'0x{i:04X}: {hex_str}  {ascii_str}')
    print()
    
    # Look for text strings (theater name, etc.)
    print('Text strings found:')
    i = 0
    while i < min(len(data), 2000):  # Search first 2KB
        if 65 <= data[i] <= 90 or 97 <= data[i] <= 122:  # A-Z or a-z
            end = i
            while end < len(data) and data[end] != 0 and end < i + 30:
                if not (32 <= data[end] < 127):
                    break
                end += 1
            if end > i + 2 and end < len(data) and data[end] == 0:
                text = data[i:end].decode('ascii', errors='ignore')
                if len(text) >= 3:
                    print(f'  0x{i:04X}: "{text}"')
            i = end + 1
        else:
            i += 1
    print()
    
    # Look for small integers (campaign day, counts)
    print('Small uint16 values (likely counters/days, < 1000):')
    for i in range(0, min(len(data) - 1, 512), 2):
        val = struct.unpack('<H', data[i:i+2])[0]
        if 0 < val < 1000:
            print(f'  0x{i:04X}: {val:5d} (0x{val:04X})')
    print()
    
    # Look for patterns that might be arrays (repeated structures)
    print('Looking for repeated byte patterns (potential arrays)...')
    # Check for regions with similar byte patterns
    for stride in [10, 12, 14, 16, 20, 24, 32]:
        print(f'  Testing stride {stride}:')
        matches = 0
        for base in range(0, min(len(data) - stride * 10, 1000), stride):
            # Check if bytes at base, base+stride, base+stride*2 have similar patterns
            if data[base] == data[base+stride] and data[base] == data[base+stride*2]:
                matches += 1
                if matches == 1:  # Show first match
                    print(f'    Potential array at 0x{base:04X} (first bytes: {data[base]:02X})')
        if matches > 0:
            print(f'    Total matches: {matches}')
    print()
    
    # Show last 128 bytes
    print('Last 128 bytes:')
    start = len(data) - 128
    for i in range(start, len(data), 16):
        hex_str = ' '.join(f'{data[i+j]:02X}' if i+j < len(data) else '  ' for j in range(16))
        ascii_str = ''.join(chr(data[i+j]) if i+j < len(data) and 32 <= data[i+j] < 127 else '.' for j in range(16) if i+j < len(data))
        print(f'0x{i:04X}: {hex_str}  {ascii_str}')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = '../game/SQUAD0.CAM'
    
    analyze_campaign(filename)
