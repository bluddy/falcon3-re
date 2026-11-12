#!/usr/bin/env python3
"""Check if dispatcher table segments match segsplit registry."""
import json

# Load segsplit registry
ss = json.load(open('../../registry/segsplit_expected.json'))

# Table segments from dispatcher analysis
table_segs = [
    0x6E05, 0x70AD, 0x721D, 0x7389, 0x746E, 0x758A, 0x7618, 
    0x7A7D, 0x7AC0, 0x8357, 0x8360, 0x8A87, 0x90B4, 0x900E
]

print(f"Checking {len(table_segs)} dispatcher table segments against segsplit registry...")
print(f"Segsplit registry has {len(ss['segments'])} segments\n")

matches = []
for seg_val in table_segs:
    for s in ss['segments']:
        if s['seg'] == seg_val:
            matches.append((seg_val, s))
            break

print(f"Found {len(matches)} exact matches!\n")

if matches:
    print(f"{'Table Seg':<12} {'Segment Name':<15} {'IDA Base':<12} {'IDA + 0x1F6C':<12}")
    print("-" * 60)
    for seg_val, s in matches:
        ida_base = s['start']
        ida_with_offset = ida_base + 0x1F6C
        print(f"0x{seg_val:04X}       {s['name']:<15} 0x{ida_base:05X}      0x{ida_with_offset:05X}")
    
    # Now check if those IDA addresses match functions
    print("\nChecking if IDA addresses (base + 0x1F6C) are function starts...")
    fb = json.load(open('../ida_falconcd/function_bytes.json'))
    
    print(f"\n{'Segment':<15} {'IDA Addr':<12} {'Function':<20} {'Size':<8}")
    print("-" * 70)
    for seg_val, s in matches:
        ida_addr = s['start'] + 0x1F6C
        # Look for function at this address
        found = None
        for fname, fdata in fb.items():
            if fdata['ea'] == ida_addr:
                found = (fname, fdata)
                break
        
        if found:
            fname, fdata = found
            print(f"{s['name']:<15} 0x{ida_addr:05X}    {fname:<20} {fdata['size']}B")
        else:
            print(f"{s['name']:<15} 0x{ida_addr:05X}    NO FUNCTION")

else:
    print("No exact matches found.")
    print("\nChecking if they might be RUNTIME segments...")
    print("Runtime segments would need to subtract load base 0x1F5 (493)")
    print("\nTrying: link_seg = runtime_seg - 0x1F5\n")
    
    print(f"{'Runtime Seg':<14} {'Link Seg':<12} {'Matched Segment':<20} {'IDA Base':<12}")
    print("-" * 70)
    
    runtime_matches = []
    for seg_val in table_segs:
        link_seg = seg_val - 0x1F5
        for s in ss['segments']:
            if s['seg'] == link_seg:
                runtime_matches.append((seg_val, link_seg, s))
                print(f"0x{seg_val:04X}         0x{link_seg:04X}       {s['name']:<20} 0x{s['start']:05X}")
                break
    
    if runtime_matches:
        print(f"\nFound {len(runtime_matches)} matches using runtime offset!")
        print("\nNow checking if +0x1F6C offset points to functions...")
        
        fb = json.load(open('../ida_falconcd/function_bytes.json'))
        
        print(f"\n{'Segment':<20} {'IDA + 0x1F6C':<12} {'Function':<25} {'Size':<8} {'Named?'}")
        print("-" * 90)
        
        for runtime_seg, link_seg, s in runtime_matches:
            ida_addr = s['start'] + 0x1F6C
            # Look for function at this address
            found = None
            for fname, fdata in fb.items():
                if fdata['ea'] == ida_addr:
                    found = (fname, fdata)
                    break
            
            if found:
                fname, fdata = found
                is_named = not fname.startswith('sub_')
                named_str = "YES" if is_named else "NO"
                print(f"{s['name']:<20} 0x{ida_addr:05X}    {fname:<25} {fdata['size']:<8}B {named_str}")
            else:
                print(f"{s['name']:<20} 0x{ida_addr:05X}    NO FUNCTION")
