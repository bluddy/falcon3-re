"""
Dump complete PICFONT.DAT to analyze compression format.
"""
import struct

with open('../game/PICFONT.DAT', 'rb') as f:
    data = f.read()

print(f"PICFONT.DAT: {len(data)} bytes\n")

# Parse header
magic = struct.unpack('<H', data[0:2])[0]
width = struct.unpack('<H', data[2:4])[0]
height = struct.unpack('<H', data[4:6])[0]

print(f"Header:")
print(f"  Magic: 0x{magic:04X}")
print(f"  Width: {width}")
print(f"  Height: {height}")
print(f"  Pixels: {width * height}")
print(f"  Compressed data: {len(data) - 6} bytes")
print(f"  Ratio: {(len(data) - 6) / (width * height) * 100:.2f}%")

# Dump all compressed data bytes
compressed = data[6:]
print(f"\nCompressed data ({len(compressed)} bytes):")
print("Offset | Hex                                              | Decimal")
print("-------|--------------------------------------------------|" + "-" * 40)

for i in range(0, len(compressed), 16):
    hex_part = ' '.join(f'{compressed[i+j]:02X}' if i+j < len(compressed) else '  ' for j in range(16))
    dec_part = ' '.join(f'{compressed[i+j]:3}' if i+j < len(compressed) else '   ' for j in range(8))
    print(f"0x{i:04X} | {hex_part} | {dec_part}")

# Look for patterns
print(f"\nByte value distribution:")
from collections import Counter
counts = Counter(compressed)
for val in sorted(counts.keys()):
    print(f"  0x{val:02X} ({val:3}): {counts[val]:2} times")

print(f"\nTotal unique byte values: {len(counts)}")
print(f"Min: 0x{min(compressed):02X} ({min(compressed)})")
print(f"Max: 0x{max(compressed):02X} ({max(compressed)})")
