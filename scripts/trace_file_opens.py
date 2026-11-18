"""
Trace file open operations to find RFM loader.
Look for patterns: string ref → file_open → read → process
"""

import idc
import idaapi
import idautils
from pathlib import Path

print("=" * 70)
print("TRACING FILE OPEN OPERATIONS")
print("=" * 70)
print()

idaapi.auto_wait()

output_lines = []

# dos_file_open function
file_open_addr = 0x0226BD

print(f"DOS file open function: 0x{file_open_addr:X}")
print()

# Find all callers of dos_file_open
print("Finding all callers of dos_file_open...")
print("-" * 70)

callers = []
for xref in idautils.CodeRefsTo(file_open_addr, False):
    func = idaapi.get_func(xref)
    if func:
        func_name = idc.get_func_name(xref)
        callers.append({
            'addr': xref,
            'func_name': func_name,
            'func_start': func.start_ea,
            'func_size': func.end_ea - func.start_ea
        })

print(f"Found {len(callers)} callers")
print()

# For each caller, look for string references nearby
for i, caller in enumerate(callers[:30]):  # Check first 30
    print(f"\nCaller {i+1}: {caller['func_name']} @ 0x{caller['func_start']:X}")
    output_lines.append(f"\nCaller: {caller['func_name']} @ 0x{caller['func_start']:X}")
    output_lines.append(f"  Size: {caller['func_size']} bytes")
    output_lines.append(f"  Call from: 0x{caller['addr']:X}")
    
    # Search backwards from the call for string references
    ea = caller['addr']
    strings_found = []
    
    for _ in range(50):  # Look back 50 instructions
        ea = idc.prev_head(ea)
        if ea == idc.BADADDR or ea < caller['func_start']:
            break
        
        # Check for data references (strings)
        for dref in idautils.DataRefsFrom(ea):
            # Try to read as string
            s = idc.get_strlit_contents(dref)
            if s:
                s_str = s.decode('ascii', errors='ignore')
                strings_found.append({
                    'addr': ea,
                    'str_addr': dref,
                    'value': s_str,
                    'disasm': idc.GetDisasm(ea)
                })
    
    if strings_found:
        line = f"  Strings found:"
        print(line)
        output_lines.append(line)
        
        for s in strings_found:
            line = f"    @ 0x{s['addr']:05X}: '{s['value']}'"
            print(line)
            output_lines.append(line)
            
            # Check if this is an RFM file
            if 'rfm' in s['value'].lower() or 'RFM' in s['value']:
                print(f"    *** RFM FILE FOUND! ***")
                output_lines.append("    *** RFM FILE FOUND! ***")
                
                # Disassemble the function
                print(f"\n    Full function disassembly:")
                output_lines.append("\n    Full function disassembly:")
                
                ea = caller['func_start']
                instr_count = 0
                while ea < caller['func_start'] + caller['func_size'] and instr_count < 100:
                    disasm = idc.GetDisasm(ea)
                    marker = " <-- STRING REF" if ea == s['addr'] else ""
                    marker += " <-- CALL FILE_OPEN" if ea == caller['addr'] else ""
                    line = f"      0x{ea:05X}: {disasm}{marker}"
                    print(line)
                    output_lines.append(line)
                    ea = idc.next_head(ea)
                    instr_count += 1

# Save output
output_path = Path(__file__).parent.parent / "temp" / "file_open_trace.txt"
with open(output_path, 'w') as f:
    f.write('\n'.join(output_lines))

print()
print("=" * 70)
print(f"Output saved to: {output_path}")
print("=" * 70)

idc.qexit(0)
