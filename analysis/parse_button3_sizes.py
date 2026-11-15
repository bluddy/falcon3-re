"""
Parse BUTTON3 assuming: count, pad, then SIZE table.
"""
import struct

with open('../game/BUTTON3', 'rb') as f:
    data = f.read()

count = data[0]
pad = data[1]

print(f"BUTTON3: {len(data)} bytes")
print(f"Count: {count}, Pad: 0x{pad:02X}\n")

# Read size table
sizes = []
for i in range(count):
    pos = 2 + i * 2
    size = struct.unpack('<H', data[pos:pos+2])[0]
    sizes.append(size)

print("Size table:")
for i, size in enumerate(sizes):
    print(f"  Record {i:2}: {size:5} bytes")

print(f"\nTotal from size table: {sum(sizes)} bytes")
print(f"Header size: {2 + count * 2} bytes")
print(f"Expected file size: {2 + count * 2 + sum(sizes)} = {len(data)} bytes")
print(f"Match: {2 + count * 2 + sum(sizes) == len(data)}")

# Now parse each record
header_size = 2 + count * 2
offset = header_size
print(f"\n\nRecords (starting at offset 0x{offset:04X}):")
print(f"{'#':<4} {'Width':<7} {'Height':<7} {'Pixels':<8} {'DataSize':<10} {'Ratio':<8} {'Offset':<8}")
print("-" * 70)

for i, size in enumerate(sizes):
    # Each record: width (2B), height (2B), then compressed data
    if offset + 4 > len(data):
        print(f"ERROR: Not enough data for record {i}")
        break
    
    width = struct.unpack('<H', data[offset:offset+2])[0]
    height = struct.unpack('<H', data[offset+2:offset+4])[0]
    
    pixels = width * height
    data_size = size - 4  # Size includes the width/height fields
    ratio = (data_size / pixels * 100) if pixels > 0 else 0
    
    print(f"{i:<4} {width:<7} {height:<7} {pixels:<8} {data_size:<10} {ratio:>6.2f}%  0x{offset:06X}")
    
    offset += size

print(f"\nTotal bytes: {offset}")
