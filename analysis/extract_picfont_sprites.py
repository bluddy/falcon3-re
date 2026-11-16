"""
Extract sprites from PICFONT.IDX/DAT based on RLE decompressor at 0x88460.

RLE Format (from assembly analysis):
- Data format: [width:word][height:word][rle_compressed_planes]
- RLE encoding:
  - flag byte with bit 7 set (0x80-0xFF): RUN
    - count = flag & 0x7F
    - followed by 1 value byte
    - repeat value 'count' times
  - flag byte with bit 7 clear (0x00-0x7F): LITERAL  
    - count = flag
    - followed by 'count' data bytes
    - copy bytes literally
- Output: VGA planar mode (4 bit planes)
- Each plane is decoded separately in sequence
"""

import struct
from pathlib import Path
from PIL import Image

def read_word_le(data, offset):
    """Read little-endian word."""
    return struct.unpack('<H', data[offset:offset+2])[0]

def rle_decompress_plane(data, offset, width_bytes):
    """
    Decompress one RLE-encoded plane.
    
    Returns: (decompressed_bytes, bytes_consumed)
    """
    result = []
    consumed = 0
    
    while len(result) < width_bytes:
        if offset + consumed >= len(data):
            break
        
        flag = data[offset + consumed]
        consumed += 1
        
        if flag & 0x80:  # RUN: repeat single value
            count = flag & 0x7F
            if count == 0:
                continue
            if offset + consumed >= len(data):
                break
            value = data[offset + consumed]
            consumed += 1
            result.extend([value] * count)
        else:  # LITERAL: copy bytes
            count = flag
            if count == 0:
                continue
            if offset + consumed + count > len(data):
                # Take what we can get
                count = len(data) - (offset + consumed)
            result.extend(data[offset + consumed:offset + consumed + count])
            consumed += count
    
    return bytes(result), consumed

def rle_decompress_vga_planar(data, offset):
    """
    Decompress VGA planar RLE image.
    
    Format:
    - width (word)
    - height (word)  
    - plane 0 RLE data
    - plane 1 RLE data
    - plane 2 RLE data
    - plane 3 RLE data
    
    Returns: (width, height, pixels, bytes_consumed)
    pixels is array of 256-color palette indices
    """
    width = read_word_le(data, offset)
    height = read_word_le(data, offset + 2)
    offset += 4
    consumed = 4
    
    print(f"  Decompressing: {width}x{height}")
    
    # VGA planar: width is in groups of 4 pixels
    # Each plane stores 1 bit per pixel
    width_bytes = (width + 3) // 4  # Round up to nearest multiple of 4
    total_pixels = width * height
    
    # Decompress 4 planes
    planes = []
    for plane_num in range(4):
        plane_data = []
        for row in range(height):
            row_data, row_consumed = rle_decompress_plane(data, offset, width_bytes)
            plane_data.append(row_data)
            offset += row_consumed
            consumed += row_consumed
        planes.append(plane_data)
    
    # Combine planes into 8-bit pixels
    # Each pixel = bit from plane 0 | (bit from plane 1 << 1) | (bit from plane 2 << 2) | (bit from plane 3 << 3)
    pixels = []
    for y in range(height):
        for x in range(width):
            byte_index = x // 4
            bit_index = 7 - (x % 4) * 2  # VGA planar bit ordering
            
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
        if offset == 0 and size == 0:
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
        print(f"\nSprite {i}: offset={offset} (0x{offset:04X}), size={size}")
        
        if offset + size > len(dat_data):
            print(f"  ERROR: Out of bounds!")
            continue
        
        try:
            # Each entry may have a 6-byte header (magic, x, y) or just be raw RLE
            # Try to detect header
            chunk = dat_data[offset:offset+size]
            
            # Check for magic number 0x0400
            if len(chunk) >= 6:
                magic = read_word_le(chunk, 0)
                if magic == 0x0400 or magic == 0x0004:
                    # Has header
                    x_pos = read_word_le(chunk, 2)
                    y_pos = read_word_le(chunk, 4)
                    print(f"  Header: magic=0x{magic:04X}, pos=({x_pos},{y_pos})")
                    data_offset = 6
                else:
                    data_offset = 0
            else:
                data_offset = 0
            
            # Try to decompress
            width, height, pixels, consumed = rle_decompress_vga_planar(chunk, data_offset)
            
            print(f"  Success: {width}x{height}, consumed {consumed+data_offset}/{size} bytes")
            
            # Create image with VGA palette (grayscale for now)
            img = Image.new('P', (width, height))
            # Set grayscale palette
            palette = []
            for i in range(256):
                palette.extend([i, i, i])
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
        print("Usage: python extract_picfont_sprites.py PICFONT.IDX PICFONT.DAT [output_dir]")
        print("\nThis script extracts sprites from PICFONT files using the RLE decompressor")
        print("algorithm reverse-engineered from Falcon 3.0 at address 0x88460.")
        sys.exit(1)
    
    idx_path = sys.argv[1]
    dat_path = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "picfont_sprites"
    
    extract_picfont_sprites(idx_path, dat_path, output_dir)
