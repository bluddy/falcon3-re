"""
Test 2: Maybe the entire chunk IS the sprite data, no header.
The RLE decompressor expects [width][height][rle_data].
The 0x0400 magic might just be coincidence or part of RLE data.
"""

def parse_idx(idx_path):
    with open(idx_path, 'rb') as f:
        data = f.read()
    
    entries = []
    i = 0
    while i + 4 <= len(data):
        offset = int.from_bytes(data[i:i+2], 'little')
        size = int.from_bytes(data[i+2:i+4], 'little')
        entries.append((offset, size))
        i += 4
    
    return entries

def test_as_raw_sprite(data, offset, size):
    """Test if chunk starts directly with width/height."""
    chunk = data[offset:offset+size]
    
    print(f"\n=== Sprite {offset} (0x{offset:04X}), size {size} ===")
    
    # Try interpreting first 2 words as width/height
    if len(chunk) >= 4:
        width = int.from_bytes(chunk[0:2], 'little')
        height = int.from_bytes(chunk[2:4], 'little')
        
        print(f"If no header - Width: {width}, Height: {height}")
        
        # Sanity check dimensions
        if width > 0 and width < 320 and height > 0 and height < 200:
            print(f"  -> Reasonable VGA dimensions!")
            print(f"  -> RLE data starts at offset 4, size {size-4} bytes")
            
            # Show first few RLE bytes
            if len(chunk) >= 12:
                print(f"\n  First RLE bytes:")
                for i in range(4, min(12, len(chunk))):
                    byte = chunk[i]
                    if byte & 0x80:
                        print(f"    [{i}] 0x{byte:02X} - RUN: count={byte & 0x7F}")
                    else:
                        print(f"    [{i}] 0x{byte:02X} - LITERAL: count={byte}")
        else:
            print(f"  -> Dimensions seem unreasonable for VGA")
            
            # Maybe there's a small header?
            print(f"\n  Trying offset 2 (skip 1 word):")
            if len(chunk) >= 6:
                width2 = int.from_bytes(chunk[2:4], 'little')
                height2 = int.from_bytes(chunk[4:6], 'little')
                print(f"  Width: {width2}, Height: {height2}")
                if width2 > 0 and width2 < 320 and height2 > 0 and height2 < 200:
                    print(f"    -> This looks better!")
            
            print(f"\n  Trying offset 4 (skip 2 words):")
            if len(chunk) >= 8:
                width3 = int.from_bytes(chunk[4:6], 'little')
                height3 = int.from_bytes(chunk[6:8], 'little')
                print(f"  Width: {width3}, Height: {height3}")
                if width3 > 0 and width3 < 320 and height3 > 0 and height3 < 200:
                    print(f"    -> This looks better!")
            
            print(f"\n  Trying offset 6 (skip 3 words):")
            if len(chunk) >= 10:
                width4 = int.from_bytes(chunk[6:8], 'little')
                height4 = int.from_bytes(chunk[8:10], 'little')
                print(f"  Width: {width4}, Height: {height4}")
                if width4 > 0 and width4 < 320 and height4 > 0 and height4 < 200:
                    print(f"    -> This looks better!")

def main():
    idx_path = r"C:\Users\ybarnoy\projects\falcon3\game\PICFONT.IDX"
    dat_path = r"C:\Users\ybarnoy\projects\falcon3\game\PICFONT.DAT"
    
    print("Loading...")
    entries = parse_idx(idx_path)
    
    with open(dat_path, 'rb') as f:
        dat_data = f.read()
    
    print(f"Found {len(entries)} sprites in {len(dat_data)} bytes")
    print("="*80)
    
    for offset, size in entries:
        test_as_raw_sprite(dat_data, offset, size)
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
