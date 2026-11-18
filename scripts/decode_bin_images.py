"""
Decode Falcon 3.0 .BIN image files to PNG.
Format: 4-byte header (width, height as 16-bit words) + raw 8-bit indexed pixel data.
"""

import struct
from pathlib import Path
from PIL import Image

# Standard VGA palette (best guess - will be replaced if we find actual palette files)
def generate_default_palette():
    """Generate a default VGA-style 256-color palette."""
    palette = []
    
    # Standard VGA 256-color palette approximation
    for i in range(256):
        if i < 16:
            # Standard 16 EGA colors
            r = ((i & 0x04) >> 2) * 170 + ((i & 0x08) >> 3) * 85
            g = ((i & 0x02) >> 1) * 170 + ((i & 0x08) >> 3) * 85
            b = (i & 0x01) * 170 + ((i & 0x08) >> 3) * 85
        else:
            # Grayscale and color ramp
            val = (i - 16) * 255 // 239
            r = g = b = val
        
        palette.extend([r, g, b])
    
    return palette

def decode_bin_image(input_path, output_path, palette=None):
    """Decode a .BIN image file to PNG."""
    with open(input_path, 'rb') as f:
        # Read 4-byte header
        header = f.read(4)
        if len(header) != 4:
            print(f"  ERROR: File too small: {input_path.name}")
            return False
        
        width, height = struct.unpack('<HH', header)
        
        if width == 0 or height == 0 or width > 2000 or height > 2000:
            print(f"  ERROR: Invalid dimensions {width}x{height}: {input_path.name}")
            return False
        
        # Read pixel data
        expected_size = width * height
        pixel_data = f.read(expected_size)
        
        if len(pixel_data) != expected_size:
            print(f"  ERROR: Expected {expected_size} bytes, got {len(pixel_data)}: {input_path.name}")
            return False
        
        # Create image
        img = Image.frombytes('P', (width, height), pixel_data)
        
        # Set palette
        if palette is None:
            palette = generate_default_palette()
        img.putpalette(palette)
        
        # Save as PNG
        img.save(output_path)
        print(f"  OK {input_path.name} -> {output_path.name} ({width}x{height})")
        return True

def main():
    game_dir = Path(r"C:\Users\ybarnoy\projects\falcon3\game")
    output_dir = Path(r"C:\Users\ybarnoy\projects\falcon3\temp\decoded_images")
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 80)
    print("DECODING FALCON 3.0 .BIN IMAGES")
    print("=" * 80)
    print()
    
    # Find all .BIN files
    bin_files = sorted(game_dir.glob("*.BIN"))
    
    print(f"Found {len(bin_files)} .BIN files")
    print()
    
    palette = generate_default_palette()
    
    success_count = 0
    for bin_file in bin_files:
        output_file = output_dir / f"{bin_file.stem}.png"
        if decode_bin_image(bin_file, output_file, palette):
            success_count += 1
    
    print()
    print("=" * 80)
    print(f"Successfully decoded: {success_count} / {len(bin_files)} images")
    print(f"Output directory: {output_dir}")
    print("=" * 80)

if __name__ == "__main__":
    main()
