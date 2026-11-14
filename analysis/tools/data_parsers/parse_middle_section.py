#!/usr/bin/env python3
"""Parse the middle section between aircraft records and waypoints."""

import struct
import sys

def analyze_block(data, offset, size, name):
    """Analyze a data block."""
    
    print(f'{name} at 0x{offset:04X} ({size} bytes):')
    
    # Show hex
    chunk = data[offset:offset+size]
    for i in range(0, size, 16):
        hex_str = ' '.join(f'{chunk[i+j]:02X}' for j in range(min(16, size-i)))
        print(f'  0x{offset+i:04X}: {hex_str}')
    
    print()
    
    # Try to interpret
    if size >= 32:
        print('  First byte:', chunk[0], '(count or ID?)')
        
        # Look for coordinate-like pairs
        for i in range(0, min(32, size), 2):
            if i + 1 < size:
                val = struct.unpack('<H', chunk[i:i+2])[0]
                if 30000 < val < 65000:  # Coordinate range?
                    print(f'    Bytes {i}-{i+1}: {val} (0x{chunk[i]:02X}{chunk[i+1]:02X}) - coord?')
    
    print()

def find_flight_plans(data, start, end):
    """Try to identify flight plan structures."""
    
    section = data[start:end]
    
    print('Searching for repeating structures...')
    print()
    
    # Look for the pattern we saw: variable-length blocks separated by zeros
    blocks = []
    i = 0
    
    while i < len(section):
        # Skip zeros
        while i < len(section) and section[i] == 0x00:
            i += 1
        
        if i >= len(section):
            break
        
        # Find end of non-zero block
        block_start = i
        while i < len(section) and section[i] != 0x00:
            i += 1
        
        # But also check for small gaps (single zeros within a block)
        while i < len(section) - 1:
            if section[i] == 0x00 and section[i+1] != 0x00:
                # Single zero, might be part of structure
                zero_count = 0
                j = i
                while j < len(section) and section[j] == 0x00:
                    zero_count += 1
                    j += 1
                
                if zero_count <= 2:  # Small gap, include it
                    i = j
                    while i < len(section) and section[i] != 0x00:
                        i += 1
                else:
                    break
            else:
                break
        
        block_end = i
        block_size = block_end - block_start
        
        if block_size > 0:
            blocks.append((start + block_start, block_size))
    
    print(f'Found {len(blocks)} data blocks:')
    print()
    print('Idx | Offset   | Size | Type Guess')
    print('----|----------|------|---------------------------')
    
    for i, (offset, size) in enumerate(blocks):
        if size <= 4:
            type_guess = 'Header/flag'
        elif size <= 10:
            type_guess = 'Short record'
        elif 20 <= size <= 35:
            type_guess = 'Flight plan?'
        elif 40 <= size <= 50:
            type_guess = 'Extended flight plan?'
        else:
            type_guess = 'Unknown'
        
        print(f'{i:3d} | 0x{offset:04X} | {size:4d} | {type_guess}')
    
    return blocks

def analyze_7byte_patterns(data, start, end):
    """Look for 7-byte patterns ending in FF XX 40 11."""
    
    section = data[start:end]
    
    print('Searching for 7-byte pattern (XX XX XX FF XX 40 11):')
    print()
    
    patterns = []
    
    for i in range(len(section) - 7):
        if (section[i+3] == 0xFF and 
            section[i+5] == 0x40 and 
            section[i+6] == 0x11):
            patterns.append(start + i)
    
    print(f'Found {len(patterns)} matches:')
    for offset in patterns:
        chunk = data[offset:offset+7]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        print(f'  0x{offset:04X}: {hex_str}')
    
    print()
    return patterns

def main():
    filename = '../game/SQUAD0.MIS'
    
    with open(filename, 'rb') as f:
        data = f.read()
    
    print('Mission File Middle Section Parser')
    print('=' * 70)
    print()
    
    start = 0x00A4
    end = 0x0251
    
    print(f'Section: 0x{start:04X} - 0x{end:04X} ({end-start} bytes)')
    print()
    
    # Analyze first few bytes
    analyze_block(data, start, 8, 'Header')
    
    # Find all blocks
    blocks = find_flight_plans(data, start, end)
    
    print()
    print('=' * 70)
    print()
    
    # Look for 7-byte pattern
    patterns = analyze_7byte_patterns(data, start, end)
    
    print()
    print('=' * 70)
    print()
    
    # Detailed analysis of first few blocks
    if len(blocks) >= 3:
        print('Detailed analysis of first blocks:')
        print()
        for i in range(min(3, len(blocks))):
            offset, size = blocks[i]
            analyze_block(data, offset, size, f'Block {i}')

if __name__ == '__main__':
    main()
