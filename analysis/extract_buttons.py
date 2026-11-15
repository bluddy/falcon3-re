"""
Extract all button graphics from BUTTON1, BUTTON2, BUTTON3 files.
These are uncompressed VGA graphics with a simple format.
"""
import struct
from pathlib import Path
from PIL import Image

# Standard VGA palette approximation
def make_vga_palette():
    """Create standard VGA 256-color palette."""
    palette = []
    
    # Colors 0-15: Standard 16 EGA colors
    ega_colors = [
        (0, 0, 0),       # 0: Black
        (0, 0, 170),     # 1: Blue
        (0, 170, 0),     # 2: Green
        (0, 170, 170),   # 3: Cyan
        (170, 0, 0),     # 4: Red
        (170, 0, 170),   # 5: Magenta
        (170, 85, 0),    # 6: Brown
        (170, 170, 170), # 7: Light Gray
        (85, 85, 85),    # 8: Dark Gray
        (85, 85, 255),   # 9: Light Blue
        (85, 255, 85),   # 10: Light Green
        (85, 255, 255),  # 11: Light Cyan
        (255, 85, 85),   # 12: Light Red
        (255, 85, 255),  # 13: Light Magenta
        (255, 255, 85),  # 14: Yellow
        (255, 255, 255), # 15: White
    ]
    palette.extend(ega_colors)
    
    # Colors 16-231: 6×6×6 RGB color cube
    for r in range(6):
        for g in range(6):
            for b in range(6):
                palette.append((r * 51, g * 51, b * 51))
    
    # Colors 232-255: Grayscale ramp
    for i in range(24):
        gray = int(8 + i * 10.3)
        palette.append((gray, gray, gray))
    
    return palette

def extract_button_file(filepath, output_dir):
    """Extract all button graphics from a BUTTON file."""
    with open(filepath, 'rb') as f:
        data = f.read()
    
    filename = Path(filepath).name
    print(f"\n=== {filename} ===")
    print(f"File size: {len(data)} bytes")
    
    # Parse header
    count = data[0]
    pad = data[1]
    print(f"Count: {count} records, Pad: 0x{pad:02X}")
    
    # Read size table
    sizes = []
    for i in range(count):
        pos = 2 + i * 2
        size = struct.unpack('<H', data[pos:pos+2])[0]
        sizes.append(size)
    
    header_size = 2 + count * 2
    print(f"Header: {header_size} bytes")
    print(f"Data: {sum(sizes)} bytes")
    
    # Create VGA palette
    vga_palette = make_vga_palette()
    flat_palette = []
    for r, g, b in vga_palette:
        flat_palette.extend([r, g, b])
    
    # Extract each record
    offset = header_size
    output_path = Path(output_dir) / filename.lower()
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\nExtracting records:")
    for i in range(count):
        if offset + 4 > len(data):
            print(f"  Record {i}: ERROR - not enough data for header")
            break
        
        # Read dimensions
        width = struct.unpack('<H', data[offset:offset+2])[0]
        height = struct.unpack('<H', data[offset+2:offset+4])[0]
        pixels_expected = width * height
        
        # Check if dimensions are reasonable
        if width < 1 or width > 500 or height < 1 or height > 500:
            print(f"  Record {i}: ERROR - invalid dimensions {width}x{height}")
            offset += sizes[i]
            continue
        
        # Read pixel data
        data_start = offset + 4
        data_size = sizes[i] - 4
        
        if data_start + data_size > len(data):
            print(f"  Record {i}: ERROR - not enough pixel data")
            break
        
        pixel_data = data[data_start:data_start+data_size]
        
        # Check if uncompressed
        if len(pixel_data) == pixels_expected:
            status = "uncompressed"
        else:
            ratio = (len(pixel_data) / pixels_expected * 100) if pixels_expected > 0 else 0
            status = f"compressed? ({ratio:.1f}%)"
        
        print(f"  Record {i:2}: {width:3}x{height:3} = {pixels_expected:5} px, {data_size:5} bytes - {status}")
        
        # Create image (only if uncompressed)
        if len(pixel_data) == pixels_expected:
            img = Image.new('P', (width, height))
            img.putpalette(flat_palette)
            img.putdata(pixel_data)
            
            out_file = output_path / f"record_{i:02d}_{width}x{height}.png"
            img.save(out_file)
            print(f"           Saved: {out_file.relative_to(output_dir)}")
        
        offset += sizes[i]
    
    total_extracted = len(list(output_path.glob('*.png')))
    print(f"\nExtracted {total_extracted} images to {output_path.relative_to(output_dir)}/")

def main():
    game_dir = Path('../game')
    output_dir = Path('../graphics/buttons')
    
    print("Falcon 3.0 Button Graphics Extractor")
    print("=" * 50)
    
    for button_file in ['BUTTON1', 'BUTTON2', 'BUTTON3']:
        filepath = game_dir / button_file
        if filepath.exists():
            extract_button_file(filepath, output_dir)
        else:
            print(f"\nSkipping {button_file} (not found)")
    
    print("\n" + "=" * 50)
    print(f"Extraction complete! Check {output_dir}/ for images")

if __name__ == '__main__':
    main()
