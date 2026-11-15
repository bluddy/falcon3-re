"""
Parse BUTTON file records to find dimensions and compressed data sizes.
"""
import struct

def parse_button_file(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"=== {filepath} ===")
    print(f"File size: {len(data)} bytes\n")
    
    # Parse header
    count = data[0]
    magic = struct.unpack('<H', data[1:3])[0]
    
    print(f"Header: count={count}, magic=0x{magic:04X}")
    
    if magic != 0x0400:
        print(f"ERROR: Unexpected magic 0x{magic:04X} (expected 0x0400)")
        return
    
    # Parse records
    offset = 3
    records = []
    
    print(f"\nRecords:")
    print(f"{'#':<4} {'Width':<7} {'Height':<7} {'Pixels':<8} {'DataSize':<10} {'Ratio':<8} {'Offset':<8}")
    print("-" * 70)
    
    for i in range(count):
        if offset + 2 > len(data):
            print(f"ERROR: Not enough data for record {i} dimensions")
            break
        
        # Read dimensions (assuming 2 bytes each like .DAT format)
        width = struct.unpack('<H', data[offset:offset+2])[0]
        offset += 2
        
        if offset + 2 > len(data):
            print(f"ERROR: Not enough data for record {i} height")
            break
            
        height = struct.unpack('<H', data[offset:offset+2])[0]
        offset += 2
        
        pixels = width * height
        
        # Find next record or end of file to determine data size
        if i + 1 < count:
            # Estimate: peek ahead to find next dimensions
            # This is tricky - we need to find where the next record starts
            # For now, let's assume the data immediately follows
            # We'll refine this by looking for reasonable dimension values
            
            # Search forward for next plausible dimension pair
            next_offset = offset
            found_next = False
            
            for search_offset in range(offset, min(offset + 10000, len(data) - 4)):
                test_w = struct.unpack('<H', data[search_offset:search_offset+2])[0]
                test_h = struct.unpack('<H', data[search_offset+2:search_offset+4])[0]
                
                # Plausible if dimensions are reasonable (10-2000) and product gives decent compression
                if 10 < test_w < 2000 and 10 < test_h < 2000:
                    test_pixels = test_w * test_h
                    # Look further ahead for another plausible dimension or end
                    data_size = search_offset - offset
                    if data_size > 0 and data_size < test_pixels:  # Must have compression
                        next_offset = search_offset
                        found_next = True
                        break
            
            if not found_next:
                # Last record
                data_size = len(data) - offset
            else:
                data_size = next_offset - offset
        else:
            # Last record
            data_size = len(data) - offset
        
        ratio = (data_size / pixels * 100) if pixels > 0 else 0
        
        records.append({
            'index': i,
            'width': width,
            'height': height,
            'pixels': pixels,
            'data_size': data_size,
            'offset': offset
        })
        
        print(f"{i:<4} {width:<7} {height:<7} {pixels:<8} {data_size:<10} {ratio:>6.2f}%  0x{offset:06X}")
        
        offset += data_size
    
    print(f"\nTotal records: {len(records)}")
    print(f"Bytes parsed: {offset} / {len(data)}")
    
    # Show first record's data for inspection
    if records:
        rec = records[0]
        print(f"\nFirst record data (first 64 bytes):")
        start = rec['offset']
        end = min(start + 64, len(data))
        hex_data = ' '.join(f'{b:02X}' for b in data[start:end])
        print(f"  {hex_data}")
    
    return records

# Parse all BUTTON files
for i in [1, 2, 3]:
    records = parse_button_file(f'../game/BUTTON{i}')
    print("\n" + "=" * 70 + "\n")
