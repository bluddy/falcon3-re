"""Test RLE decompression on PEOPLE.DAT"""
import struct

dat = open('../game/people.dat', 'rb').read()

# First record starts at 0, size 666
record = dat[6:666]  # Skip 6-byte header

print(f"Record size: {len(record)} bytes")
print(f"First 20 bytes: {' '.join(f'{b:02X}' for b in record[:20])}")

# Try to read as the RLE decompressor would
pos = 0

# First 4 bytes should be width, height
if len(record) >= 4:
    width = struct.unpack('<H', record[0:2])[0]
    height = struct.unpack('<H', record[2:4])[0]
    print(f"\nIf first 4 bytes are width/height: {width} x {height}")
    
    # Does this make sense?
    if width > 0 and width <= 320 and height > 0 and height <= 200:
        print("  -> Plausible dimensions!")
        pixels_needed = width * height
        print(f"  -> Would need {pixels_needed} pixels")
    else:
        print("  -> Not plausible dimensions")

# Try interpreting as RLE flags
print("\nFirst 10 bytes as RLE flags:")
for i in range(min(10, len(record))):
    b = record[i]
    if b & 0x80:
        count = b & 0x7F
        print(f"  [{i}] 0x{b:02X}: RUN of {count} bytes")
    else:
        count = b & 0x7F
        print(f"  [{i}] 0x{b:02X}: LITERAL {count} bytes")
