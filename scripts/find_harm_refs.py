"""
Find references to AGM-88 HARM weapon type (0x19).
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

print("=" * 80)
print("HARM WEAPON TYPE (0x19) REFERENCE SEARCH")
print("=" * 80)

# Wait for auto-analysis
print("Waiting for auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete\n")

results = {
    'harm_type': '0x19',
    'references': []
}

# Search for immediate value 0x19 in code segment
text_seg = idaapi.get_segm_by_name(".text")
if not text_seg:
    print("ERROR: .text segment not found")
    idc.qexit(1)

print(f"Searching .text segment: {text_seg.start_ea:#x} - {text_seg.end_ea:#x}")

ea = text_seg.start_ea
count = 0
max_refs = 50  # Limit output

while ea < text_seg.end_ea and count < max_refs:
    insn = idaapi.insn_t()
    insn_len = idaapi.decode_insn(insn, ea)
    
    if insn_len > 0:
        # Check for cmp/mov/test with 0x19
        if insn.itype in [idaapi.NN_cmp, idaapi.NN_mov, idaapi.NN_test]:
            for op in insn.ops:
                if op.type == idaapi.o_imm and op.value == 0x19:
                    func_name = idc.get_func_name(ea)
                    disasm = idc.generate_disasm_line(ea, 0)
                    
                    results['references'].append({
                        'address': hex(ea),
                        'function': func_name if func_name else 'unknown',
                        'disasm': disasm
                    })
                    count += 1
                    print(f"  {count}. {ea:#08x} in {func_name}: {disasm}")
                    break
    
    ea = idc.next_head(ea, text_seg.end_ea)

print(f"\nFound {len(results['references'])} references to weapon type 0x19 (HARM)")

# Save to JSON
output_file = Path(__file__).parent / "harm_refs.json"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"Results saved to: {output_file}")
print("Exiting IDA...")

# Exit immediately
idc.qexit(0)
