"""
Debug RLE decompression to see why MADFONT returns 0 bytes.
"""
from rle_decompress import parse_idx_dat, extract_dat_record, rle_decompress

def debug_decompress(data, max_bytes=100):
    """Debug RLE decompression step by step."""
    print(f"Input data ({len(data)} bytes):")
    print(f"  Hex: {data[:min(50, len(data))].hex()}")
    print(f"  Bytes: {list(data[:min(20, len(data))])}")
    print()
    
    result = []
    pos = 0
    step = 0
    
    while pos < len(data) and step < 20:  # Limit steps for debugging
        if pos >= len(data):
            break
            
        control = data[pos]
        pos += 1
        step += 1
        
        print(f"Step {step}: pos={pos-1}, control=0x{control:02X} ({control})")
        
        if control & 0x80:
            # Run-length
            count = control & 0x7F
            if pos >= len(data):
                print(f"  -> RLE run, count={count}, but NO DATA LEFT")
                break
            value = data[pos]
            pos += 1
            print(f"  -> RLE run: repeat 0x{value:02X} × {count}")
            result.extend([value] * count)
        else:
            # Literal
            count = control & 0x7F
            if count == 0:
                print(f"  -> Literal count=0, END MARKER")
                break
            if pos + count > len(data):
                avail = len(data) - pos
                print(f"  -> Literal: copy {count} bytes, but only {avail} available")
                count = avail
            print(f"  -> Literal: copy {count} bytes")
            result.extend(data[pos:pos+count])
            pos += count
        
        if len(result) > max_bytes:
            print(f"  -> Output limit reached ({max_bytes} bytes)")
            break
    
    print(f"\nTotal steps: {step}")
    print(f"Bytes consumed: {pos} / {len(data)}")
    print(f"Output: {len(result)} bytes")
    if result:
        print(f"Output hex: {bytes(result[:50]).hex()}")
    print()
    
    return bytes(result)

# Test on MADFONT record 0
print("=" * 80)
print("MADFONT Record 0 (should be space character?)")
print("=" * 80)

records = parse_idx_dat('../game/MADFONT.IDX', '../game/MADFONT.DAT')
rec0 = records[0]

ex = extract_dat_record(rec0['data'])
print(f"Header: magic=0x{ex['magic']:04X}, width={ex['width']}, height={ex['height']}")
print(f"Compressed data: {ex['compressed_size']} bytes")
print()

result = debug_decompress(ex['compressed_data'], max_bytes=200)

print("=" * 80)
print("MADFONT Record 5 (should have some pixels)")
print("=" * 80)

rec5 = records[5]
ex5 = extract_dat_record(rec5['data'])
print(f"Header: magic=0x{ex5['magic']:04X}, width={ex5['width']}, height={ex5['height']}")
print(f"Compressed data: {ex5['compressed_size']} bytes")
print()

result5 = debug_decompress(ex5['compressed_data'], max_bytes=200)

print("=" * 80)
print("PICFONT Record 0 (this one DOES decompress)")
print("=" * 80)

records_pic = parse_idx_dat('../game/PICFONT.IDX', '../game/PICFONT.DAT')
rec_pic = records_pic[0]

ex_pic = extract_dat_record(rec_pic['data'])
print(f"Header: magic=0x{ex_pic['magic']:04X}, width={ex_pic['width']}, height={ex_pic['height']}")
print(f"Compressed data: {ex_pic['compressed_size']} bytes")
print()

result_pic = debug_decompress(ex_pic['compressed_data'], max_bytes=300)
