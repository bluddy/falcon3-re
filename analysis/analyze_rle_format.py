"""
Manually analyze PICFONT.DAT to reverse-engineer the RLE compression format.

Based on observations:
- Header: 00 04 [width 2B] [height 2B]
- Compressed data follows
- Compression ratio: 1-4% suggests very effective RLE

Expected uncompressed size for first entry:
- Width: 0x0016 = 22 pixels
- Height: 0x01EC = 492 pixels  
- Total: 22 * 492 = 10,824 pixels
- Compressed: 43 - 6 = 37 bytes
- Ratio: 37/10824 = 0.34% (incredibly high compression!)

This suggests the data is mostly one color (background) with sparse foreground pixels.
"""

import struct

def analyze_picfont_dat():
    """Analyze PICFONT.DAT to understand RLE format."""
    
    # Read files
    with open(r'..\game\PICFONT.IDX', 'rb') as f:
        idx_data = f.read()
    
    with open(r'..\game\PICFONT.DAT', 'rb') as f:
        dat_data = f.read()
    
    # Parse index
    num_entries = len(idx_data) // 4
    print(f"Number of entries: {num_entries}")
    print("="*80)
    
    for i in range(num_entries):
        offset = struct.unpack('<H', idx_data[i*4:i*4+2])[0]
        size = struct.unpack('<H', idx_data[i*4+2:i*4+4])[0]
        
        # Extract this entry
        entry_data = dat_data[offset:offset+size]
        
        # Parse header
        if len(entry_data) < 6:
            print(f"Entry {i}: Too small ({len(entry_data)} bytes)")
            continue
        
        marker1, marker2 = entry_data[0], entry_data[1]
        width = struct.unpack('<H', entry_data[2:4])[0]
        height = struct.unpack('<H', entry_data[4:6])[0]
        
        compressed_size = size - 6
        uncompressed_size = width * height
        ratio = (compressed_size / uncompressed_size * 100) if uncompressed_size > 0 else 0
        
        print(f"\nEntry {i}:")
        print(f"  Offset: {offset}, Total size: {size} bytes")
        print(f"  Marker: 0x{marker1:02X} 0x{marker2:02X}")
        print(f"  Dimensions: {width}×{height} pixels")
        print(f"  Uncompressed: {uncompressed_size} pixels")
        print(f"  Compressed: {compressed_size} bytes")
        print(f"  Ratio: {ratio:.2f}%")
        
        # Analyze compressed data
        compressed = entry_data[6:]
        print(f"  First 20 compressed bytes: {' '.join(f'{b:02X}' for b in compressed[:20])}")
        
        # Try to identify RLE pattern
        # Common RLE formats:
        # 1. [count][value] - repeat 'value' 'count' times
        # 2. [value][count] - repeat 'value' 'count' times
        # 3. [control_byte][data...] - MSB indicates run vs literal
        
        if len(compressed) >= 2:
            # Check if it's [count][value] format
            print(f"\n  RLE hypothesis: [count][value]")
            print(f"    Byte 0 (count?): 0x{compressed[0]:02X} = {compressed[0]}")
            print(f"    Byte 1 (value?): 0x{compressed[1]:02X} = {compressed[1]}")
            print(f"    If this is a run of {compressed[0]} pixels of value 0x{compressed[1]:02X}...")
            
            # Check if we can decode the whole thing
            pos = 0
            decoded_count = 0
            operations = []
            
            while pos < len(compressed) and len(operations) < 10:
                if pos + 1 >= len(compressed):
                    break
                
                count = compressed[pos]
                value = compressed[pos+1]
                operations.append(f"[{count}×0x{value:02X}]")
                decoded_count += count
                pos += 2
            
            print(f"    Decoded operations (first 10): {' '.join(operations)}")
            print(f"    Total pixels decoded: {decoded_count} / {uncompressed_size}")
            
            if decoded_count == uncompressed_size:
                print(f"    [OK] PERFECT MATCH! This is likely [count][value] RLE")
            elif abs(decoded_count - uncompressed_size) < 100:
                print(f"    [~] CLOSE MATCH (off by {abs(decoded_count - uncompressed_size)})")
            else:
                print(f"    [X] Mismatch - need different format")

if __name__ == '__main__':
    analyze_picfont_dat()
