"""
Search for "*.RFM" or ".RFM" byte patterns in code and data segments.
"""

import idc
import idaapi
from pathlib import Path

print("=" * 70)
print("SEARCHING FOR RFM BYTE PATTERNS")
print("=" * 70)
print()

idaapi.auto_wait()

output_lines = []

# Search for "*.RFM" pattern (ASCII bytes)
# * = 0x2A, . = 0x2E, R = 0x52, F = 0x46, M = 0x4D
patterns = [
    ("2A 2E 52 46 4D", "*.RFM"),
    ("2E 52 46 4D", ".RFM"),
    ("52 46 4D", "RFM"),
]

for pattern_bytes, pattern_name in patterns:
    print(f"\nSearching for: '{pattern_name}' ({pattern_bytes})")
    print("-" * 70)
    
    # Search in all segments
    ea = 0
    found_count = 0
    
    while ea != idc.BADADDR:
        ea = idc.find_binary(ea, idc.SEARCH_DOWN | idc.SEARCH_CASE, pattern_bytes)
        
        if ea != idc.BADADDR:
            found_count += 1
            
            # Get segment info
            seg = idaapi.getseg(ea)
            seg_name = idc.get_segm_name(ea) if seg else "unknown"
            
            line = f"  Found @ 0x{ea:X} in segment {seg_name}"
            print(line)
            output_lines.append(line)
            
            # Try to read as string
            s = idc.get_strlit_contents(ea - 10, 20)
            if s:
                s_str = s.decode('ascii', errors='ignore')
                line = f"    String context: '{s_str}'"
                print(line)
                output_lines.append(line)
            
            # Find xrefs to this location
            xrefs = list(idautils.XrefsTo(ea))
            if xrefs:
                line = f"    Cross-references: {len(xrefs)}"
                print(line)
                output_lines.append(line)
                
                for xref in xrefs[:5]:  # Show first 5
                    func = idaapi.get_func(xref.frm)
                    if func:
                        func_name = idc.get_func_name(xref.frm)
                        line = f"      From 0x{xref.frm:X} in {func_name}"
                        print(line)
                        output_lines.append(line)
            
            ea = idc.next_head(ea)
    
    print(f"  Total found: {found_count}")
    output_lines.append(f"  Total found: {found_count}")

# Also search for DEFBFM pattern (common filename prefix)
print("\n" + "=" * 70)
print("Searching for 'DEFBFM' pattern")
print("=" * 70)

# D E F B F M = 44 45 46 42 46 4D
ea = 0
while ea != idc.BADADDR:
    ea = idc.find_binary(ea, idc.SEARCH_DOWN | idc.SEARCH_CASE, "44 45 46 42 46 4D")
    
    if ea != idc.BADADDR:
        seg_name = idc.get_segm_name(ea)
        line = f"  Found @ 0x{ea:X} in {seg_name}"
        print(line)
        output_lines.append(line)
        
        # Context
        s = idc.get_strlit_contents(ea, 15)
        if s:
            s_str = s.decode('ascii', errors='ignore')
            line = f"    String: '{s_str}'"
            print(line)
            output_lines.append(line)
        
        ea = idc.next_head(ea)

# Save output
output_path = Path(__file__).parent.parent / "temp" / "rfm_byte_search.txt"
with open(output_path, 'w') as f:
    f.write('\n'.join(output_lines))

print()
print("=" * 70)
print(f"Output saved to: {output_path}")
print("=" * 70)

idc.qexit(0)
