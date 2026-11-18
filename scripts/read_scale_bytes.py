"""
Read scale factor bytes from specific addresses in fixed_vec3_accumulate_a.
"""

import idc
import idaapi
import json
from pathlib import Path

print("=" * 70)
print("READING SCALE FACTOR BYTES")
print("=" * 70)
print()

# Wait for auto-analysis
print("Waiting for auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete\n")

# Addresses from fixed_vec3_accumulate_a disassembly
# These are CS segment offsets referenced in the MUL instructions

# From instruction bytes at these addresses:
# 0x22C97: 2E F7 26 BD 35    mul cs:matrix_scale_x
# 0x22CAC: 2E F7 26 BF 35    mul cs:matrix_scale_y
# 0x22CC1: 2E F7 26 C1 35    mul cs:matrix_scale_z

# The offsets are in little-endian: BD 35 = 0x35BD

scale_x_addr = 0x35BD
scale_y_addr = 0x35BF
scale_z_addr = 0x35C1

div_x_addr = 0x35C3
div_y_addr = 0x35C5
div_z_addr = 0x35C7

print("Reading from CS segment offsets:")
print(f"  scale_x @ 0x{scale_x_addr:04X}")
print(f"  scale_y @ 0x{scale_y_addr:04X}")
print(f"  scale_z @ 0x{scale_z_addr:04X}")
print(f"  div_x @ 0x{div_x_addr:04X}")
print(f"  div_y @ 0x{div_y_addr:04X}")
print(f"  div_z @ 0x{div_z_addr:04X}")
print()

# Read 2-byte words from these addresses
scale_x = idc.get_wide_word(scale_x_addr)
scale_y = idc.get_wide_word(scale_y_addr)
scale_z = idc.get_wide_word(scale_z_addr)

div_x = idc.get_wide_word(div_x_addr)
div_y = idc.get_wide_word(div_y_addr)
div_z = idc.get_wide_word(div_z_addr)

print("Values read:")
print(f"  scale_x = {scale_x:5d} (0x{scale_x:04X})")
print(f"  scale_y = {scale_y:5d} (0x{scale_y:04X})")
print(f"  scale_z = {scale_z:5d} (0x{scale_z:04X})")
print()
print(f"  div_x = {div_x:5d} (0x{div_x:04X})")
print(f"  div_y = {div_y:5d} (0x{div_y:04X})")
print(f"  div_z = {div_z:5d} (0x{div_z:04X})")
print()

# Also try to get the names
print("Symbol names:")
print(f"  0x{scale_x_addr:04X}: {idc.get_name(scale_x_addr)}")
print(f"  0x{scale_y_addr:04X}: {idc.get_name(scale_y_addr)}")
print(f"  0x{scale_z_addr:04X}: {idc.get_name(scale_z_addr)}")
print(f"  0x{div_x_addr:04X}: {idc.get_name(div_x_addr)}")
print(f"  0x{div_y_addr:04X}: {idc.get_name(div_y_addr)}")
print(f"  0x{div_z_addr:04X}: {idc.get_name(div_z_addr)}")
print()

# Save to JSON
result = {
    "scale_x": scale_x,
    "scale_y": scale_y,
    "scale_z": scale_z,
    "div_x": div_x,
    "div_y": div_y,
    "div_z": div_z,
}

output_path = Path(__file__).parent.parent / "temp" / "scale_factors.json"
with open(output_path, 'w') as f:
    json.dump(result, f, indent=2)

print(f"Saved to: {output_path}")
print()
print("=" * 70)

# Exit
idc.qexit(0)
