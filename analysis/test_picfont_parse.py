"""
Simple test to parse PICFONT structure without full decompression.
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

def analyze_sprite_header(data, offset, size):
    """Analyze sprite data structure."""
    chunk = data[offset:offset+size]
    
    print(f"\n=== Sprite at offset {offset} (0x{offset:04X}), size {size} ===")
    
    # First 16 bytes
    print("First 16 bytes:")
    for i in range(min(16, len(chunk))):
        print(f"  [{i:2d}] 0x{chunk[i]:02X} ({chunk[i]:3d})", end="")
        if i % 4 == 3:
            # Show as word
            if i >= 1:
                word_val = int.from_bytes(chunk[i-1:i+1], 'little')
                print(f"  <- bytes {i-1}-{i}: word = 0x{word_val:04X} ({word_val})")
            else:
                print()
        else:
            print()
    
    # Check for header
    if len(chunk) >= 6:
        word0 = int.from_bytes(chunk[0:2], 'little')
        word1 = int.from_bytes(chunk[2:4], 'little')
        word2 = int.from_bytes(chunk[4:6], 'little')
        
        print(f"\nPossible header:")
        print(f"  Word 0: 0x{word0:04X} ({word0}) - magic/type?")
        print(f"  Word 1: 0x{word1:04X} ({word1}) - X pos?")
        print(f"  Word 2: 0x{word2:04X} ({word2}) - Y pos?")
        
        # If 0x0400 magic, sprite data starts at byte 6
        if word0 == 0x0400:
            print(f"\n  -> Magic 0x0400 detected! Sprite data likely starts at offset 6")
            if len(chunk) >= 10:
                width = int.from_bytes(chunk[6:8], 'little')
                height = int.from_bytes(chunk[8:10], 'little')
                print(f"  -> Dimensions at offset 6: {width}x{height}")
        else:
            # No header, dimensions at start
            print(f"\n  -> No magic, dimensions might be at offset 0: {word0}x{word1}")

def main():
    idx_path = r"C:\Users\ybarnoy\projects\falcon3\game\PICFONT.IDX"
    dat_path = r"C:\Users\ybarnoy\projects\falcon3\game\PICFONT.DAT"
    
    print("Loading index...")
    entries = parse_idx(idx_path)
    print(f"Found {len(entries)} entries\n")
    
    print("Loading data...")
    with open(dat_path, 'rb') as f:
        dat_data = f.read()
    print(f"Data size: {len(dat_data)} bytes\n")
    
    print("="*80)
    for i, (offset, size) in enumerate(entries):
        analyze_sprite_header(dat_data, offset, size)
    
    print("\n" + "="*80)
    print("Analysis complete")

if __name__ == "__main__":
    main()
