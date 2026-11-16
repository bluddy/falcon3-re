"""
Extract GENBMAP/FGENBMAP - try without assuming 0x0400 header.
Maybe RLE data starts directly with width/height.
"""

import struct
from pathlib import Path
from PIL import Image

def read_word_le(data, offset):
    if offset + 2 > len(data):
        return None
    return struct.unpack('<H', data[offset:offset+2])[0]

def load_idx(idx_path):
    with open(idx_path, 'rb') as f:
        data = f.read()
    
    entries = []
    i = 0
    while i + 4 <= len(data):
        offset = read_word_le(data, i)
        size = read_word_le(data, i + 2)
        if offset is None or size is None:
            break
        entries.append((offset, size))
        i += 4
    
    return entries

def try_raw_vga(chunk, sprite_id):
    """Try as uncompressed VGA (width, height, pixels)."""
    if len(chunk) < 4:
        return None
    
    width = read_word_le(chunk, 0)
    height = read_word_le(chunk, 2)
    
    if width == 0 or height == 0 or width > 320 or height > 200:
        return None
    
    expected_size = width * height + 4
    if len(chunk) != expected_size:
        return None
    
    print(f"  Sprite {sprite_id}: {width}x{height} uncompressed VGA")
    
    pixels = chunk[4:]
    img = Image.new('P', (width, height))
    
    # Grey palette
    palette = []
    for i in range(256):
        palette.extend([i, i, i])
    img.putpalette(palette)
    img.putdata(pixels)
    
    return img

def try_rle_with_0x0400_header(chunk, sprite_id):
    """Try as RLE with 0x0400 header: [0x0400][width][height][RLE data]."""
    if len(chunk) < 6:
        return None
    
    magic = read_word_le(chunk, 0)
    if magic != 0x0400:
        return None
    
    width = read_word_le(chunk, 2)
    height = read_word_le(chunk, 4)
    
    if width == 0 or height == 0 or width > 320 or height > 200:
        return None
    
    print(f"  Sprite {sprite_id}: {width}x{height} RLE (with 0x0400 header)")
    print(f"    RLE data starts at offset 6, size {len(chunk)-6} bytes")
    
    # Now decompress RLE starting at offset 6
    # This is VGA planar RLE - need the full decompressor
    # For now, just report that we found a valid header
    return None  # TODO: implement RLE decompression

def dump_hex(data, max_bytes=64):
    """Dump hex for analysis."""
    for i in range(min(max_bytes, len(data))):
        if i % 16 == 0:
            print(f"\n    {i:04X}: ", end='')
        print(f"{data[i]:02X} ", end='')
    print()

def analyze_genbmap(idx_path, dat_path, output_dir):
    """Analyze GENBMAP structure."""
    print(f"="*80)
    print(f"ANALYZING: {Path(idx_path).name} / {Path(dat_path).name}")
    print(f"="*80)
    
    entries = load_idx(idx_path)
    print(f"\nFound {len(entries)} entries in index")
    
    with open(dat_path, 'rb') as f:
        dat_data = f.read()
    print(f"DAT file size: {len(dat_data)} bytes")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, (offset, size) in enumerate(entries):
        print(f"\n--- Entry {i} ---")
        print(f"  Offset: {offset} (0x{offset:04X})")
        print(f"  Size: {size} bytes")
        
        if offset + size > len(dat_data):
            print(f"  ERROR: Out of bounds!")
            continue
        
        chunk = dat_data[offset:offset+size]
        
        # Show first bytes
        print(f"  First 32 bytes:")
        dump_hex(chunk, 32)
        
        # Try different interpretations
        
        # 1. RLE with 0x0400 header
        result = try_rle_with_0x0400_header(chunk, i)
        if result:
            continue
        
        # 2. Raw VGA (no header, just w/h/pixels)
        img = try_raw_vga(chunk, i)
        if img:
            output_path = output_dir / f"sprite_{i:03d}_raw.png"
            img.save(output_path)
            print(f"  SUCCESS: Saved as {output_path.name}")
            continue
        
        # 2. Check for patterns
        if len(chunk) >= 4:
            w0 = read_word_le(chunk, 0)
            h0 = read_word_le(chunk, 2)
            print(f"  Offset 0: width={w0}, height={h0}")
        
        if len(chunk) >= 8:
            w4 = read_word_le(chunk, 4)
            h4 = read_word_le(chunk, 6)
            print(f"  Offset 4: width={w4}, height={h4}")
        
        if len(chunk) >= 12:
            w8 = read_word_le(chunk, 8)
            h8 = read_word_le(chunk, 10)
            print(f"  Offset 8: width={w8}, height={h8}")
        
        print(f"  -> Could not decode")

if __name__ == "__main__":
    import sys
    
    game_dir = Path("..") / "game"
    
    pairs = [
        ("FGENBMAP.IDX", "FGENBMAP.DAT", "fgenbmap_extracted"),
        ("GENBMAP.IDX", "GENBMAP.DAT", "genbmap_extracted"),
    ]
    
    for idx_name, dat_name, output_name in pairs:
        idx_path = game_dir / idx_name
        dat_path = game_dir / dat_name
        
        if not idx_path.exists() or not dat_path.exists():
            print(f"Skipping {idx_name} (not found)")
            continue
        
        analyze_genbmap(idx_path, dat_path, output_name)
        print("\n")
