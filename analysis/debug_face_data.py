"""
Debug the face data format more carefully
"""
import struct

def rle_decompress_debug(data):
    """Decompress RLE with debug output"""
    output = bytearray()
    pos = 0
    
    print("RLE decompression trace:")
    while pos < len(data) and len(output) < 2000:
        flag = data[pos]
        print(f"  [{pos:3d}] flag=0x{flag:02X} ", end='')
        pos += 1
        
        if flag == 0:
            print("STOP")
            break
        
        if flag & 0x80:  # Run
            count = flag & 0x7F
            if pos >= len(data):
                print("ERROR: truncated run")
                break
            value = data[pos]
            pos += 1
            output.extend([value] * count)
            print(f"RUN: {count} × 0x{value:02X} -> total {len(output)} pixels")
        else:  # Literal
            count = flag & 0x7F
            if pos + count > len(data):
                print(f"ERROR: truncated literal (need {count}, have {len(data)-pos})")
                break
            output.extend(data[pos:pos+count])
            pos += count
            print(f"LITERAL: {count} bytes -> total {len(output)} pixels")
        
        if len(output) >= 100:
            break  # Stop after first ~100 pixels for debugging
    
    return bytes(output)

# Read first face
dat = open('../game/people.dat', 'rb').read()

print("="*60)
print("FIRST FACE ANALYSIS")
print("="*60)

# First record: offset 0, size 666
record = dat[0:666]

print(f"\nTotal record size: {len(record)} bytes")
print(f"First 20 bytes (hex): {' '.join(f'{b:02X}' for b in record[:20])}")

# Check header
magic = struct.unpack('<H', record[0:2])[0]
x_coord = struct.unpack('<H', record[2:4])[0]
y_coord = struct.unpack('<H', record[4:6])[0]

print(f"\nHeader:")
print(f"  Magic: 0x{magic:04X}")
print(f"  X coord: {x_coord}")
print(f"  Y coord: {y_coord}")

# Skip header, decompress
compressed = record[6:]
print(f"\nCompressed data: {len(compressed)} bytes")
print(f"First 10 bytes: {' '.join(f'{b:02X}' for b in compressed[:10])}")

print("\n" + "="*60)
pixels = rle_decompress_debug(compressed)
print("="*60)

print(f"\nDecompressed {len(pixels)} pixels")

if len(pixels) > 0:
    # Show pixel statistics
    unique = len(set(pixels))
    print(f"Unique values: {unique}")
    print(f"Min value: {min(pixels)}")
    print(f"Max value: {max(pixels)}")
    
    # Show first 100 pixels
    print(f"\nFirst 100 pixels:")
    for i in range(min(100, len(pixels))):
        if i % 20 == 0:
            print(f"\n[{i:3d}]: ", end='')
        print(f"{pixels[i]:02X} ", end='')
    print()
