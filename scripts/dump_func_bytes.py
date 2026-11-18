"""
Dump raw bytes from fixed_vec3_accumulate_a function.
"""

import idc
import idaapi
from pathlib import Path

print("=" * 70)
print("DUMPING FUNCTION BYTES")
print("=" * 70)
print()

# Wait for auto-analysis
idaapi.auto_wait()

# Function address and size
func_addr = 0x22C91
func_size = 68

print(f"Function: 0x{func_addr:X}, size: {func_size} bytes")
print()

# Read all bytes
func_bytes = idc.get_bytes(func_addr, func_size)

# Print hex dump
print("Hex dump:")
print("-" * 70)
for i in range(0, len(func_bytes), 16):
    addr = func_addr + i
    chunk = func_bytes[i:i+16]
    hex_str = ' '.join(f'{b:02X}' for b in chunk)
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
    print(f"0x{addr:05X}: {hex_str:48s} {ascii_str}")

print()

# Save to file
output_path = Path(__file__).parent.parent / "temp" / "func_bytes.bin"
with open(output_path, 'wb') as f:
    f.write(func_bytes)

print(f"Saved to: {output_path}")
print()

# Now specifically look at the MUL/DIV instructions
print("MUL/DIV instruction analysis:")
print("-" * 70)

# X component: mul @ 0x22C97
addr = 0x22C97
insn_bytes = idc.get_bytes(addr, 5)
cs_offset = insn_bytes[3] | (insn_bytes[4] << 8)
print(f"0x{addr:X} MUL: bytes={' '.join(f'{b:02X}' for b in insn_bytes)}, CS offset=0x{cs_offset:04X}")

# X div @ 0x22C9C
addr = 0x22C9C
insn_bytes = idc.get_bytes(addr, 5)
cs_offset = insn_bytes[3] | (insn_bytes[4] << 8)
print(f"0x{addr:X} DIV: bytes={' '.join(f'{b:02X}' for b in insn_bytes)}, CS offset=0x{cs_offset:04X}")

# Y component: mul @ 0x22CAC
addr = 0x22CAC
insn_bytes = idc.get_bytes(addr, 5)
cs_offset = insn_bytes[3] | (insn_bytes[4] << 8)
print(f"0x{addr:X} MUL: bytes={' '.join(f'{b:02X}' for b in insn_bytes)}, CS offset=0x{cs_offset:04X}")

# Y div @ 0x22CB1
addr = 0x22CB1
insn_bytes = idc.get_bytes(addr, 5)
cs_offset = insn_bytes[3] | (insn_bytes[4] << 8)
print(f"0x{addr:X} DIV: bytes={' '.join(f'{b:02X}' for b in insn_bytes)}, CS offset=0x{cs_offset:04X}")

# Z component: mul @ 0x22CC1
addr = 0x22CC1
insn_bytes = idc.get_bytes(addr, 5)
cs_offset = insn_bytes[3] | (insn_bytes[4] << 8)
print(f"0x{addr:X} MUL: bytes={' '.join(f'{b:02X}' for b in insn_bytes)}, CS offset=0x{cs_offset:04X}")

# Z div @ 0x22CC6
addr = 0x22CC6
insn_bytes = idc.get_bytes(addr, 5)
cs_offset = insn_bytes[3] | (insn_bytes[4] << 8)
print(f"0x{addr:X} DIV: bytes={' '.join(f'{b:02X}' for b in insn_bytes)}, CS offset=0x{cs_offset:04X}")

print()
print("=" * 70)

idc.qexit(0)
