"""
Find entity field writes that could be radar_emitter_active.

Looking for writes to entity fields in range +0x50 to +0xB0 (combat/state fields).
Pattern: mov [bx+offset], value or mov [si+offset], value
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

print("=" * 80)
print("ENTITY FIELD WRITE ANALYSIS")
print("=" * 80)

# Wait for auto-analysis
print("Waiting for auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete\n")

# Track field writes
field_writes = {}  # offset -> list of write locations

# Search .text segment
text_seg = idaapi.get_segm_by_name(".text")
if not text_seg:
    print("ERROR: .text segment not found")
    idc.qexit(1)

print(f"Scanning .text segment: {text_seg.start_ea:#x} - {text_seg.end_ea:#x}")
print("Looking for entity field writes [bx+offset], [si+offset], [di+offset]")
print("Offset range: 0x50 - 0xB0 (combat/state fields)\n")

ea = text_seg.start_ea
total_writes = 0

while ea < text_seg.end_ea:
    insn = idaapi.insn_t()
    insn_len = idaapi.decode_insn(insn, ea)
    
    if insn_len > 0:
        # Look for mov instructions to memory
        if insn.itype == idaapi.NN_mov:
            # Check if destination is [base+disp]
            dst_op = insn.ops[0]
            if dst_op.type == idaapi.o_displ:
                base_reg = dst_op.reg
                offset = dst_op.addr
                
                # Filter: entity-like registers and combat field range
                if base_reg in [idaapi.R_bx, idaapi.R_si, idaapi.R_di]:
                    if 0x50 <= offset <= 0xB0:
                        func_name = idc.get_func_name(ea)
                        disasm = idc.generate_disasm_line(ea, 0)
                        
                        if offset not in field_writes:
                            field_writes[offset] = []
                        
                        field_writes[offset].append({
                            'address': hex(ea),
                            'function': func_name if func_name else 'unknown',
                            'disasm': disasm
                        })
                        total_writes += 1
    
    ea = idc.next_head(ea, text_seg.end_ea)

print(f"Found {total_writes} writes to {len(field_writes)} unique entity fields\n")

# Sort by offset
sorted_offsets = sorted(field_writes.keys())

print("Entity field writes by offset:")
print("=" * 80)

for offset in sorted_offsets:
    writes = field_writes[offset]
    print(f"\nOffset +{offset:#04x} ({offset}d) - {len(writes)} writes:")
    
    # Show first 5 examples
    for i, write in enumerate(writes[:5]):
        func = write['function']
        addr = write['address']
        disasm = write['disasm']
        print(f"  {i+1}. {addr} in {func}:")
        print(f"     {disasm}")
    
    if len(writes) > 5:
        print(f"  ... and {len(writes) - 5} more writes")

# Save results
results = {
    'total_writes': total_writes,
    'unique_fields': len(field_writes),
    'field_writes': {hex(k): v for k, v in field_writes.items()}
}

output_file = Path(__file__).parent / "entity_field_writes.json"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n{'=' * 80}")
print(f"Results saved to: {output_file}")
print("Exiting IDA...")

# Exit
idc.qexit(0)
