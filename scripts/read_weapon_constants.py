"""
Read weapon hash constants directly from memory addresses.
Based on the disassembly of fixed_vec3_accumulate_a @ 0x22C91.
"""

import idc
import idaapi
import json
from pathlib import Path

print("=" * 70)
print("READING WEAPON HASH CONSTANTS FROM MEMORY")
print("=" * 70)
print()

# Wait for auto-analysis - REQUIRED
print("Waiting for auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete\n")

# Based on disassembly at 0x22C91-0x22CD5
# These are the offsets within the code segment that MUL/DIV reference

# From the disassembly, we know the instruction bytes contain these offsets:
# 0x22C97: 2E F7 26 BD 35    mul cs:matrix_scale_x
# The offset BD 35 = 0x35BD in little endian

# 0x22C9C: 2E F7 36 C3 35    div cs:fixedpoint_divisor_x  
# The offset C3 35 = 0x35C3

# 0x22CAC: 2E F7 26 BF 35    mul cs:matrix_scale_y
# The offset BF 35 = 0x35BF

# 0x22CB1: 2E F7 36 C5 35    div cs:fixedpoint_divisor_y
# The offset C5 35 = 0x35C5

# 0x22CC1: 2E F7 26 C1 35    mul cs:matrix_scale_z
# The offset C1 35 = 0x35C1

# 0x22CC6: 2E F7 36 C7 35    div cs:fixedpoint_divisor_z
# The offset C7 35 = 0x35C7

# Read the instruction bytes to extract the offsets
addr = 0x22C97
bytes_mul_x = idc.get_bytes(addr, 5)
offset_scale_x = (bytes_mul_x[3] | (bytes_mul_x[4] << 8))

addr = 0x22C9C
bytes_div_x = idc.get_bytes(addr, 5)
offset_div_x = (bytes_div_x[3] | (bytes_div_x[4] << 8))

addr = 0x22CAC
bytes_mul_y = idc.get_bytes(addr, 5)
offset_scale_y = (bytes_mul_y[3] | (bytes_mul_y[4] << 8))

addr = 0x22CB1
bytes_div_y = idc.get_bytes(addr, 5)
offset_div_y = (bytes_div_y[3] | (bytes_div_y[4] << 8))

addr = 0x22CC1
bytes_mul_z = idc.get_bytes(addr, 5)
offset_scale_z = (bytes_mul_z[3] | (bytes_mul_z[4] << 8))

addr = 0x22CC6
bytes_div_z = idc.get_bytes(addr, 5)
offset_div_z = (bytes_div_z[3] | (bytes_div_z[4] << 8))

print("Extracted offsets from instruction bytes:")
print(f"  scale_x offset: 0x{offset_scale_x:04X}")
print(f"  div_x offset:   0x{offset_div_x:04X}")
print(f"  scale_y offset: 0x{offset_scale_y:04X}")
print(f"  div_y offset:   0x{offset_div_y:04X}")
print(f"  scale_z offset: 0x{offset_scale_z:04X}")
print(f"  div_z offset:   0x{offset_div_z:04X}")
print()

# Now read the values from these CS segment offsets
# The CS segment contains the code, so we need to read from the code segment
scale_x = idc.get_wide_word(offset_scale_x)
div_x = idc.get_wide_word(offset_div_x)
scale_y = idc.get_wide_word(offset_scale_y)
div_y = idc.get_wide_word(offset_div_y)
scale_z = idc.get_wide_word(offset_scale_z)
div_z = idc.get_wide_word(offset_div_z)

print("=" * 70)
print("CONSTANTS READ FROM MEMORY")
print("=" * 70)
print()

print(f"Scale factors:")
print(f"  X: {scale_x:5d} (0x{scale_x:04X})")
print(f"  Y: {scale_y:5d} (0x{scale_y:04X})")
print(f"  Z: {scale_z:5d} (0x{scale_z:04X})")
print()

print(f"Divisors:")
print(f"  X: {div_x:5d} (0x{div_x:04X})")
print(f"  Y: {div_y:5d} (0x{div_y:04X})")
print(f"  Z: {div_z:5d} (0x{div_z:04X})")
print()

print("=" * 70)
print("HASH FORMULA")
print("=" * 70)
print()
print(f"category = (field_06 * {scale_x} / {div_x}) +")
print(f"           (field_08 * {scale_y} / {div_y}) +")
print(f"           (field_0A * {scale_z} / {div_z})")
print()

# Also display the named symbols
print("Named symbols:")
print(f"  cs:0x{offset_scale_x:04X} = {idc.get_name(offset_scale_x)}")
print(f"  cs:0x{offset_div_x:04X} = {idc.get_name(offset_div_x)}")
print(f"  cs:0x{offset_scale_y:04X} = {idc.get_name(offset_scale_y)}")
print(f"  cs:0x{offset_div_y:04X} = {idc.get_name(offset_div_y)}")
print(f"  cs:0x{offset_scale_z:04X} = {idc.get_name(offset_scale_z)}")
print(f"  cs:0x{offset_div_z:04X} = {idc.get_name(offset_div_z)}")
print()

# Save results to JSON
constants = {
    'scale_x': scale_x,
    'scale_y': scale_y,
    'scale_z': scale_z,
    'div_x': div_x,
    'div_y': div_y,
    'div_z': div_z,
}

output_path = Path(__file__).parent.parent / "temp" / "weapon_hash_constants.json"
with open(output_path, 'w') as f:
    json.dump(constants, f, indent=2)

print(f"Results saved to: {output_path}")
print()
print("=" * 70)
print("Done! Constants read successfully.")
print("=" * 70)

# CRITICAL: Exit explicitly or script hangs forever!
idc.qexit(0)
