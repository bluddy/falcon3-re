#!/usr/bin/env python3
"""Map dispatcher table entries that fall in overlay record 69."""
import json

# Load overlay placement
op = json.load(open('../ida_falconcd/overlay_placement.json'))

# Find record 69
rec69 = [r for r in op if r['idx'] == 69][0]

print("=" * 80)
print("OVERLAY RECORD 69 ANALYSIS")
print("=" * 80)
print(f"\nRecord 69 details:")
print(f"  Link segment (w0): 0x{rec69['w0']:04X}")
print(f"  IDA base address: 0x{rec69['ida_ea']:05X}")
print(f"  Length: {rec69['real_len']} bytes")
print(f"  Segment name: {rec69['seg_name']}")
print(f"  Link segment range: 0x{rec69['w0']:04X}..0x{rec69['w0'] + rec69['real_len']//16:04X}")

# Table entries that fall in this record
table_entries = [
    (1, 0x0000, 0xFFFF),  # Special entry
    (5, 0x006E, 0x0000),
    (6, 0x0100, 0x0058),
    (10, 0x900E, 0x0000),
    (11, 0x90B4, 0x1F6C),
    (12, 0x8A87, 0x1F6C),
    (13, 0x7AC0, 0x1F6C),
    (14, 0x7A7D, 0x1F6C),
    (15, 0x7618, 0x1F6C),
    (16, 0x758A, 0x1F6C),
    (17, 0x746E, 0x1F6C),
    (18, 0x7389, 0x1F6C),
    (19, 0x721D, 0x1F6C),
    (20, 0x70AD, 0x1F6C),
    (21, 0x6E05, 0x1F6C),
    (22, 0x8360, 0x1F6C),
    (23, 0x8357, 0x1F6C),
    (24, 0x0000, 0x1F6C),
    (25, 0x0258, 0x0000),
    (26, 0x0000, 0x0002),
    (27, 0x6E4C, 0x6ED3),
]

rec69_base_link = rec69['w0']
rec69_base_ida = rec69['ida_ea']
image_para = 0x1F5  # Load base

print("\n" + "=" * 80)
print("DISPATCHER TABLE ENTRIES -> RECORD 69 FUNCTIONS")
print("=" * 80)

# Load function_bytes
fb = json.load(open('../ida_falconcd/function_bytes.json'))

print(f"\n{'Idx':<5} {'Runtime Seg':<13} {'Offset':<10} {'Link Seg':<12} {'IDA Addr':<12} {'Function':<25} {'Size'}")
print("-" * 100)

results = []
for idx, runtime_seg, offset in table_entries:
    # Convert runtime to link: link = runtime - image_para
    link_seg = runtime_seg - image_para if runtime_seg > 0 else 0
    
    # Check if this link segment is in record 69
    in_rec69 = rec69_base_link <= link_seg < rec69_base_link + (rec69['real_len'] // 16)
    
    if in_rec69 or runtime_seg == 0:
        # Calculate IDA address: 
        # offset_in_rec69 = (link_seg - rec69_base_link) * 16 + offset
        # ida_addr = rec69_base_ida + offset_in_rec69
        
        if runtime_seg > 0:
            offset_in_rec69 = (link_seg - rec69_base_link) * 16 + offset
            ida_addr = rec69_base_ida + offset_in_rec69
        else:
            # Segment 0 entries - might be special or resident
            if offset == 0xFFFF:
                ida_addr = None  # Invalid
            else:
                # Try as resident offset
                ida_addr = 0x10000 + offset
        
        # Look for function
        found_func = None
        func_size = None
        
        if ida_addr:
            for fname, fdata in fb.items():
                if fdata['ea'] == ida_addr:
                    found_func = fname
                    func_size = fdata['size']
                    break
                # Check mid-body
                if fdata['ea'] <= ida_addr < fdata['ea'] + fdata.get('size', 0):
                    offset_in = ida_addr - fdata['ea']
                    found_func = f"{fname}+0x{offset_in:X}"
                    func_size = fdata['size']
                    break
        
        func_str = found_func if found_func else "???"
        size_str = f"{func_size}B" if func_size else ""
        ida_str = f"0x{ida_addr:05X}" if ida_addr else "INVALID"
        link_str = f"0x{link_seg:04X}" if runtime_seg > 0 else "n/a"
        
        print(f"{idx:<5} 0x{runtime_seg:04X}        0x{offset:04X}     {link_str:<12} {ida_str:<12} {func_str:<25} {size_str}")
        
        results.append({
            'index': idx,
            'runtime_seg': runtime_seg,
            'offset': offset,
            'link_seg': link_seg,
            'ida_address': ida_addr,
            'function': func_str,
            'in_record_69': in_rec69
        })

# Summary
rec69_entries = [r for r in results if r['in_record_69']]
print(f"\n\nSummary:")
print(f"  Total table entries: {len(table_entries)}")
print(f"  In record 69: {len(rec69_entries)}")
print(f"  Functions found: {len([r for r in rec69_entries if r['function'] and r['function'] != '???'])}")

# Save
output = {
    'record_69': {
        'idx': 69,
        'link_base': rec69_base_link,
        'ida_base': rec69_base_ida,
        'length': rec69['real_len'],
        'seg_name': rec69['seg_name']
    },
    'mapped_entries': results
}

json.dump(output, open('dispatcher_record69_mapping.json', 'w'), indent=2)
print(f"\nSaved to dispatcher_record69_mapping.json")
