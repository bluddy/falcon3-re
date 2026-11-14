#!/usr/bin/env python3
"""Parse strategic targets from campaign files."""

import struct
import sys

def find_blocks(data):
    """Find all data blocks separated by 4+ FF bytes."""
    blocks = []
    in_block = False
    block_start = 0
    
    for i in range(len(data)):
        if data[i] != 0xFF and not in_block:
            in_block = True
            block_start = i
        elif data[i] == 0xFF and in_block:
            # Check if this is sustained FFs (at least 4 in a row)
            if i + 3 < len(data) and data[i+1] == 0xFF and data[i+2] == 0xFF and data[i+3] == 0xFF:
                blocks.append((block_start, i))
                in_block = False
    
    if in_block:
        blocks.append((block_start, len(data)))
    
    return blocks

def parse_target_block(data, start, end, index):
    """Try to parse a 70-73 byte block as a strategic target."""
    size = end - start
    if size < 60 or size > 80:
        return None
    
    block = data[start:end]
    
    # Attempt to identify fields
    target = {
        'index': index,
        'offset': start,
        'size': size,
    }
    
    # Byte 0-1: Target ID or index
    target['id'] = struct.unpack('<H', block[0:2])[0]
    
    # Next bytes often have patterns like: 00 00 01 00 02 or similar
    target['header'] = ' '.join(f'{block[i]:02X}' for i in range(0, min(8, size)))
    
    # Look for bytes in range 0x3C (60) which appears frequently - might be a separator
    # This could be the '<' character but more likely a field value
    
    # Many blocks have patterns around offset 6-7 with 0x3C
    if size > 7 and block[6] == 0x3C:
        target['field_at_6'] = block[7]
    
    # Look for strength/percentage values (0-100 or 0-255)
    for i in range(8, min(size-1, 20)):
        if 0 < block[i] <= 100:
            if 'strength_candidates' not in target:
                target['strength_candidates'] = []
            target['strength_candidates'].append((i, block[i]))
    
    # Look for repeated bytes that might be arrays
    for i in range(8, min(size-8, 30)):
        # Check for runs of similar values
        if block[i] == block[i+1] == block[i+2]:
            if 'repeated_bytes' not in target:
                target['repeated_bytes'] = []
            target['repeated_bytes'].append((i, block[i], 'x3+'))
    
    return target

def main():
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = '../game/SQUAD0.CAM'
    
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f'Campaign file: {len(data)} bytes')
    print()
    
    blocks = find_blocks(data)
    print(f'Found {len(blocks)} data blocks')
    print()
    
    # Focus on 70-73 byte blocks (likely target records)
    target_blocks = [(s, e) for s, e in blocks if 70 <= e - s <= 73]
    print(f'Found {len(target_blocks)} blocks of size 70-73 bytes (likely targets)')
    print()
    
    # Parse each target block
    print('=== POTENTIAL STRATEGIC TARGETS ===')
    print()
    for i, (start, end) in enumerate(target_blocks[:10]):  # First 10
        target = parse_target_block(data, start, end, i)
        if target:
            print(f'Target {i} @ 0x{start:04X} ({target["size"]} bytes):')
            print(f'  ID: 0x{target["id"]:04X} ({target["id"]})')
            print(f'  Header: {target["header"]}')
            if 'field_at_6' in target:
                print(f'  Field at +6: 0x3C, value at +7: 0x{target["field_at_6"]:02X}')
            if 'strength_candidates' in target:
                print(f'  Strength candidates: {target["strength_candidates"][:3]}')
            
            # Show full hex dump
            print(f'  Full dump:')
            block = data[start:end]
            for j in range(0, len(block), 16):
                hex_str = ' '.join(f'{block[j+k]:02X}' for k in range(min(16, len(block)-j)))
                print(f'    +0x{j:02X}: {hex_str}')
            print()
    
    # Look for header block
    print('=== CAMPAIGN HEADER (First 73-byte block) ===')
    if blocks[0][1] - blocks[0][0] == 73:
        header = data[blocks[0][0]:blocks[0][1]]
        print('Header structure:')
        for i in range(0, 73, 16):
            hex_str = ' '.join(f'{header[i+j]:02X}' for j in range(min(16, 73-i)))
            ascii_str = ''.join(chr(header[i+j]) if 32 <= header[i+j] < 127 else '.' for j in range(min(16, 73-i)))
            print(f'  +0x{i:02X}: {hex_str}  {ascii_str}')
        print()
        print('Potential header fields:')
        print(f'  +0x00-02: {header[0]:02X} {header[1]:02X} {header[2]:02X} (version/flags)')
        print(f'  +0x03: {header[3]} (campaign day? theater ID?)')
        print(f'  +0x04-05: {header[4]:02X} {header[5]:02X}')
        print(f'  +0x06-07: 0x{struct.unpack("<H", header[6:8])[0]:04X} ({struct.unpack("<H", header[6:8])[0]})')
        
        # Bytes 8-23 have repeated patterns (05 05 05... DD DD DD... C5 C5 C5...)
        print(f'  +0x08-0F: Repeated 0x{header[8]:02X} pattern (8 bytes)')
        print(f'  +0x10-17: Repeated 0x{header[16]:02X}/0x{header[17]:02X} pattern (8 bytes)')
        print(f'  +0x18-1F: Repeated 0x{header[24]:02X} pattern (8 bytes)')

if __name__ == '__main__':
    main()
