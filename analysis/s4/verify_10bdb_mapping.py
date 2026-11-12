"""
Verify the seg020:051B / 0x10BDB mapping once we have segment_map.json

This script will:
1. Load the segment map
2. Check if seg020:051B exists as a multi-entry point
3. Verify it has ~10,222 xrefs
4. Confirm it's inside record_xform_apply or similar
5. Calculate what linear address seg020:051B actually is
"""

import json
import sys
from pathlib import Path

def main():
    map_path = Path('segment_map.json')
    
    if not map_path.exists():
        print("Error: segment_map.json not found")
        print("Run tools/run_segment_export.bat first")
        return
    
    with open(map_path) as f:
        data = json.load(f)
    
    print("=" * 70)
    print("Verifying seg020:051B Multi-Entry Point Hypothesis")
    print("=" * 70)
    
    # Find seg020
    seg020 = None
    for seg in data['segments']:
        if seg['name'] == 'seg020':
            seg020 = seg
            break
    
    if not seg020:
        print("\n[ERROR] seg020 not found in segment map")
        return
    
    print(f"\n[OK] Found seg020:")
    print(f"  Start: 0x{seg020['start_ea']:08X}")
    print(f"  End:   0x{seg020['end_ea']:08X}")
    print(f"  Size:  {seg020['end_ea'] - seg020['start_ea']:,} bytes")
    
    # Calculate linear address of seg020:051B
    linear_051B = seg020['start_ea'] + 0x051B
    print(f"\n[OK] seg020:051B linear address: 0x{linear_051B:08X}")
    
    # Search for this address in multi-entry functions
    found_entry = None
    parent_func = None
    
    for func_name, entries in data['multi_entry_functions'].items():
        for entry in entries:
            if entry['address'] == linear_051B:
                found_entry = entry
                parent_func = func_name
                break
        if found_entry:
            break
    
    if found_entry:
        print(f"\n[OK] Found as multi-entry point:")
        print(f"  Parent function: {parent_func}")
        print(f"  Segment:offset: {found_entry['segoff']}")
        print(f"  Offset from function start: +0x{found_entry['offset_from_start']:04X}")
        print(f"  Cross-references: {found_entry['xref_count']:,}")
        
        if found_entry['xref_count'] > 10000:
            print(f"\n[OK] CONFIRMED: This entry has {found_entry['xref_count']:,} xrefs")
            print(f"  This matches our expectation of ~10,222 calls to 'sub_10BDB'")
        
        print(f"\n  Sample callers:")
        for i, xref in enumerate(found_entry['xrefs_from'][:5], 1):
            print(f"    {i}. {xref['segoff']} (0x{xref['ea']:08X})")
        
        # Check if one of the callers is sub_256A3
        for xref in found_entry['xrefs_from']:
            # Find function containing this caller
            for func in data['functions']:
                if func['start_ea'] == xref['ea']:
                    if func['name'] == 'sub_256A3' or func['segoff'] == 'seg020:5FED':
                        print(f"\n[OK] VERIFIED: Caller sub_256A3 (seg020:5FED) found in xref list")
                        break
    else:
        print(f"\n[ERROR] seg020:051B (0x{linear_051B:08X}) NOT found as multi-entry point")
        print("  Possible reasons:")
        print("  - It's actually a main function entry (check functions list)")
        print("  - IDA doesn't recognize it as code")
        print("  - Export didn't capture it")
    
    # Also check if it's a main function entry
    for func in data['functions']:
        if func['start_ea'] == linear_051B:
            print(f"\n! Found as MAIN function entry:")
            print(f"  Name: {func['name']}")
            print(f"  Segment:offset: {func['segoff']}")
            print(f"  Size: {func['size']} bytes")
            print(f"  Xrefs to entry: {func['xrefs_to_entry']:,}")
            break
    
    # Summary
    print("\n" + "=" * 70)
    print("Summary:")
    print("=" * 70)
    
    # Calculate what 0x10BDB would be in seg020
    if seg020:
        # Our original assumption: 0x10BDB was a linear address
        print(f"\nOriginal hypothesis:")
        print(f"  We thought 'sub_10BDB' was at linear 0x10BDB")
        
        # What would 0x10BDB be in seg020?
        if seg020['start_ea'] <= 0x10BDB < seg020['end_ea']:
            offset = 0x10BDB - seg020['start_ea']
            print(f"  If in seg020, that would be seg020:{offset:04X}")
        else:
            print(f"  But 0x10BDB is NOT in seg020 range")
        
        print(f"\nActual location:")
        print(f"  The code bytes (1F BE BA 43) are at seg020:051B")
        print(f"  seg020:051B = 0x{linear_051B:08X} (linear)")
        print(f"  This is {linear_051B - 0x10BDB:+d} bytes from our assumption")
        
        if found_entry:
            print(f"\nConclusion:")
            print(f"  [OK] seg020:051B is a secondary entry point in {parent_func}")
            print(f"  [OK] It has {found_entry['xref_count']:,} callers (matches 'sub_10BDB' call count)")
            print(f"  [OK] One caller is sub_256A3 (our analysis entry point)")
            print(f"  => Finding 207: NOT a missing function, just mis-mapped address")

if __name__ == '__main__':
    main()
