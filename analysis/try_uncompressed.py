"""
Try interpreting face data as uncompressed
"""
from PIL import Image
import struct

def get_vga_palette():
    """Generate standard VGA 256-color palette"""
    palette = []
    
    # First 16 colors - EGA compatible
    ega_colors = [
        (0x00, 0x00, 0x00), (0x00, 0x00, 0xAA), (0x00, 0xAA, 0x00), (0x00, 0xAA, 0xAA),
        (0xAA, 0x00, 0x00), (0xAA, 0x00, 0xAA), (0xAA, 0x55, 0x00), (0xAA, 0xAA, 0xAA),
        (0x55, 0x55, 0x55), (0x55, 0x55, 0xFF), (0x55, 0xFF, 0x55), (0x55, 0xFF, 0xFF),
        (0xFF, 0x55, 0x55), (0xFF, 0x55, 0xFF), (0xFF, 0xFF, 0x55), (0xFF, 0xFF, 0xFF),
    ]
    
    for r, g, b in ega_colors:
        palette.extend([r, g, b])
    
    # Colors 16-231: 6x6x6 color cube
    for r in range(6):
        for g in range(6):
            for b in range(6):
                palette.extend([int(r * 255 / 5), int(g * 255 / 5), int(b * 255 / 5)])
    
    # Colors 232-255: Grayscale ramp
    for i in range(24):
        val = int(8 + i * 10)
        palette.extend([val, val, val])
    
    return palette

dat = open('../game/people.dat', 'rb').read()

# First record: 666 bytes total
record = dat[0:666]

# Skip 6-byte header
pixels = record[6:]

print(f"Trying as uncompressed: {len(pixels)} bytes")

# Try various dimensions
test_dims = [
    (22, 30),  # 660 pixels exactly!
    (30, 22),
    (20, 33),
    (33, 20),
]

vga_palette = get_vga_palette()

for width, height in test_dims:
    expected = width * height
    if expected != len(pixels):
        continue
    
    print(f"\nTrying {width} x {height} (exact match!)...")
    
    img = Image.frombytes('P', (width, height), pixels)
    img.putpalette(vga_palette)
    
    output = f'uncompressed_{width}x{height}.png'
    img.save(output)
    print(f"  Saved: {output}")
