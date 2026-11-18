"""
Decode CALL instruction bytes to understand the actual target.
"""

import idc
import idaapi
from pathlib import Path

print("=" * 70)
print("DECODING CALL INSTRUCTION BYTES")
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
    # Get the instruction bytes
    insn_len = idc.get_item_size(call_addr)
    insn_bytes = idc.get_bytes(call_addr, insn_len)
    hex_bytes = ' '.join(f'{b:02X}' for b in insn_bytes)
    
    # Get disassembly
    disasm = idc.GetDisasm(call_addr)
    
    line = f"0x{call_addr:05X}: {disasm}"
    print(line)
    output_lines.append(line)
    
    line = f"  Bytes: {hex_bytes} (length={insn_len})"
    print(line)
    output_lines.append(line)
    
    # Decode based on instruction type
    if insn_bytes[0] == 0xE8:  # NEAR call (relative)
        # E8 XX XX - near call, relative offset
        offset = insn_bytes[1] | (insn_bytes[2] << 8)
        # Sign extend if negative
        if offset >= 0x8000:
            offset = offset - 0x10000
        
        target = call_addr + insn_len + offset
        line = f"  Type: NEAR CALL (relative)"
        print(line)
        output_lines.append(line)
        
        line = f"  Relative offset: {offset} (0x{offset & 0xFFFF:04X})"
        print(line)
        output_lines.append(line)
        
        line = f"  Calculated target: 0x{target:05X}"
        print(line)
        output_lines.append(line)
        
    elif insn_bytes[0] == 0x9A:  # FAR call (absolute)
        # 9A XX XX YY YY - far call, segment:offset
        offset = insn_bytes[1] | (insn_bytes[2] << 8)
        segment = insn_bytes[3] | (insn_bytes[4] << 8)
        line = f"  Type: FAR CALL (absolute)"
        print(line)
        output_lines.append(line)
        
        line = f"  Segment:Offset: 0x{segment:04X}:0x{offset:04X}"
        print(line)
        output_lines.append(line)
        
    else:
        line = f"  Type: Unknown or indirect call (opcode=0x{insn_bytes[0]:02X})"
        print(line)
        output_lines.append(line)
    
    print()
    output_lines.append("")

output_path = Path(__file__).parent.parent / "temp" / "call_instruction_bytes.txt"
with open(output_path, 'w') as f:
    f.write('\n'.join(output_lines))

print(f"Saved to: {output_path}")
print("=" * 70)

idc.qexit(0)
