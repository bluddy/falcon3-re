"""
Find code that sets up vec3 components before calling fixed_vec3_accumulate_a.
Search in the vicinity of the call sites.
"""

import idc
import idaapi
from pathlib import Path

print("=" * 70)
print("FINDING VEC3 COMPONENT SETUP")
print("=" * 70)
print()

idaapi.auto_wait()

# Call sites we're interested in
call_sites = [
    0x4C3E8,  # Weapon 5
    0x4C434,  # Weapon 6  
    0x4C480,  # Weapon 9
]

output_lines = []

# vec3 component addresses (CS segment offsets)
vec3_x_offset = 0x35B1
vec3_y_offset = 0x35B3
vec3_z_offset = 0x35B5

for call_addr in call_sites:
    line = f"\nAnalyzing call @ 0x{call_addr:05X}:"
    print(line)
    output_lines.append(line)
    
    line = "=" * 70
    print(line)
    output_lines.append(line)
    
    # Search backwards 100 instructions
    ea = call_addr
    for i in range(100):
        ea = idc.prev_head(ea)
        if ea == idc.BADADDR:
            break
        
        disasm = idc.GetDisasm(ea)
        mnem = idc.print_insn_mnem(ea)
        
        # Look for MOV instructions
        if mnem == "mov":
            op0 = idc.print_operand(ea, 0)
            op1 = idc.print_operand(ea, 1)
            
            # Check if writing to CS segment (vec3 components)
            if "cs:" in op0 or "vec3" in disasm.lower():
                line = f"  0x{ea:05X}: {disasm}"
                print(line)
                output_lines.append(line)
            
            # Also look for moves from [SI+6/8/A]
            if "[si+" in op1.lower() and any(x in op1 for x in ["6]", "8]", "0Ah]"]):
                line = f"  0x{ea:05X}: {disasm}  <-- Reading entity field"
                print(line)
                output_lines.append(line)

output_path = Path(__file__).parent.parent / "temp" / "vec3_setup_near_call.txt"
with open(output_path, 'w') as f:
    f.write('\n'.join(output_lines))

print()
print(f"Saved to: {output_path}")
print("=" * 70)

idc.qexit(0)
