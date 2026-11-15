"""
Implement the RLE decompressor found at 0x88460.
Based on the disassembly analysis in RLE_DECOMPRESSOR_FOUND.md

Algorithm: Classic flag-byte RLE
- Control byte bit 7 = 1: Run-length (count in bits 0-6, next byte = value)
- Control byte bit 7 = 0: Literal (count in bits 0-6, next N bytes = data)
"""

def rle_decompress(compressed_data):
    """
    Decompress RLE data using the algorithm from 0x88460.
    
    Args:
        compressed_data: bytes object containing compressed data
        
    Returns:
        bytes object containing decompressed data
    """
    result = []
    pos = 0
    
    while pos < len(compressed_data):
        # Read control byte
        control = compressed_data[pos]
        pos += 1
        
        if control & 0x80:
            # Run-length: repeat next byte
            count = control & 0x7F
            if pos >= len(compressed_data):
                break
            value = compressed_data[pos]
            pos += 1
            result.extend([value] * count)
        else:
            # Literal: copy next N bytes
            count = control & 0x7F
            if count == 0:
                break  # End marker?
            if pos + count > len(compressed_data):
                count = len(compressed_data) - pos
            result.extend(compressed_data[pos:pos+count])
            pos += count
    
    return bytes(result)


def parse_idx_dat(idx_path, dat_path):
    """
    Parse .IDX and .DAT file pair.
    
    Returns:
        List of records, each containing:
        - offset: position in .DAT file
        - size: size of compressed data
        - data: raw compressed bytes
    """
    with open(idx_path, 'rb') as f:
        idx_data = f.read()
    
    with open(dat_path, 'rb') as f:
        dat_data = f.read()
    
    # Parse index entries (2-byte offset + 2-byte size)
    import struct
    num_entries = len(idx_data) // 4
    
    records = []
    for i in range(num_entries):
        pos = i * 4
        offset, size = struct.unpack('<HH', idx_data[pos:pos+4])
        
        if offset + size <= len(dat_data):
            record_data = dat_data[offset:offset+size]
            records.append({
                'index': i,
                'offset': offset,
                'size': size,
                'data': record_data
            })
    
    return records


def extract_dat_record(record_data):
    """
    Extract a single .DAT record.
    
    .DAT format (from MENU_DATA_FORMAT_SPEC.md):
    - Bytes 0-1: 0x00 0x04 (format marker)
    - Bytes 2-3: Width (word, little-endian)
    - Bytes 4-5: Height (word, little-endian)
    - Bytes 6+: Compressed data
    
    Returns:
        dict with 'magic', 'width', 'height', 'compressed_data', 'decompressed'
    """
    import struct
    
    if len(record_data) < 6:
        return None
    
    magic = struct.unpack('<H', record_data[0:2])[0]
    width = struct.unpack('<H', record_data[2:4])[0]
    height = struct.unpack('<H', record_data[4:6])[0]
    compressed = record_data[6:]
    
    # Try to decompress
    try:
        decompressed = rle_decompress(compressed)
    except Exception as e:
        decompressed = None
    
    return {
        'magic': magic,
        'width': width,
        'height': height,
        'compressed_data': compressed,
        'decompressed': decompressed,
        'compressed_size': len(compressed),
        'decompressed_size': len(decompressed) if decompressed else 0
    }


def test_decompression():
    """Test RLE decompression on a simple example."""
    # Create test data
    # 0x85 0x41 = run of 5 'A's
    # 0x03 0x42 0x43 0x44 = literal "BCD"
    test_data = bytes([0x85, 0x41, 0x03, 0x42, 0x43, 0x44])
    
    result = rle_decompress(test_data)
    expected = b'AAAAABCD'
    
    print("RLE Decompression Test:")
    print(f"Input:    {test_data.hex()}")
    print(f"Output:   {result}")
    print(f"Expected: {expected}")
    print(f"Match: {result == expected}")
    print()


if __name__ == '__main__':
    test_decompression()
    
    # Try on SYSMENU
    print("Testing on SYSMENU.IDX/.DAT...")
    print("=" * 70)
    
    records = parse_idx_dat('../game/SYSMENU.IDX', '../game/SYSMENU.DAT')
    print(f"Found {len(records)} records")
    print()
    
    # Analyze first few records
    for i in range(min(5, len(records))):
        print(f"Record {i}:")
        extracted = extract_dat_record(records[i]['data'])
        if extracted:
            print(f"  Magic: 0x{extracted['magic']:04X}")
            print(f"  Dimensions: {extracted['width']}x{extracted['height']}")
            print(f"  Compressed: {extracted['compressed_size']} bytes")
            print(f"  Decompressed: {extracted['decompressed_size']} bytes")
            
            expected_pixels = extracted['width'] * extracted['height']
            if extracted['decompressed_size'] > 0:
                ratio = extracted['decompressed_size'] / expected_pixels
                print(f"  Expected pixels: {expected_pixels}")
                print(f"  Ratio: {ratio:.4f} (1.0 = exact match)")
            print()
