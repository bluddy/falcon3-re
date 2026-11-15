"""
Extract raw uncompressed VGA images (320x200 with 4-byte header).
"""
import struct
from pathlib import Path
from PIL import Image

# Standard VGA palette approximation
vga_palette = []
ega_colors = [
    (0,0,0), (0,0,168), (0,168,0), (0,168,168),
    (168,0,0), (168,0,168), (168,84,0), (168,168,168),
    (84,84,84), (84,84,252), (84,252,84), (84,252,252),
    (252,84,84), (252,84,252), (252,252,84), (252,252,252)
]
for r,g,b in ega_colors:
    vga_palette.extend([r,g,b])

# Colors 16-231: Color cube
for r in range(6):
    for g in range(6):
        for b in range(6):
            vga_palette.extend([r * 51, g * 51, b * 51])

# Colors 232-255: Grayscale
for i in range(24):
    gray = 8 + i * 10
    vga_palette.extend([gray, gray, gray])

game_dir = Path(__file__).parent.parent / 'game'
output_dir = Path(__file__).parent.parent / 'graphics' / 'fullscreen'
output_dir.mkdir(exist_ok=True)

# All files with full-screen images (320x200 + 4 byte header = 64004)
vga_files = []
for f in game_dir.glob('*'):
    if f.is_file() and f.stat().st_size == 64004:
        vga_files.append(f.name)

for filename in sorted(vga_files):
    filepath = game_dir / filename
    if not filepath.exists():
        continue
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"\n{filename}: {len(data)} bytes")
    
    if len(data) < 4:
        continue
    
    # Try reading as width/height header
    width, height = struct.unpack('<HH', data[0:4])
    expected_size = width * height + 4
    
    print(f"  Header suggests: {width}×{height} = {width*height} pixels")
    print(f"  Expected total: {expected_size} bytes")
    print(f"  Actual: {len(data)} bytes")
    
    if len(data) == expected_size:
        # Perfect match!
        pixels = data[4:]
        print(f"  MATCH! Extracting...")
        
        img = Image.new('P', (width, height))
        img.putdata(pixels)
        img.putpalette(vga_palette)
        
        output_path = output_dir / f'{filename}_{width}x{height}.png'
        img.save(output_path)
        print(f"  Saved: {output_path.name}")
        
        # Show pixel stats
        pixel_list = list(pixels)
        print(f"  Pixel range: {min(pixel_list)} to {max(pixel_list)}")
    elif width * height == len(data):
        # No header, just raw pixels
        print(f"  No header, trying as raw {width}×{height}")
        pixels = data
        
        img = Image.new('P', (width, height))
        img.putdata(pixels)
        img.putpalette(vga_palette)
        
        output_path = output_dir / f'{filename}_{width}x{height}_noheader.png'
        img.save(output_path)
        print(f"  Saved: {output_path.name}")
    else:
        print(f"  Size mismatch - not a simple image")

print(f"\n{'='*80}")
print(f"Extracted images to: {output_dir}")
