"""
Extract first record from BUTTON3 to verify it's uncompressed.
"""
import struct

with open('../game/BUTTON3', 'rb') as f:
    data = f.read()

# Skip header (1 + 1 + 13*2 = 28 bytes)
offset = 28

# Read first record
width = struct.unpack('<H', data[offset:offset+2])[0]
height = struct.unpack('<H', data[offset+2:offset+4])[0]
pixels = data[offset+4:offset+4+width*height]

print(f"Record 0: {width}x{height} = {width*height} pixels")
print(f"Got {len(pixels)} bytes of pixel data")
print(f"\nFirst 16 pixels: {list(pixels[:16])}")
print(f"Min pixel value: {min(pixels)}")
print(f"Max pixel value: {max(pixels)}")
print(f"Unique colors: {len(set(pixels))}")

# Count pixels by value
from collections import Counter
counts = Counter(pixels)
print(f"\nTop 10 most common pixel values:")
for val, count in counts.most_common(10):
    print(f"  Color {val:3}: {count:4} times ({count/len(pixels)*100:5.1f}%)")
