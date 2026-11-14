#!/usr/bin/env python3
"""Find repeating structures in campaign files."""

import struct

def analyze_block(data, start, end, name):
    """Analyze a single data block."""
    size = end - start
    block = data[start:end]
    
    print(f'{name} @ 0x{start:04X}-0x{end:04X} ({size} bytes):')
    for i in range(0, size, 16):
        hex_str = ' '.join(f'{block[i+j]:02X}' for j in range(min(16, size-i)))
        ascii_str = ''.join(chr(block[i+j]) if 32 <= block[i+j] < 127 else '.' for j in range(min(16, size-i)))
        print(f'  0x{start+i:04X}: {hex_str}  {ascii_str}')
    print()

def main():
    with open('../game/SQUAD0.CAM', 'rb') as f:
        data = f.read()
    
    print(f'Campaign file: {len(data)} bytes')
    print()
    
    # The file likely has:
    # - Header
    # - Strategic target array
    # - Supply/inventory data
    # - Campaign state
    
    # Look for the header - probably starts with theater ID or campaign day
    print('=== HEADER ANALYSIS ===')
    print('First 64 bytes:')
    for i in range(0, 64, 16):
        hex_str = ' '.join(f'{data[i+j]:02X}' for j in range(16))
        print(f'0x{i:04X}: {hex_str}')
    print()
    
    # Look for blocks of non-FF data (actual records)
    print('=== FINDING DATA BLOCKS ===')
    in_block = False
    block_start = 0
    blocks = []
    
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
    
    print(f'Found {len(blocks)} data blocks (separated by 4+ consecutive FFs)')
    print()
    print('First 30 blocks:')
    for i, (start, end) in enumerate(blocks[:30]):
        size = end - start
        # Show first few bytes
        preview = ' '.join(f'{data[start+j]:02X}' for j in range(min(8, size)))
        print(f'  [{i:3d}] 0x{start:04X}-0x{end:04X} ({size:4d} bytes): {preview}...')
    
    # Check if blocks have regular sizes
    print()
    print('Block size distribution:')
    sizes = [end - start for start, end in blocks]
    size_counts = {}
    for s in sizes:
        size_counts[s] = size_counts.get(s, 0) + 1
    
    for size in sorted(size_counts.keys()):
        if size_counts[size] > 3:  # Only show sizes that appear multiple times
            print(f'  {size:4d} bytes: {size_counts[size]:3d} blocks')
    
    print()
    print('=== DETAILED BLOCK ANALYSIS ===')
    print()
    
    # Analyze first few large blocks
    analyze_block(data, 0x0000, 0x0049, 'Block 0 (Header candidate)')
    analyze_block(data, 0x004E, 0x0095, 'Block 1 (71 bytes)')
    analyze_block(data, 0x009C, 0x00E2, 'Block 2 (70 bytes)')

if __name__ == '__main__':
    main()
