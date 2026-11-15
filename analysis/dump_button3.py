"""
Dump BUTTON3 structure in detail since it's smallest.
"""
import struct

with open('../game/BUTTON3', 'rb') as f:
    data = f.read()

print(f"BUTTON3: {len(data)} bytes\n")
print("First 256 bytes (hex):")
for i in range(0, min(256, len(data)), 16):
    hex_part = ' '.join(f'{data[i+j]:02X}' if i+j < len(data) else '  ' for j in range(16))
    ascii_part = ''.join(chr(data[i+j]) if 32 <= data[i+j] < 127 and i+j < len(data) else '.' for j in range(16))
    print(f"{i:04X}: {hex_part}  {ascii_part}")

print("\n\nTrying to parse as: count (1B), pad (1B), then offset table (2B each):")
count = data[0]
pad = data[1]
print(f"Count: {count}, Pad: 0x{pad:02X}")

print(f"\nOffset table ({count} entries, 2 bytes each):")
for i in range(count):
    offset_pos = 2 + i * 2
    if offset_pos + 2 <= len(data):
        offset = struct.unpack('<H', data[offset_pos:offset_pos+2])[0]
        print(f"  Entry {i:2}: offset 0x{offset:04X} ({offset})")
        
        # Check if this looks like a valid offset
        if offset < len(data):
            # Try to read dimensions at this offset
            if offset + 4 <= len(data):
                w = struct.unpack('<H', data[offset:offset+2])[0]
                h = struct.unpack('<H', data[offset+2:offset+4])[0]
                if 1 < w < 500 and 1 < h < 500:
                    print(f"          -> Possible dimensions: {w}x{h} = {w*h} pixels")
