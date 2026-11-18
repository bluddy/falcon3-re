"""
Comprehensive search for .RFM file references in the executable.
Search for: "*.RFM", ".RFM", "RFM" strings and patterns.
"""

import idc
import idaapi
import idautils
from pathlib import Path

print("=" * 70)
print("COMPREHENSIVE RFM STRING SEARCH")
print("=" * 70)
print()

idaapi.auto_wait()

output_lines = []

# Search for all strings containing "RFM"
print("Searching for strings containing 'RFM'...")
print("-" * 70)

rfm_strings = []

for s in idautils.Strings():
    s_val = str(s)
    if 'RFM' in s_val.upper() or 'rfm' in s_val:
        rfm_strings.append({
            'addr': s.ea,
            'value': s_val,
            'length': s.length
        })
        line = f"Found @ 0x{s.ea:X}: '{s_val}' (len={s.length})"
        print(line)
        output_lines.append(line)

print(f"\nTotal RFM strings found: {len(rfm_strings)}")
print()

# For each string, find cross-references
for rfm_str in rfm_strings:
    print("=" * 70)
    line = f"Analyzing string @ 0x{rfm_str['addr']:X}: '{rfm_str['value']}'"
    print(line)
    output_lines.append(line)
    print("=" * 70)
    
    # Get xrefs
    xrefs = list(idautils.XrefsTo(rfm_str['addr']))
    
    if not xrefs:
        line = "  No cross-references found"
        print(line)
        output_lines.append(line)
        continue
    
    print(f"  Found {len(xrefs)} cross-references:")
    output_lines.append(f"  Found {len(xrefs)} cross-references:")
    
    for xref in xrefs:
        from_addr = xref.frm
        
        # Get function containing this xref
        func = idaapi.get_func(from_addr)
        if func:
            func_name = idc.get_func_name(from_addr)
            func_start = func.start_ea
            func_size = func.end_ea - func.start_ea
            
            line = f"\n  Function: {func_name}"
            print(line)
            output_lines.append(line)
            
            line = f"    Address: 0x{func_start:X}"
            print(line)
            output_lines.append(line)
            
            line = f"    Size: {func_size} bytes"
            print(line)
            output_lines.append(line)
            
            line = f"    Xref from: 0x{from_addr:X}"
            print(line)
            output_lines.append(line)
            
            # Show context around the reference
            print(f"\n    Context (20 instructions):")
            output_lines.append("    Context:")
            
            # Go back 10 instructions
            ea = from_addr
            for _ in range(10):
                prev = idc.prev_head(ea)
                if prev == idc.BADADDR:
                    break
                ea = prev
            
            # Show 20 instructions
            for i in range(20):
                if ea >= func.end_ea:
                    break
                    
                disasm = idc.GetDisasm(ea)
                marker = " <-- STRING REF" if ea == from_addr else ""
                line = f"      0x{ea:05X}: {disasm}{marker}"
                print(line)
                output_lines.append(line)
                
                ea = idc.next_head(ea)
        else:
            line = f"  Xref @ 0x{from_addr:X} - not in a function"
            print(line)
            output_lines.append(line)
    
    print()

# Also search for common file operation patterns
print("=" * 70)
print("SEARCHING FOR FILE OPEN PATTERNS")
print("=" * 70)
print()

# Look for DOS INT 21h with AH=3D (open file)
print("Searching for DOS INT 21h file open calls...")

file_opens = []
ea = 0
while ea != idc.BADADDR:
    ea = idc.find_binary(ea, idc.SEARCH_DOWN, "B4 3D CD 21")
    if ea != idc.BADADDR:
        func = idaapi.get_func(ea)
        if func:
            func_name = idc.get_func_name(ea)
            file_opens.append({
                'addr': ea,
                'func': func_name,
                'func_start': func.start_ea
            })
        ea = idc.next_head(ea)

print(f"Found {len(file_opens)} file open calls")

# Check which ones are near string references
for fopen in file_opens[:10]:  # Check first 10
    line = f"\nFile open @ 0x{fopen['addr']:X} in {fopen['func']}"
    print(line)
    output_lines.append(line)
    
    # Check for nearby string references
    ea = fopen['addr']
    for _ in range(20):  # Check 20 instructions before
        ea = idc.prev_head(ea)
        if ea == idc.BADADDR:
            break
        
        # Check for LEA DX or MOV DX with string address
        for xref in idautils.DataRefsFrom(ea):
            # Check if this is a string
            for rfm_str in rfm_strings:
                if xref == rfm_str['addr']:
                    line = f"  Found string ref @ 0x{ea:X}: '{rfm_str['value']}'"
                    print(line)
                    output_lines.append(line)

print()

# Save results
output_path = Path(__file__).parent.parent / "temp" / "rfm_string_search.txt"
with open(output_path, 'w') as f:
    f.write('\n'.join(output_lines))

print("=" * 70)
print(f"Results saved to: {output_path}")
print("=" * 70)

idc.qexit(0)
