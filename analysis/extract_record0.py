"""Extract first record from PICFONT.DAT"""
import struct

with open('../game/PICFONT.DAT', 'rb') as f:
    dat = f.read()

with open('../game/PICFONT.IDX', 'rb') as f:
    idx = f.read()

# Parse first record from IDX
offset = struct.unpack('<H', idx[0:2])[0]
size = struct.unpack('<H', idx[2:4])[0]

print(f"Record 0: offset={offset}, size={size}")

# Extract record
record = dat[offset:offset+size]

print(f"Extracted {len(record)} bytes\n")

# Parse header
magic = struct.unpack('<H', record[0:2])[0]
width = struct.unpack('<H', record[2:4])[0]
height = struct.unpack('<H', record[4:6])[0]
compressed = record[6:]

print(f"Header:")
print(f"  Magic: 0x{magic:04X}")
print(f"  Width: {width}")
print(f"  Height: {height}")
print(f"  Pixels: {width * height}")
print(f"  Compressed: {len(compressed)} bytes")
print(f"  Ratio: {len(compressed) / (width * height) * 100:.2f}%")

print(f"\nCompressed data:")
print(' '.join(f'{b:02X}' for b in compressed))
