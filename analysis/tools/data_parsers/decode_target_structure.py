#!/usr/bin/env python3
"""Decode strategic target structure from campaign files."""

import struct

def find_all_blocks(data):
    """Find ALL data blocks (any size)."""
    blocks = []
    i = 0
    while i < len(data):
        if data[i] != 0xFF:
            start = i
            while i < len(data) and not (data[i:i+4] == b'\xFF\xFF\xFF\xFF'):
                i += 1
            end = i
            blocks.append((start, end, end - start))
        i += 1
    return blocks

def find_target_blocks(data):
    """Find 70-73 byte blocks (strategic targets)."""
    blocks = []
    i = 0
    while i < len(data):
        if data[i] != 0xFF:
            start = i
            while i < len(data) and not (data[i:i+4] == b'\xFF\xFF\xFF\xFF'):
                i += 1
            end = i
            if 70 <= end - start <= 73:
                blocks.append((start, end))
        i += 1
    return blocks

def parse_target(data, start, end):
    """Parse a single strategic target."""
    block = data[start:end]
    size = len(block)
    
    target = {}
    
    # Bytes 0-1: Target ID (uint16)
    target['id'] = struct.unpack('<H', block[0:2])[0]
    
    # Bytes 2-5: Unknown header fields
    target['byte_2'] = block[2]
    target['byte_3'] = block[3]
    target['byte_4'] = block[4]
    target['byte_5'] = block[5]
    
    # Byte 6: Always 0x3C (separator/magic?)
    target['separator'] = block[6]
    
    # Byte 7: Unknown (varies 14-60)
    target['field_7'] = block[7]
    
    # Bytes 8-15: Array of 8 values (strength data?)
    target['array1'] = list(block[8:16])
    
    # Bytes 16-23: Array of 8 values (higher values, 0xC0-0xF0 range)
    target['array2'] = list(block[16:24])
    
    # Bytes 24-31: Array of 8 values (status flags?)
    target['array3'] = list(block[24:32])
    
    # Bytes 32-39: More arrays or individual fields
    target['data_32_39'] = list(block[32:40]) if size > 39 else []
    
    # Remaining bytes: uint16 values (target indices? coordinates?)
    target['uint16_values'] = []
    for i in range(48, min(size-1, 70), 2):
        val = struct.unpack('<H', block[i:i+2])[0]
        target['uint16_values'].append(val)
    
    return target

def analyze_small_blocks(data):
    """Analyze small data blocks that might contain supply data."""
    all_blocks = find_all_blocks(data)
    
    print('=== SMALL BLOCKS ANALYSIS ===')
    print()
    
    # Categorize by size
    small = [(s, e, sz) for s, e, sz in all_blocks if 1 <= sz <= 10]
    medium = [(s, e, sz) for s, e, sz in all_blocks if 11 <= sz <= 30]
    large = [(s, e, sz) for s, e, sz in all_blocks if 31 <= sz <= 69]
    xlarge = [(s, e, sz) for s, e, sz in all_blocks if sz >= 70]
    
    print(f'Block categories:')
    print(f'  Small (1-10b):   {len(small):3d} blocks')
    print(f'  Medium (11-30b): {len(medium):3d} blocks')
    print(f'  Large (31-69b):  {len(large):3d} blocks')
    print(f'  XLarge (70+b):   {len(xlarge):3d} blocks')
    print()
    
    print('First 15 small blocks (potential supply/inventory data):')
    for s, e, sz in small[:15]:
        hex_str = ' '.join(f'{data[s+i]:02X}' for i in range(sz))
        
        # Try to interpret
        interp = ''
        if sz == 1:
            interp = f'u8={data[s]:3d}'
        elif sz == 2:
            val = struct.unpack('<H', data[s:e])[0]
            interp = f'u16={val:5d}'
        elif sz == 4:
            val = struct.unpack('<I', data[s:e])[0]
            interp = f'u32={val:10d}'
        
        print(f'  0x{s:04X} ({sz:2d}b): {hex_str:30s} {interp}')
    
    print()
    print('First 5 medium blocks:')
    for s, e, sz in medium[:5]:
        hex_str = ' '.join(f'{data[s+i]:02X}' for i in range(min(20, sz)))
        if sz > 20:
            hex_str += '...'
        print(f'  0x{s:04X} ({sz:2d}b): {hex_str}')

def main():
    with open('../game/SQUAD0.CAM', 'rb') as f:
        data = f.read()
    
    blocks = find_target_blocks(data)
    print(f'Found {len(blocks)} strategic targets')
    print()
    
    # Parse all targets
    targets = []
    for start, end in blocks:
        target = parse_target(data, start, end)
        targets.append(target)
    
    # Show first 5 targets in detail
    print('=== FIRST 5 TARGETS (DETAILED) ===')
    print()
    for i, t in enumerate(targets[:5]):
        print(f'Target {i}: ID={t["id"]} (0x{t["id"]:04X})')
        print(f'  Bytes 2-5: {t["byte_2"]:02X} {t["byte_3"]:02X} {t["byte_4"]:02X} {t["byte_5"]:02X}')
        print(f'  Byte 6: 0x{t["separator"]:02X} (expect 0x3C)')
        print(f'  Byte 7: {t["field_7"]:3d} (0x{t["field_7"]:02X})')
        print(f'  Array 1 (+8-15):  {[f"{v:3d}" for v in t["array1"]]}')
        print(f'  Array 2 (+16-23): {[f"0x{v:02X}" for v in t["array2"]]}')
        print(f'  Array 3 (+24-31): {[f"{v:3d}" for v in t["array3"]]}')
        if t['data_32_39']:
            print(f'  Data (+32-39):    {[f"{v:3d}" for v in t["data_32_39"]]}')
        if t['uint16_values']:
            print(f'  Uint16 values: {[f"{v:4d}" for v in t["uint16_values"][:6]]}...')
        print()
    
    # Analyze patterns
    print('=== PATTERN ANALYSIS ===')
    print()
    
    # Check array1 (bytes 8-15) - these look like strength percentages
    print('Array 1 value distribution (bytes 8-15):')
    all_a1_vals = []
    for t in targets:
        all_a1_vals.extend(t['array1'])
    print(f'  Range: {min(all_a1_vals)}-{max(all_a1_vals)}')
    print(f'  Values that look like percentages (0-100): {sum(1 for v in all_a1_vals if 0 <= v <= 100)} / {len(all_a1_vals)}')
    print()
    
    # Check byte 7 - might be bit flags or combined field
    print('Byte 7 distribution (field after 0x3C):')
    byte7_vals = [t['field_7'] for t in targets]
    print(f'  Range: {min(byte7_vals)}-{max(byte7_vals)}')
    print(f'  Unique values: {sorted(set(byte7_vals))}')
    print()
    
    # Check if arrays have patterns
    print('Array pattern check:')
    print('  Targets with all 05 in array1:', sum(1 for t in targets if all(v == 5 for v in t['array1'])))
    print('  Targets with repeated values in array1:', sum(1 for t in targets if len(set(t['array1'])) <= 3))
    print('  Targets with repeated values in array2:', sum(1 for t in targets if len(set(t['array2'])) <= 3))
    print()
    
    # Now analyze small blocks
    analyze_small_blocks(data)

if __name__ == '__main__':
    main()
