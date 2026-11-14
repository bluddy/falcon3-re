#!/usr/bin/env python3
"""Analyze flight record section in mission files."""

import struct
import sys

def analyze_header(data, name):
    """Analyze mission file header."""
    
    print(f'=== {name} ===')
    print()
    print('First 64 bytes:')
    for i in range(0, 64, 16):
        hex_str = ' '.join(f'{data[i+j]:02X}' for j in range(min(16, len(data)-i)))
        print(f'  0x{i:04X}: {hex_str}')
    
    print()
    print('Header fields:')
    print(f'  Byte 0:    {data[0]:3d} (0x{data[0]:02X})')
    print(f'  Bytes 1-2: {struct.unpack("<H", data[1:3])[0]:5d} (0x{data[1]:02X}{data[2]:02X})')
    print(f'  Byte 3:    {data[3]:3d} (0x{data[3]:02X})')
    print(f'  Byte 4:    {data[4]:3d} (0x{data[4]:02X})')
    print(f'  Byte 5:    {data[5]:3d} (0x{data[5]:02X})')
    print()

def find_repeating_patterns(data, max_pattern_len=10):
    """Find repeating byte patterns."""
    
    print('Searching for repeating patterns...')
    print()
    
    # Look for patterns that repeat at least twice
    for pattern_len in range(3, max_pattern_len + 1):
        for start in range(0, min(100, len(data) - pattern_len * 2)):
            pattern = data[start:start+pattern_len]
            
            # Check if pattern repeats immediately after
            next_chunk = data[start+pattern_len:start+pattern_len*2]
            
            if len(next_chunk) == pattern_len:
                # Check for similar patterns (not exact match)
                differences = sum(1 for a, b in zip(pattern, next_chunk) if a != b)
                
                # If only 1-2 bytes differ, it might be a counter or index
                if differences == 1 or differences == 2:
                    # Find how many times this pattern-like structure repeats
                    count = 2
                    offset = start + pattern_len * 2
                    while offset + pattern_len <= len(data):
                        chunk = data[offset:offset+pattern_len]
                        diffs = sum(1 for a, b in zip(pattern, chunk) if a != b)
                        if diffs <= 2:
                            count += 1
                            offset += pattern_len
                        else:
                            break
                    
                    if count >= 3:
                        print(f'Pattern length {pattern_len} at 0x{start:04X}, repeats {count} times:')
                        for i in range(min(count, 5)):
                            off = start + i * pattern_len
                            chunk = data[off:off+pattern_len]
                            hex_str = ' '.join(f'{b:02X}' for b in chunk)
                            print(f'  [{i}] 0x{off:04X}: {hex_str}')
                        print()
                        return start, pattern_len, count

def analyze_structure(data, start, pattern_len, count):
    """Analyze the structure of repeating patterns."""
    
    print(f'Detailed analysis of {count} patterns starting at 0x{start:04X}:')
    print()
    print('Idx | Offset | ', end='')
    for i in range(pattern_len):
        print(f'B{i:02d} ', end='')
    print()
    print('----|--------|', end='')
    for i in range(pattern_len):
        print('----', end='')
    print()
    
    entries = []
    for i in range(count):
        off = start + i * pattern_len
        chunk = data[off:off+pattern_len]
        entries.append(chunk)
        
        print(f'{i:3d} | 0x{off:04X} | ', end='')
        for b in chunk:
            print(f'{b:3d} ', end='')
        print()
    
    print()
    print('Field analysis:')
    for field_idx in range(pattern_len):
        values = [entry[field_idx] for entry in entries]
        unique = set(values)
        
        if len(unique) == 1:
            print(f'  Byte {field_idx}: constant = {values[0]} (0x{values[0]:02X})')
        elif len(unique) == len(values):
            # All unique - might be incrementing
            diffs = [values[i+1] - values[i] for i in range(len(values)-1)]
            if len(set(diffs)) == 1:
                print(f'  Byte {field_idx}: increments by {diffs[0]} (range: {min(values)}-{max(values)})')
            else:
                print(f'  Byte {field_idx}: varies (range: {min(values)}-{max(values)}, {len(unique)} unique)')
        else:
            print(f'  Byte {field_idx}: varies (range: {min(values)}-{max(values)}, {len(unique)} unique)')

def main():
    file0 = '../game/SQUAD0.MIS'
    file1 = '../game/SQUAD1.MIS'
    
    print('Mission File Flight Record Analysis')
    print('=' * 70)
    print()
    
    with open(file0, 'rb') as f:
        data0 = f.read()
    
    with open(file1, 'rb') as f:
        data1 = f.read()
    
    analyze_header(data0, 'SQUAD0.MIS')
    analyze_header(data1, 'SQUAD1.MIS')
    
    print('=' * 70)
    print()
    
    # Find repeating pattern in SQUAD0
    result = find_repeating_patterns(data0)
    if result:
        start, pattern_len, count = result
        analyze_structure(data0, start, pattern_len, count)

if __name__ == '__main__':
    main()
