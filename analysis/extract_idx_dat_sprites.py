"""
Extract sprites from .IDX/.DAT files with correct format.

Format discovered:
  Offset 0-1: Magic 0x0400 (always)
  Offset 2-3: Width (word, little-endian)
  Offset 4-5: Height (word, little-endian)
  Offset 6+:  VGA planar RLE compressed data
"""

import struct
from pathlib import Path
from PIL import Image

def read_word_le(data, offset):
    """Read little-endian word."""
    if offset + 2 > len(data):
        return None
    return struct.unpack('<H', data[offset:offset+2])[0]

def rle_decompress_row(data, offset, width_bytes):
    """
    Decompress exactly width_bytes of RLE data for one row of one plane.
    
    Returns: (decompressed_bytes, bytes_consumed)
    """
    result = []
    consumed = 0
    bytes_remaining = width_bytes
    
    while bytes_remaining > 0:
        if offset + consumed >= len(data):
            print(f"      WARNING: Ran out of data (need {bytes_remaining} more bytes)")
            break
        
        flag = data[offset + consumed]
        consumed += 1
        
        if flag & 0x80:  # RUN: repeat single value
            count = flag & 0x7F
            if count == 0:
                continue
            if count > bytes_remaining:
                count = bytes_remaining
            
            if offset + consumed >= len(data):
                print(f"      WARNING: No value byte for RUN")
                break
            value = data[offset + consumed]
            consumed += 1
            result.extend([value] * count)
            bytes_remaining -= count
        else:  # LITERAL: copy bytes
            count = flag
            if count == 0:
                continue
            if count > bytes_remaining:
                count = bytes_remaining
            
            if offset + consumed + count > len(data):
                available = len(data) - (offset + consumed)
                count = available
            
            result.extend(data[offset + consumed:offset + consumed + count])
            consumed += count
            bytes_remaining -= count
    
    return bytes(result), consumed

def rle_decompress_vga_planar(data, offset, width, height):
    """
    Decompress VGA planar RLE image.
    
    Data format (starting at offset):
    - For each of 4 bit planes:
    -   For each row (height times):
    -     RLE compressed row data (exactly width/8 bytes when decompressed)
    
    Returns: (pixels, bytes_consumed) or (None, 0) on error
    """
    print(f"    Decompressing {width}x{height}...")
    
    # VGA planar: each byte stores 8 pixels worth of 1 bit
    width_bytes = (width + 7) // 8
    
    consumed = 0
    
    # Decompress 4 planes
    planes = []
    for plane_num in range(4):
        plane_data = []
        for row in range(height):
            row_data, row_consumed = rle_decompress_row(data, offset, width_bytes)
            if len(row_data) != width_bytes:
                print(f"      WARNING: Row {row} plane {plane_num}: got {len(row_data)} bytes, expected {width_bytes}")
            plane_data.append(row_data)
            offset += row_consumed
            consumed += row_consumed
        planes.append(plane_data)
    
    # Combine planes into 4-bit pixels
    pixels = []
    for y in range(height):
        for x in range(width):
            byte_index = x // 8
            bit_index = 7 - (x % 8)
            
            pixel = 0
            for plane_num in range(4):
                if byte_index < len(planes[plane_num][y]):
                    byte_val = planes[plane_num][y][byte_index]
                    bit = (byte_val >> bit_index) & 1
                    pixel |= (bit << plane_num)
            
            pixels.append(pixel)
    
    return bytes(pixels), consumed

def load_idx(idx_path):
    """Load .IDX index file."""
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

def extract_sprites(idx_path, dat_path, output_dir):
    """Extract all sprites from .IDX/.DAT pair."""
    print(f"\n{'='*80}")
    print(f"EXTRACTING: {Path(idx_path).name} / {Path(dat_path).name}")
    print(f"{'='*80}")
    
    entries = load_idx(idx_path)
    print(f"Found {len(entries)} entries in index")
    
    with open(dat_path, 'rb') as f:
        dat_data = f.read()
    print(f"DAT file size: {len(dat_data)} bytes")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    
    for i, (offset, size) in enumerate(entries):
        print(f"\n  Entry {i}: offset={offset} (0x{offset:04X}), size={size}")
        
        if offset + size > len(dat_data):
            print(f"    ERROR: Out of bounds!")
            continue
        
        chunk = dat_data[offset:offset+size]
        
        # Check for 0x0400 magic
        if len(chunk) < 6:
            print(f"    ERROR: Too small for header")
            continue
        
        magic = read_word_le(chunk, 0)
        if magic != 0x0400:
            print(f"    WARNING: No 0x0400 magic (got 0x{magic:04X})")
            continue
        
        width = read_word_le(chunk, 2)
        height = read_word_le(chunk, 4)
        
        print(f"    Dimensions: {width}x{height}")
        
        # Sanity check
        if width == 0 or height == 0 or width > 320 or height > 480:
            print(f"    ERROR: Invalid dimensions")
            continue
        
        # Decompress RLE data starting at offset 6
        try:
            pixels, consumed = rle_decompress_vga_planar(chunk, 6, width, height)
            
            if pixels is None:
                print(f"    ERROR: Decompression failed")
                continue
            
            print(f"    Consumed {consumed} bytes of RLE data ({consumed+6}/{size} total)")
            
            # Create image
            img = Image.new('P', (width, height))
            
            # EGA palette (16 colors)
            ega_palette = [
                0x00, 0x00, 0x00,  # 0: black
                0x00, 0x00, 0xAA,  # 1: blue
                0x00, 0xAA, 0x00,  # 2: green
                0x00, 0xAA, 0xAA,  # 3: cyan
                0xAA, 0x00, 0x00,  # 4: red
                0xAA, 0x00, 0xAA,  # 5: magenta
                0xAA, 0x55, 0x00,  # 6: brown
                0xAA, 0xAA, 0xAA,  # 7: light gray
                0x55, 0x55, 0x55,  # 8: dark gray
                0x55, 0x55, 0xFF,  # 9: bright blue
                0x55, 0xFF, 0x55,  # A: bright green
                0x55, 0xFF, 0xFF,  # B: bright cyan
                0xFF, 0x55, 0x55,  # C: bright red
                0xFF, 0x55, 0xFF,  # D: bright magenta
                0xFF, 0xFF, 0x55,  # E: yellow
                0xFF, 0xFF, 0xFF,  # F: white
            ]
            palette = ega_palette + [0, 0, 0] * 240
            img.putpalette(palette)
            img.putdata(pixels)
            
            # Save
            base_name = Path(dat_path).stem.lower()
            output_path = output_dir / f"{base_name}_sprite_{i:03d}_{width}x{height}.png"
            img.save(output_path)
            print(f"    SUCCESS: {output_path.name}")
            
            success_count += 1
            
        except Exception as e:
            print(f"    ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*80}")
    print(f"Extracted {success_count}/{len(entries)} sprites from {Path(dat_path).name}")
    print(f"{'='*80}")
    
    return success_count

def main():
    import sys
    
    game_dir = Path("..") / "game"
    
    # Default: extract common sprite files
    if len(sys.argv) < 2:
        pairs = [
            ("FGENBMAP.IDX", "FGENBMAP.DAT", "extracted_sprites"),
            ("GENBMAP.IDX", "GENBMAP.DAT", "extracted_sprites"),
            ("PATCHES.IDX", "PATCHES.DAT", "extracted_sprites"),
            ("HPATCHES.IDX", "HPATCHES.DAT", "extracted_sprites"),
            ("MPATCHES.IDX", "MPATCHES.DAT", "extracted_sprites"),
        ]
    else:
        # Custom: python script.py PICFONT.IDX PICFONT.DAT output_dir
        if len(sys.argv) < 3:
            print("Usage: python extract_idx_dat_sprites.py [IDX_FILE DAT_FILE [OUTPUT_DIR]]")
            print("\nDefault: extracts FGENBMAP, GENBMAP, PATCHES, HPATCHES, MPATCHES")
            sys.exit(1)
        
        idx_name = sys.argv[1]
        dat_name = sys.argv[2]
        output_name = sys.argv[3] if len(sys.argv) > 3 else "extracted_sprites"
        pairs = [(idx_name, dat_name, output_name)]
    
    total_success = 0
    total_entries = 0
    
    for idx_name, dat_name, output_name in pairs:
        idx_path = game_dir / idx_name
        dat_path = game_dir / dat_name
        
        if not idx_path.exists():
            print(f"\nSkipping {idx_name} (not found)")
            continue
        
        if not dat_path.exists():
            print(f"\nSkipping {dat_name} (not found)")
            continue
        
        success = extract_sprites(idx_path, dat_path, output_name)
        total_success += success
        
        # Count total entries
        entries = load_idx(idx_path)
        total_entries += len(entries)
    
    print(f"\n{'='*80}")
    print(f"FINAL RESULTS")
    print(f"{'='*80}")
    print(f"Total: {total_success}/{total_entries} sprites extracted successfully")
    print(f"Output directory: extracted_sprites/")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
