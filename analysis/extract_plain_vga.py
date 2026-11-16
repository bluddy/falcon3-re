"""
Extract plain VGA images (no compression, just width/height/pixels).
Based on successful BUTTON and LOSETEXT extraction.
"""

import struct
from pathlib import Path
from PIL import Image

def extract_plain_vga_image(filepath, output_path=None):
    """
    Extract a plain VGA image file.
    
    Format:
    - Bytes 0-1: width (word, little-endian)
    - Bytes 2-3: height (word, little-endian)  
    - Bytes 4+: pixel data (width × height bytes, uncompressed)
    """
    with open(filepath, 'rb') as f:
        data = f.read()
    
    if len(data) < 4:
        print(f"ERROR: File too small ({len(data)} bytes)")
        return None
    
    # Read dimensions
    width = struct.unpack('<H', data[0:2])[0]
    height = struct.unpack('<H', data[2:4])[0]
    
    print(f"Dimensions: {width}x{height}")
    print(f"Expected pixel data: {width * height} bytes")
    print(f"Actual data after header: {len(data) - 4} bytes")
    
    # Sanity checks
    if width == 0 or height == 0 or width > 640 or height > 480:
        print(f"WARNING: Unusual dimensions")
    
    expected_size = width * height + 4
    if len(data) != expected_size:
        diff = len(data) - expected_size
        print(f"WARNING: Size mismatch! Off by {diff} bytes")
        print(f"  Expected: {expected_size} (4 header + {width}×{height})")
        print(f"  Actual: {len(data)}")
        
        # Maybe there's a different header?
        if len(data) > expected_size:
            extra_header = len(data) - (width * height) - 4
            print(f"  Possible extra header: {extra_header} bytes")
    
    # Extract pixels
    pixel_offset = 4
    pixel_count = width * height
    
    if pixel_offset + pixel_count > len(data):
        print(f"ERROR: Not enough pixel data!")
        # Try anyway with what we have
        pixel_count = len(data) - pixel_offset
        print(f"  Using {pixel_count} pixels instead")
    
    pixels = data[pixel_offset:pixel_offset + pixel_count]
    
    # Create image
    img = Image.new('P', (width, height))
    
    # Grey palette (from successful BUTTON extraction)
    palette = []
    # Colors 0-15: standard VGA colors
    for i in range(16):
        if i == 0:
            palette.extend([0, 0, 0])  # Black
        elif i < 8:
            val = 128
            palette.extend([
                val if i & 4 else 0,
                val if i & 2 else 0,
                val if i & 1 else 0
            ])
        else:
            val = 255
            palette.extend([
                val if i & 4 else 0,
                val if i & 2 else 0,
                val if i & 1 else 0
            ])
    
    # Colors 16-31: grey ramp (for buttons/UI)
    for i in range(16):
        grey = 32 + i * 14  # 32 to 242
        palette.extend([grey, grey, grey])
    
    # Colors 32-255: standard greyscale  
    for i in range(32, 256):
        palette.extend([i, i, i])
    
    img.putpalette(palette)
    
    # Handle size mismatch
    if len(pixels) == pixel_count:
        img.putdata(pixels)
    else:
        # Pad with zeros
        padded = list(pixels) + [0] * (pixel_count - len(pixels))
        img.putdata(padded[:pixel_count])
    
    # Save
    if output_path is None:
        stem = Path(filepath).stem
        output_path = f"{stem}_{width}x{height}.png"
    
    img.save(output_path)
    print(f"Saved: {output_path}")
    
    return img

def try_multiple_offsets(filepath):
    """Try different header offsets in case format varies."""
    print(f"\n{'='*80}")
    print(f"Trying different header offsets for: {Path(filepath).name}")
    print(f"{'='*80}")
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data)} bytes\n")
    
    # Try different offsets
    for offset in [0, 2, 4, 6, 8, 10]:
        print(f"\n--- Offset {offset} bytes ---")
        
        if offset + 4 > len(data):
            print("Not enough data")
            continue
        
        width = struct.unpack('<H', data[offset:offset+2])[0]
        height = struct.unpack('<H', data[offset+2:offset+4])[0]
        
        print(f"Dimensions: {width}x{height}")
        
        if width == 0 or height == 0 or width > 640 or height > 480:
            print("  -> Invalid dimensions")
            continue
        
        expected_pixels = width * height
        available_pixels = len(data) - offset - 4
        
        print(f"Expected pixels: {expected_pixels}")
        print(f"Available pixels: {available_pixels}")
        
        if abs(expected_pixels - available_pixels) < 100:
            print("  -> GOOD MATCH!")
            
            # Extract
            pixels = data[offset+4:offset+4+expected_pixels]
            
            img = Image.new('P', (width, height))
            
            # Grey palette
            palette = []
            for i in range(16):
                if i == 0:
                    palette.extend([0, 0, 0])
                elif i < 8:
                    val = 128
                    palette.extend([
                        val if i & 4 else 0,
                        val if i & 2 else 0,
                        val if i & 1 else 0
                    ])
                else:
                    val = 255
                    palette.extend([
                        val if i & 4 else 0,
                        val if i & 2 else 0,
                        val if i & 1 else 0
                    ])
            for i in range(16):
                grey = 32 + i * 14
                palette.extend([grey, grey, grey])
            for i in range(32, 256):
                palette.extend([i, i, i])
            
            img.putpalette(palette)
            img.putdata(pixels)
            
            stem = Path(filepath).stem
            output = f"{stem}_offset{offset}_{width}x{height}.png"
            img.save(output)
            print(f"  Saved: {output}")

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python extract_plain_vga.py <file> [file2] [file3] ...")
        print("\nExamples:")
        print("  python extract_plain_vga.py ../game/FTITLE1")
        print("  python extract_plain_vga.py ../game/FTITLE*")
        sys.exit(1)
    
    for filepath in sys.argv[1:]:
        print(f"\n{'='*80}")
        print(f"Processing: {filepath}")
        print(f"{'='*80}")
        
        try:
            extract_plain_vga_image(filepath)
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        # Also try multiple offsets
        try:
            try_multiple_offsets(filepath)
        except Exception as e:
            print(f"ERROR in offset detection: {e}")

if __name__ == "__main__":
    main()
