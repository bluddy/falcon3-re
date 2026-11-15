"""
Analyze SYSMENU.DAT structure - War Room graphics.
Check if it uses same compressed format as fonts.
"""
import struct

def analyze_dat_file(idx_path, dat_path):
    # Read index
    with open(idx_path, 'rb') as f:
        idx_data = f.read()
    
    # Read data
    with open(dat_path, 'rb') as f:
        dat_data = f.read()
    
    # Parse index entries
    num_entries = len(idx_data) // 4
    entries = []
    for i in range(num_entries):
        offset = struct.unpack('<H', idx_data[i*4:i*4+2])[0]
        size = struct.unpack('<H', idx_data[i*4+2:i*4+4])[0]
        entries.append((offset, size))
    
    print(f"=== {idx_path} / {dat_path} ===")
    print(f"DAT size: {len(dat_data)} bytes")
    print(f"IDX size: {len(idx_data)} bytes")
    print(f"Number of records: {num_entries}")
    print()
    
    # Analyze first 10 records
    print(f"First 10 records:")
    print(f"{'#':<4} {'Offset':<8} {'Size':<6} {'Magic':<7} {'Width':<7} {'Height':<7} {'Pixels':<9} {'Ratio':<8}")
    print("-" * 80)
    
    for i in range(min(10, num_entries)):
        offset, size = entries[i]
        
        if offset + size > len(dat_data):
            print(f"{i:<4} {offset:<8} {size:<6} ERROR: beyond file size")
            continue
        
        record = dat_data[offset:offset+size]
        
        # Try to parse as compressed graphics
        if len(record) >= 6:
            magic = struct.unpack('<H', record[0:2])[0]
            width = struct.unpack('<H', record[2:4])[0]
            height = struct.unpack('<H', record[4:6])[0]
            
            if magic == 0x0400 and 1 <= width <= 1000 and 1 <= height <= 1000:
                # Looks like compressed graphics
                pixels = width * height
                compressed_size = size - 6
                ratio = (compressed_size / pixels * 100) if pixels > 0 else 0
                print(f"{i:<4} {offset:<8} {size:<6} 0x{magic:04X}  {width:<7} {height:<7} {pixels:<9} {ratio:>6.2f}%")
            else:
                # Not graphics or wrong format
                print(f"{i:<4} {offset:<8} {size:<6} 0x{magic:04X}  ???")
        else:
            print(f"{i:<4} {offset:<8} {size:<6} (too small)")
    
    # Summary statistics
    compressed_count = 0
    uncompressed_count = 0
    other_count = 0
    
    for i, (offset, size) in enumerate(entries):
        if offset + size > len(dat_data):
            continue
        
        record = dat_data[offset:offset+size]
        if len(record) >= 6:
            magic = struct.unpack('<H', record[0:2])[0]
            
            if magic == 0x0400:
                width = struct.unpack('<H', record[2:4])[0]
                height = struct.unpack('<H', record[4:6])[0]
                
                if 1 <= width <= 1000 and 1 <= height <= 1000:
                    pixels = width * height
                    compressed_size = size - 6
                    ratio = (compressed_size / pixels * 100) if pixels > 0 else 0
                    
                    if ratio < 90:
                        compressed_count += 1
                    elif ratio < 110:
                        uncompressed_count += 1
                    else:
                        other_count += 1
                else:
                    other_count += 1
            else:
                other_count += 1
        else:
            other_count += 1
    
    print(f"\nSummary:")
    print(f"  Compressed graphics: {compressed_count}")
    print(f"  Uncompressed graphics: {uncompressed_count}")
    print(f"  Other/unknown: {other_count}")
    print()

# Analyze SYSMENU files
analyze_dat_file('../game/SYSMENU.IDX', '../game/SYSMENU.DAT')

# Also analyze PICFONT for comparison
print("\n" + "=" * 80 + "\n")
analyze_dat_file('../game/PICFONT.IDX', '../game/PICFONT.DAT')
