"""Dump .IDX file structure"""
import sys
import struct

filepath = sys.argv[1] if len(sys.argv) > 1 else '../game/PICFONT.IDX'

with open(filepath, 'rb') as f:
    data = f.read()

print(f"{filepath}: {len(data)} bytes\n")
print("All bytes (hex):")
print(' '.join(f'{b:02X}' for b in data))

print("\n\nAs 16-bit words (little-endian):")
for i in range(0, len(data), 2):
    if i + 2 <= len(data):
        word = struct.unpack('<H', data[i:i+2])[0]
        print(f"  Word {i//2:2}: 0x{word:04X} ({word:5})")
