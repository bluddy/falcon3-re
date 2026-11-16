"""
Analyze mission slot field offsets from all writer functions
"""

import json
import re

def parse_offset(dest_str):
    """Extract numeric offset from es:[bx+offset] pattern"""
    # Pattern: es:[bx+14h] or es:[bx+0x14] or es:[bx]
    if '+' not in dest_str:
        return 0
    
    # Extract the part after '+'
    match = re.search(r'\+([0-9A-Fa-fx]+)h?\]', dest_str)
    if match:
        offset_str = match.group(1)
        if offset_str.startswith('0x'):
            return int(offset_str, 16)
        else:
            # Try hex first
            try:
                return int(offset_str, 16)
            except:
                try:
                    return int(offset_str, 10)
                except:
                    return None
    return None

def analyze_field_patterns():
    """Analyze all mission slot field writes"""
    
    json_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\mission_slot_writers.json'
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    print("=" * 80)
    print("MISSION SLOT ARRAY FIELD ANALYSIS")
    print("=" * 80)
    print(f"Pointer: {data['pointer']} @ 0x{data['pointer_addr']:X}")
    print(f"Total references: {data['total_references']}")
    print(f"Functions with writes: {sum(1 for f in data['functions'] if f['total_writes'] > 0)}")
    print()
    
    # Collect all field writes
    field_writes = {}
    
    for func_data in data['functions']:
        if func_data['total_writes'] == 0:
            continue
        
        func_name = func_data['name']
        
        for ref in func_data['references']:
            for write in ref['writes']:
                offset = parse_offset(write['dest'])
                
                if offset is None:
                    # Variable offset like es:[bx+di] or es:[bx+si]
                    offset_key = write['dest']
                else:
                    offset_key = offset
                
                if offset_key not in field_writes:
                    field_writes[offset_key] = []
                
                field_writes[offset_key].append({
                    'function': func_name,
                    'addr': write['addr'],
                    'disasm': write['disasm'],
                    'src': write['src']
                })
    
    # Sort by offset
    print("MISSION SLOT FIELD OFFSETS (20 bytes total):")
    print("-" * 80)
    
    sorted_offsets = sorted([k for k in field_writes.keys() if isinstance(k, int)])
    
    for offset in sorted_offsets:
        writes = field_writes[offset]
        print(f"\n+0x{offset:02X} ({offset:2d}) - {len(writes)} write(s)")
        
        # Group by source value
        by_source = {}
        for w in writes:
            src = w['src']
            if src not in by_source:
                by_source[src] = []
            by_source[src].append(w)
        
        for src, ws in sorted(by_source.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"  {src:20s} : {len(ws):2d}x - {ws[0]['function']}")
            if len(ws) <= 3:
                for w in ws:
                    print(f"      0x{w['addr']:06X}: {w['disasm']}")
    
    # Variable offsets
    print("\n\nVARIABLE OFFSETS (indexed writes):")
    print("-" * 80)
    
    var_offsets = [k for k in field_writes.keys() if not isinstance(k, int)]
    for offset_key in var_offsets:
        writes = field_writes[offset_key]
        print(f"\n{offset_key} - {len(writes)} write(s)")
        for w in writes[:5]:
            print(f"  0x{w['addr']:06X}: {w['disasm']} ({w['function']})")
    
    # Identify likely field boundaries
    print("\n\nFIELD STRUCTURE HYPOTHESIS:")
    print("-" * 80)
    print("Based on write patterns (20 bytes total):")
    print()
    
    if 0 in field_writes:
        print(f"+0x00 (2 bytes): Mission label/ID (string start)")
        print(f"  - {len(field_writes[0])} writes of various values")
    
    if 1 in field_writes:
        print(f"+0x01 (1 byte): String terminator or flag")
        print(f"  - {len(field_writes[1])} writes")
    
    # Look for gaps and patterns
    max_offset = max([k for k in field_writes.keys() if isinstance(k, int)])
    print(f"\nHighest fixed offset: +0x{max_offset:02X} ({max_offset} bytes)")
    print(f"Expected structure size: 20 bytes (0x14)")
    
    if max_offset >= 20:
        print(f"\nWARNING: Writes beyond 20 bytes detected!")
        print(f"This suggests the pointer may NOT always point to a MissionSlot,")
        print(f"or the structure is larger than 20 bytes in some contexts.")
    
    # Look for 20-byte stride patterns
    stride_offsets = [offset for offset in sorted_offsets if offset % 20 == 0 or (offset > 0 and offset % 20 == 1)]
    if stride_offsets:
        print(f"\nOffsets matching 20-byte stride: {stride_offsets}")
    
    return field_writes

if __name__ == '__main__':
    field_writes = analyze_field_patterns()
