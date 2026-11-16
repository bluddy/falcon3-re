"""
Extract PICFONT sprites - Version 2 with corrected RLE algorithm.

Based on careful analysis of RLE decompressor at 0x88460.
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
            print(f"    ERROR: Ran out of data (need {bytes_remaining} more bytes)")
            break
        
        flag = data[offset + consumed]
        consumed += 1
        
        if flag & 0x80:  # RUN: repeat single value
            count = flag & 0x7F
            if count == 0 or count > bytes_remaining:
                print(f"    WARNING: RUN count {count} (remaining {bytes_remaining})")
                if count == 0:
                    continue
                count = min(count, bytes_remaining)
            
            if offset + consumed >= len(data):
                print(f"    ERROR: No value byte for RUN")
                break
            value = data[offset + consumed]
            consumed += 1
            result.extend([value] * count)
            bytes_remaining -= count
        else:  # LITERAL: copy bytes
            count = flag
            if count == 0 or count > bytes_remaining:
                print(f"    WARNING: LITERAL count {count} (remaining {bytes_remaining})")
                if count == 0:
                    continue
                count = min(count, bytes_remaining)
            
            if offset + consumed + count > len(data):
                available = len(data) - (offset + consumed)
                print(f"    ERROR: Not enough literal data (need {count}, have {available})")
                count = available
            
            result.extend(data[offset + consumed:offset + consumed + count])
            consumed += count
            bytes_remaining -= count
    
    return bytes(result), consumed

def rle_decompress_vga_planar(data, offset):
    """
    Decompress VGA planar RLE image.
    
    Format (from assembly at 0x88460):
    - width (word) - in pixels
    - height (word) - in rows
    - For each of 4 bit planes:
    -   For each row (height times):
    -     RLE compressed row data (exactly width/4 bytes when decompressed)
    
    Returns: (width, height, pixels, bytes_consumed)
    """
    width = read_word_le(data, offset)
    height = read_word_le(data, offset + 2)
    
    if width is None or height is None:
        return None, None, None, 0
    
    print(f"  Dimensions: {width}x{height}")
    
    # Sanity check
    if width == 0 or height == 0 or width > 320 or height > 200:
        print(f"  ERROR: Invalid dimensions")
        return None, None, None, 4
    
    offset += 4
    consumed = 4
    
    # VGA planar: each byte stores 8 pixels worth of 1 bit
    # Width in bytes per plane
    width_bytes = (width + 7) // 8
    
    print(f"  Width in bytes: {width_bytes} per plane per row")
    
    # Decompress 4 planes
    planes = []
    for plane_num in range(4):
        print(f"  Decompressing plane {plane_num}...")
        plane_data = []
        for row in range(height):
            row_data, row_consumed = rle_decompress_row(data, offset, width_bytes)
            if len(row_data) != width_bytes:
                print(f"    Row {row}: got {len(row_data)} bytes, expected {width_bytes}")
            plane_data.append(row_data)
            offset += row_consumed
            consumed += row_consumed
        planes.append(plane_data)
    
    # Combine planes into 4-bit pixels
    # Each pixel = bit0 from plane0 | bit1 from plane1 | bit2 from plane2 | bit3 from plane3
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
    
    return width, height, bytes(pixels), consumed

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

def extract_picfont_sprites(idx_path, dat_path, output_dir):
    """Extract all sprites from PICFONT.IDX/DAT."""
    print(f"Loading index from {idx_path}...")
    entries = load_idx(idx_path)
    print(f"  Found {len(entries)} entries")
    
    print(f"\nLoading data from {dat_path}...")
    with open(dat_path, 'rb') as f:
        dat_data = f.read()
    print(f"  Data size: {len(dat_data)} bytes")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nExtracting sprites to {output_dir}/...")
    
    success_count = 0
    for i, (offset, size) in enumerate(entries):
        print(f"\n--- Sprite {i} ---")
        print(f"  Offset: {offset} (0x{offset:04X}), Size: {size} bytes")
        
        if offset + size > len(dat_data):
            print(f"  ERROR: Out of bounds!")
            continue
        
        try:
            chunk = dat_data[offset:offset+size]
            
            # Check for 6-byte header (magic + position)
            magic = read_word_le(chunk, 0)
            if magic == 0x0400:
                # Has header
                x_pos = read_word_le(chunk, 2)
                y_pos = read_word_le(chunk, 4)
                print(f"  Header found: magic=0x{magic:04X}, position=({x_pos},{y_pos})")
                data_offset = 6
            else:
                # No header, sprite data starts immediately
                data_offset = 0
            
            # Try to decompress
            width, height, pixels, consumed = rle_decompress_vga_planar(chunk, data_offset)
            
            if width is None:
                print(f"  FAILED: Could not decompress")
                continue
            
            print(f"  Success: {width}x{height}, consumed {consumed+data_offset}/{size} bytes")
            
            # Create image with EGA palette (16 colors)
            img = Image.new('P', (width, height))
            
            # EGA default palette
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
            # Extend to 256 colors (repeat pattern)
            palette = ega_palette + [0, 0, 0] * 240
            img.putpalette(palette)
            img.putdata(pixels)
            
            # Save
            output_path = output_dir / f"sprite_{i:03d}_{width}x{height}.png"
            img.save(output_path)
            print(f"  Saved: {output_path}")
            
            success_count += 1
            
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n" + "="*80)
    print(f"Extraction complete: {success_count}/{len(entries)} sprites successfully extracted")
    print("="*80)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python extract_picfont_v2.py PICFONT.IDX PICFONT.DAT [output_dir]")
        print("\nThis script extracts sprites from PICFONT files using the RLE decompressor")
        print("algorithm reverse-engineered from Falcon 3.0 at address 0x88460.")
        sys.exit(1)
    
    idx_path = sys.argv[1]
    dat_path = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "picfont_sprites"
    
    extract_picfont_sprites(idx_path, dat_path, output_dir)
