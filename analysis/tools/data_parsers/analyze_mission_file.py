#!/usr/bin/env python3
"""Initial analysis of .MIS mission files."""

import struct
import sys

def analyze_mission_file(filename):
    """Analyze a mission file structure."""
    
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f'Mission file: {filename}')
    print(f'Size: {len(data)} bytes')
    print()
    
    # Show first 256 bytes
    print('First 256 bytes:')
    for i in range(0, min(256, len(data)), 16):
        hex_str = ' '.join(f'{data[i+j]:02X}' for j in range(min(16, len(data)-i)))
        ascii_str = ''.join(chr(data[i+j]) if 32 <= data[i+j] < 127 else '.' for j in range(min(16, len(data)-i)))
        print(f'0x{i:04X}: {hex_str}  {ascii_str}')
    print()
    
    # Look for patterns
    print('Pattern Analysis:')
    print()
    
    # Count 0xFF bytes
    ff_count = data.count(0xFF)
    print(f'0xFF bytes: {ff_count} ({ff_count*100/len(data):.1f}%)')
    
    # Count 0x00 bytes
    zero_count = data.count(0x00)
    print(f'0x00 bytes: {zero_count} ({zero_count*100/len(data):.1f}%)')
    print()
    
    # Look for text strings
    print('Text strings found:')
    i = 0
    strings_found = 0
    while i < len(data) and strings_found < 10:
        if 65 <= data[i] <= 90 or 97 <= data[i] <= 122:  # A-Z or a-z
            end = i
            while end < len(data) and data[end] != 0 and end < i + 30:
                if not (32 <= data[end] < 127):
                    break
                end += 1
            if end > i + 3 and end < len(data) and (data[end] == 0 or end == i + 30):
                text = data[i:end].decode('ascii', errors='ignore')
                if len(text) >= 4:
                    print(f'  0x{i:04X}: "{text}"')
                    strings_found += 1
            i = end + 1
        else:
            i += 1
    print()
    
    # Look for repeating structures
    print('Looking for repeating patterns:')
    # Check common structure sizes
    for stride in [8, 12, 16, 20, 24, 32, 40, 48, 64]:
        matches = 0
        # Check if data at regular intervals has patterns
        if stride * 3 < len(data):
            for base in range(0, min(len(data) - stride * 3, 200)):
                # Check if first byte repeats at stride intervals
                if data[base] != 0 and data[base] == data[base+stride]:
                    matches += 1
        if matches > 2:
            print(f'  Stride {stride:2d}: {matches} potential repeating structures')
    print()
    
    # Look for uint16 values that might be counts
    print('Small uint16 values (potential counts, 1-50):')
    count_printed = 0
    for i in range(0, min(len(data)-1, 200), 2):
        val = struct.unpack('<H', data[i:i+2])[0]
        if 1 <= val <= 50:
            print(f'  0x{i:04X}: {val:3d}')
            count_printed += 1
            if count_printed >= 15:
                break
    print()
    
    # Show last 128 bytes
    if len(data) > 256:
        print('Last 128 bytes:')
        start = len(data) - 128
        for i in range(start, len(data), 16):
            hex_str = ' '.join(f'{data[i+j]:02X}' if i+j < len(data) else '  ' for j in range(min(16, len(data)-i)))
            ascii_str = ''.join(chr(data[i+j]) if i+j < len(data) and 32 <= data[i+j] < 127 else '.' for j in range(min(16, len(data)-i)))
            print(f'0x{i:04X}: {hex_str}  {ascii_str}')

def main():
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = '../game/SQUAD0.MIS'
    
    analyze_mission_file(filename)

if __name__ == '__main__':
    main()
