"""
Find the .RFM file loader by tracing the "*.RFM" string xref.
"""

import idc
import idaapi
import idautils
from pathlib import Path

print("=" * 70)
print("FINDING .RFM FILE LOADER")
print("=" * 70)
print()

idaapi.auto_wait()

# The string "*.RFM" is at 0x1381249 (from data_symbols.json: aPRfm)
rfm_string_addr = 0x1381249  # This is 0x151001 in linear addressing

print(f"Searching for xrefs to .RFM string @ 0x{rfm_string_addr:X}")
print()

# Get all cross-references to this string
xrefs = list(idautils.XrefsTo(rfm_string_addr))

print(f"Found {len(xrefs)} references:")
print("-" * 70)

output_lines = []

for xref in xrefs:
    from_addr = xref.frm
    xref_type = xref.type
    
    # Get the function containing this xref
    func = idaapi.get_func(from_addr)
    if func:
        func_name = idc.get_func_name(from_addr)
        func_start = func.start_ea
        func_end = func.end_ea
        func_size = func_end - func_start
        
        line = f"\nFunction: {func_name}"
        print(line)
        output_lines.append(line)
        
        line = f"  Address: 0x{func_start:X} - 0x{func_end:X}"
        print(line)
        output_lines.append(line)
        
        line = f"  Size: {func_size} bytes"
        print(line)
        output_lines.append(line)
        
        line = f"  Xref from: 0x{from_addr:X} (type={xref_type})"
        print(line)
        output_lines.append(line)
        
        # Disassemble around the xref (20 instructions before and after)
        print("\n  Context (10 instructions before and 10 after):")
        output_lines.append("\n  Context:")
        
        # Go back 10 instructions
        ea = from_addr
        for _ in range(10):
            ea = idc.prev_head(ea)
        
        # Print 20 instructions
        for i in range(20):
            disasm = idc.GetDisasm(ea)
            marker = " <-- STRING REF" if ea == from_addr else ""
            line = f"    0x{ea:05X}: {disasm}{marker}"
            print(line)
            output_lines.append(line)
            ea = idc.next_head(ea)
        
        print()
    else:
        line = f"\nXref @ 0x{from_addr:X} - not in a function"
        print(line)
        output_lines.append(line)

# Save output
output_path = Path(__file__).parent.parent / "temp" / "rfm_loader_found.txt"
with open(output_path, 'w') as f:
    f.write('\n'.join(output_lines))

print("=" * 70)
print(f"Output saved to: {output_path}")
print("=" * 70)

idc.qexit(0)
