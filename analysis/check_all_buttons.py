"""
Check if BUTTON1/2/3 are compressed or uncompressed.
"""
import struct

def analyze_button(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    count = data[0]
    pad = data[1]
    
    print(f"\n=== {filepath} ===")
    print(f"File size: {len(data)} bytes")
    print(f"Count: {count}, Pad: 0x{pad:02X}")
    
    # Read size table
    sizes = []
    for i in range(count):
        pos = 2 + i * 2
        size = struct.unpack('<H', data[pos:pos+2])[0]
        sizes.append(size)
    
    header_size = 2 + count * 2
    expected_size = header_size + sum(sizes)
    
    print(f"Header size: {header_size} bytes")
    print(f"Sum of record sizes: {sum(sizes)} bytes")
    print(f"Expected total: {expected_size} bytes")
    print(f"Actual total: {len(data)} bytes")
    print(f"Match: {expected_size == len(data)}")
    
    # Check if records are compressed
    offset = header_size
    compressed_count = 0
    uncompressed_count = 0
    
    print(f"\nSample records:")
    for i in range(min(5, count)):
        if offset + 4 > len(data):
            break
        
        width = struct.unpack('<H', data[offset:offset+2])[0]
        height = struct.unpack('<H', data[offset+2:offset+4])[0]
        pixels = width * height
        data_size = sizes[i] - 4
        
        ratio = (data_size / pixels * 100) if pixels > 0 else 0
        
        if ratio < 95:
            status = "COMPRESSED"
            compressed_count += 1
        elif ratio > 105:
            status = "ERROR"
        else:
            status = "uncompressed"
            uncompressed_count += 1
        
        print(f"  Rec {i}: {width:4}x{height:4} = {pixels:6} px, {data_size:5} bytes ({ratio:6.1f}%) {status}")
        
        offset += sizes[i]
    
    print(f"\nConclusion: ", end='')
    if compressed_count > 0 and uncompressed_count == 0:
        print("ALL COMPRESSED")
    elif uncompressed_count > 0 and compressed_count == 0:
        print("ALL UNCOMPRESSED")
    else:
        print(f"MIXED ({compressed_count} compressed, {uncompressed_count} uncompressed)")

for button in ['BUTTON1', 'BUTTON2', 'BUTTON3']:
    analyze_button(f'../game/{button}')
