"""
Check the actual target of CALL instructions in ag_weapon_entity_initialize.
"""

import idc
import idaapi
from pathlib import Path

print("=" * 70)
print("CHECKING CALL TARGETS")
print("=" * 70)
print()

idaapi.auto_wait()

# Check the calls we're interested in
call_sites = [
    0x4C3E8,  # Weapon 5
    0x4C434,  # Weapon 6
    0x4C480,  # Weapon 9
]

output_lines = []

for call_addr in call_sites:
    # Get the instruction
    disasm = idc.GetDisasm(call_addr)
    mnem = idc.print_insn_mnem(call_addr)
    
    if mnem == "call":
        # Get the target address
        target = idc.get_operand_value(call_addr, 0)
        target_name = idc.get_func_name(target)
        
        line = f"0x{call_addr:05X}: {disasm}"
        print(line)
        output_lines.append(line)
        
        line = f"  Target: 0x{target:05X} ({target_name})"
        print(line)
        output_lines.append(line)
        
        # Check if this is fixed_vec3_accumulate_a
        if target == 0x22C91:
            line = f"  -> This IS fixed_vec3_accumulate_a"
            print(line)
            output_lines.append(line)
        else:
            line = f"  -> This is NOT fixed_vec3_accumulate_a (0x22C91)"
            print(line)
            output_lines.append(line)
            
            line = f"  -> Disassembling target function..."
            print(line)
            output_lines.append(line)
            
            # Disassemble first 15 instructions of target
            ea = target
            for i in range(15):
                disasm_line = idc.GetDisasm(ea)
                line = f"     0x{ea:05X}: {disasm_line}"
                print(line)
                output_lines.append(line)
                ea = idc.next_head(ea)
        
        print()
        output_lines.append("")

output_path = Path(__file__).parent.parent / "temp" / "call_targets.txt"
with open(output_path, 'w') as f:
    f.write('\n'.join(output_lines))

print(f"Saved to: {output_path}")
print("=" * 70)

idc.qexit(0)
