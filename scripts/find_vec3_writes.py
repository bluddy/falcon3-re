"""
Find all writes to vec3_x/y/z_component globals.
These are used as inputs to fixed_vec3_accumulate_a.
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

print("=" * 70)
print("FINDING WRITES TO VEC3 COMPONENTS")
print("=" * 70)
print()

# Wait for auto-analysis
print("Waiting for auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete\n")

# The vec3 component addresses (from disassembly)
vec3_x = 0x235B1
vec3_y = 0x235B3
vec3_z = 0x235B5

print(f"Searching for writes to:")
print(f"  vec3_x_component @ 0x{vec3_x:X}")
print(f"  vec3_y_component @ 0x{vec3_y:X}")
print(f"  vec3_z_component @ 0x{vec3_z:X}")
print()

# Find all cross-references (xrefs) to these addresses
results = []

for name, addr in [("vec3_x_component", vec3_x), ("vec3_y_component", vec3_y), ("vec3_z_component", vec3_z)]:
    print(f"\nAnalyzing {name} @ 0x{addr:X}:")
    print("-" * 70)
    
    xrefs = list(idautils.DataRefsTo(addr))
    print(f"Found {len(xrefs)} references")
    
    for xref in xrefs:
        # Get the instruction
        mnem = idc.print_insn_mnem(xref)
        disasm = idc.GetDisasm(xref)
        func_name = idc.get_func_name(xref)
        
        # Check if it's a write (MOV to memory)
        is_write = mnem in ["mov"] and idc.print_operand(xref, 0).startswith("cs:")
        
        results.append({
            "address": hex(xref),
            "name": name,
            "mnem": mnem,
            "disasm": disasm,
            "function": func_name,
            "is_write": is_write
        })
        
        write_str = " [WRITE]" if is_write else ""
        print(f"  0x{xref:05X}: {disasm:50s} in {func_name}{write_str}")

print()
print("=" * 70)
print(f"TOTAL: {len(results)} references found")
print("=" * 70)

# Save results
output_path = Path(__file__).parent.parent / "temp" / "vec3_component_writes.json"
with open(output_path, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to: {output_path}")

# CRITICAL: Exit explicitly!
idc.qexit(0)
