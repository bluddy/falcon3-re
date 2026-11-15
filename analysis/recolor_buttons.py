"""
Re-extract buttons with a grey-based palette for the menu system.
Since the armament screen should use grey tones, adjust the palette accordingly.
"""
from PIL import Image
from pathlib import Path
import struct

def make_grey_menu_palette():
    """Create a grey-based palette for menu buttons."""
    palette = []
    
    # Color 0: Black (background)
    palette.append((0, 0, 0))
    
    # Colors 1-15: EGA colors (keep for compatibility)
    ega_colors = [
        (0, 0, 170),     # 1: Blue -> Dark Grey
        (0, 170, 0),     # 2: Green
        (0, 170, 170),   # 3: Cyan
        (170, 0, 0),     # 4: Red
        (170, 0, 170),   # 5: Magenta
        (170, 85, 0),    # 6: Brown
        (170, 170, 170), # 7: Light Gray
        (85, 85, 85),    # 8: Dark Gray
        (85, 85, 255),   # 9: Light Blue -> Grey
        (85, 255, 85),   # 10: Light Green
        (85, 255, 255),  # 11: Light Cyan
        (255, 85, 85),   # 12: Light Red
        (255, 85, 255),  # 13: Light Magenta
        (255, 255, 85),  # 14: Yellow
        (255, 255, 255), # 15: White
    ]
    palette.extend(ega_colors)
    
    # Colors 16-31: Grey ramp for buttons (these are the main menu colors)
    # Button colors observed: 16-31 (16 colors)
    # Should be: dark grey to light grey/white
    for i in range(16):
        # Create smooth grey ramp from dark to light
        grey = int(32 + i * 14)  # Range: 32 -> 242
        palette.append((grey, grey, grey))
    
    # Colors 32-231: Continue with 6×6×6 RGB cube
    for r in range(6):
        for g in range(6):
            for b in range(6):
                if len(palette) < 232:
                    palette.append((r * 51, g * 51, b * 51))
    
    # Colors 232-255: Grayscale ramp
    for i in range(24):
        grey = int(8 + i * 10.3)
        palette.append((grey, grey, grey))
    
    return palette

def extract_buttons_with_grey_palette(button_file, output_dir):
    """Re-extract buttons with grey palette."""
    with open(button_file, 'rb') as f:
        data = f.read()
    
    filename = Path(button_file).name
    print(f"\n=== {filename} (Grey Palette) ===")
    
    # Parse header
    count = data[0]
    pad = data[1]
    
    # Read size table
    sizes = []
    for i in range(count):
        pos = 2 + i * 2
        size = struct.unpack('<H', data[pos:pos+2])[0]
        sizes.append(size)
    
    header_size = 2 + count * 2
    
    # Create grey palette
    grey_palette = make_grey_menu_palette()
    flat_palette = []
    for r, g, b in grey_palette:
        flat_palette.extend([r, g, b])
    
    # Extract each record
    offset = header_size
    output_path = Path(output_dir) / f"{filename.lower()}_grey"
    output_path.mkdir(parents=True, exist_ok=True)
    
    extracted = 0
    for i in range(count):
        if offset + 4 > len(data):
            break
        
        # Read dimensions
        width = struct.unpack('<H', data[offset:offset+2])[0]
        height = struct.unpack('<H', data[offset+2:offset+4])[0]
        pixels_expected = width * height
        
        if width < 1 or width > 500 or height < 1 or height > 500:
            offset += sizes[i]
            continue
        
        # Read pixel data
        data_start = offset + 4
        data_size = sizes[i] - 4
        
        if data_start + data_size > len(data):
            break
        
        pixel_data = data[data_start:data_start+data_size]
        
        # Only extract uncompressed
        if len(pixel_data) == pixels_expected:
            img = Image.new('P', (width, height))
            img.putpalette(flat_palette)
            img.putdata(pixel_data)
            
            out_file = output_path / f"record_{i:02d}_{width}x{height}.png"
            img.save(out_file)
            extracted += 1
        
        offset += sizes[i]
    
    print(f"Extracted {extracted} images with grey palette")
    return extracted

def main():
    game_dir = Path('../game')
    output_dir = Path('../graphics/buttons')
    
    print("Re-extracting buttons with GREY palette for menu system")
    print("=" * 70)
    
    total = 0
    for button_file in ['BUTTON1', 'BUTTON2', 'BUTTON3']:
        filepath = game_dir / button_file
        if filepath.exists():
            count = extract_buttons_with_grey_palette(filepath, output_dir)
            total += count
    
    print("\n" + "=" * 70)
    print(f"Total extracted: {total} images with corrected grey palette")
    print(f"Output: {output_dir}/button*_grey/")

if __name__ == '__main__':
    main()
