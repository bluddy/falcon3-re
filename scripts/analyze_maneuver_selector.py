"""
Analyze ai_combat_maneuver_selector function to understand how it uses .RFM data.
Address: 0x3E2D3 (505 bytes)
"""

import idc
import idaapi
import idautils
from pathlib import Path

print("=" * 70)
print("ANALYZING AI COMBAT MANEUVER SELECTOR")
print("=" * 70)
print()

idaapi.auto_wait()

func_addr = 0x3E2D3
func_name = "ai_combat_maneuver_selector"

print(f"Function: {func_name}")
print(f"Address: 0x{func_addr:X}")
print()

# Get function info
func = idaapi.get_func(func_addr)
if not func:
    print("ERROR: Function not found!")
    idc.qexit(1)

func_size = func.end_ea - func.start_ea
print(f"Size: {func_size} bytes")
print(f"Range: 0x{func.start_ea:X} - 0x{func.end_ea:X}")
print()

# Find all memory accesses
print("=" * 70)
print("MEMORY ACCESS PATTERNS")
print("=" * 70)
print()

output_lines = []

memory_accesses = []
ea = func.start_ea

while ea < func.end_ea:
    mnem = idc.print_insn_mnem(ea)
    
    # Look for memory operations
    if mnem in ["mov", "lea", "cmp", "test", "add", "sub", "and", "or"]:
        disasm = idc.GetDisasm(ea)
        
        # Check if it accesses memory
        for i in range(2):
            op = idc.print_operand(ea, i)
            if '[' in op:
                memory_accesses.append({
                    'addr': ea,
                    'mnem': mnem,
                    'disasm': disasm,
                    'operand': op
                })
                break
    
    ea = idc.next_head(ea)

print(f"Found {len(memory_accesses)} memory accesses")
print()

# Group by pattern
print("Memory access patterns (first 30):")
print("-" * 70)
for i, acc in enumerate(memory_accesses[:30]):
    line = f"0x{acc['addr']:05X}: {acc['disasm']}"
    print(line)
    output_lines.append(line)

print()

# Look for comparisons (43 comparisons mentioned in registry)
print("=" * 70)
print("COMPARISON OPERATIONS")
print("=" * 70)
print()

comparisons = []
ea = func.start_ea

while ea < func.end_ea:
    mnem = idc.print_insn_mnem(ea)
    
    if mnem in ["cmp", "test"]:
        disasm = idc.GetDisasm(ea)
        op0 = idc.print_operand(ea, 0)
        op1 = idc.print_operand(ea, 1)
        
        comparisons.append({
            'addr': ea,
            'disasm': disasm,
            'op0': op0,
            'op1': op1
        })
    
    ea = idc.next_head(ea)

print(f"Found {len(comparisons)} comparisons")
print()
print("First 20 comparisons:")
print("-" * 70)

for i, cmp in enumerate(comparisons[:20]):
    line = f"0x{cmp['addr']:05X}: {cmp['disasm']}"
    print(line)
    output_lines.append(line)

print()

# Look for function calls
print("=" * 70)
print("FUNCTION CALLS")
print("=" * 70)
print()

calls = []
for xref in idautils.CodeRefsFrom(func.start_ea, True):
    if xref >= func.start_ea and xref < func.end_ea:
        continue
    
    target_name = idc.get_func_name(xref)
    if target_name:
        calls.append({
            'target': xref,
            'name': target_name
        })

print(f"Found {len(calls)} function calls:")
print("-" * 70)
for call in calls:
    line = f"  0x{call['target']:X}: {call['name']}"
    print(line)
    output_lines.append(line)

print()

# Look for data references (might point to .RFM data or tables)
print("=" * 70)
print("DATA REFERENCES")
print("=" * 70)
print()

data_refs = []
ea = func.start_ea

while ea < func.end_ea:
    for xref in idautils.DataRefsFrom(ea):
        data_name = idc.get_name(xref)
        segment = idc.get_segm_name(xref)
        
        data_refs.append({
            'from': ea,
            'to': xref,
            'name': data_name if data_name else '(unnamed)',
            'segment': segment if segment else '(unknown)',
            'disasm': idc.GetDisasm(ea)
        })
    
    ea = idc.next_head(ea)

print(f"Found {len(data_refs)} data references:")
print("-" * 70)
for i, ref in enumerate(data_refs[:20]):
    line = f"0x{ref['from']:05X} -> 0x{ref['to']:X} ({ref['segment']}:{ref['name']})"
    print(line)
    output_lines.append(line)
    line = f"  {ref['disasm']}"
    print(line)
    output_lines.append(line)

print()

# Disassemble first 50 instructions
print("=" * 70)
print("FIRST 50 INSTRUCTIONS")
print("=" * 70)
print()

ea = func.start_ea
for i in range(50):
    disasm = idc.GetDisasm(ea)
    line = f"0x{ea:05X}: {disasm}"
    print(line)
    output_lines.append(line)
    ea = idc.next_head(ea)
    if ea >= func.end_ea:
        break

# Save output
output_path = Path(__file__).parent.parent / "temp" / "maneuver_selector_analysis.txt"
with open(output_path, 'w') as f:
    f.write('\n'.join(output_lines))

print()
print("=" * 70)
print(f"Analysis saved to: {output_path}")
print("=" * 70)

idc.qexit(0)
