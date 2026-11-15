"""Test RLE decompression with assumed dimensions"""
import struct

def rle_decompress_all(data):
    """Decompress all RLE data - no pixel limit"""
    output = bytearray()
    pos = 0
    
    while pos < len(data):
        flag = data[pos]
        pos += 1
        
        if flag == 0:  # Stop marker?
            break
        
        if flag & 0x80:  # Run
            count = flag & 0x7F
            if pos >= len(data):
                break
            value = data[pos]
            pos += 1
            output.extend([value] * count)
        else:  # Literal
            count = flag & 0x7F
            if pos + count > len(data):
                break
            output.extend(data[pos:pos+count])
            pos += count
    
    return bytes(output), pos

dat = open('../game/people.dat', 'rb').read()

# First record starts at 0, size 666
record = dat[6:666]  # Skip 6-byte header

print(f"Record size: {len(record)} bytes\n")

# Try various dimensions
# First try decompressing all data
print("Decompressing entire record...")
all_pixels, bytes_used = rle_decompress_all(record)
print(f"  Total pixels: {len(all_pixels)}, used {bytes_used}/{len(record)} bytes\n")

# Try to find dimensions that match
for divisor in range(10, 200):
    if len(all_pixels) % divisor == 0:
        other = len(all_pixels) // divisor
        if other <= 200:
            print(f"  Possible dims: {divisor} x {other} = {len(all_pixels)}")

print()

# Try various dimensions
def rle_decompress_simple(data, expected_pixels):
    """Simple RLE decompressor - no width/height in stream"""
    output = bytearray()
    pos = 0
    
    while len(output) < expected_pixels and pos < len(data):
        flag = data[pos]
        pos += 1
        
        if flag == 0:  # Stop marker?
            break
        
        if flag & 0x80:  # Run
            count = flag & 0x7F
            if pos >= len(data):
                break
            value = data[pos]
            pos += 1
            output.extend([value] * count)
        else:  # Literal
            count = flag & 0x7F
            if pos + count > len(data):
                break
            output.extend(data[pos:pos+count])
            pos += count
    
    return bytes(output), pos

test_dims = [
    (32, 20),  # 640 pixels
    (40, 16),  # 640 pixels
    (64, 10),  # 640 pixels
    (32, 32),  # 1024 pixels
    (40, 40),  # 1600 pixels
    (64, 64),  # 4096 pixels
]

for width, height in test_dims:
    pixels_needed = width * height
    output, bytes_used = rle_decompress_simple(record, pixels_needed)
    
    print(f"Trying {width}x{height} ({pixels_needed} pixels):")
    print(f"  Decompressed: {len(output)} pixels, used {bytes_used}/{len(record)} bytes")
    
    if len(output) == pixels_needed:
        print(f"  OK Perfect match!")
        
        # Check if output looks reasonable (not all zeros, has variety)
        unique_values = len(set(output))
        zero_count = output.count(0)
        print(f"  Unique values: {unique_values}, zeros: {zero_count}")
        
        # Save it
        with open(f'test_face_{width}x{height}.raw', 'wb') as f:
            f.write(output)
        print(f"  Saved as test_face_{width}x{height}.raw")
    elif len(output) < pixels_needed:
        print(f"  X Not enough data (short by {pixels_needed - len(output)} pixels)")
    print()
