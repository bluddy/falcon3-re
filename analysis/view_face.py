"""
Convert raw face data to PNG with VGA palette
"""
from PIL import Image
import struct

# Standard VGA palette (256 colors, 6-bit RGB values scaled to 8-bit)
def get_vga_palette():
    """Generate standard VGA 256-color palette"""
    palette = []
    
    # First 16 colors - EGA compatible
    ega_colors = [
        (0x00, 0x00, 0x00),  # 0: Black
        (0x00, 0x00, 0xAA),  # 1: Blue
        (0x00, 0xAA, 0x00),  # 2: Green
        (0x00, 0xAA, 0xAA),  # 3: Cyan
        (0xAA, 0x00, 0x00),  # 4: Red
        (0xAA, 0x00, 0xAA),  # 5: Magenta
        (0xAA, 0x55, 0x00),  # 6: Brown
        (0xAA, 0xAA, 0xAA),  # 7: Light Gray
        (0x55, 0x55, 0x55),  # 8: Dark Gray
        (0x55, 0x55, 0xFF),  # 9: Light Blue
        (0x55, 0xFF, 0x55),  # 10: Light Green
        (0x55, 0xFF, 0xFF),  # 11: Light Cyan
        (0xFF, 0x55, 0x55),  # 12: Light Red
        (0xFF, 0x55, 0xFF),  # 13: Light Magenta
        (0xFF, 0xFF, 0x55),  # 14: Yellow
        (0xFF, 0xFF, 0xFF),  # 15: White
    ]
    
    for r, g, b in ega_colors:
        palette.extend([r, g, b])
    
    # Colors 16-231: 6x6x6 color cube
    for r in range(6):
        for g in range(6):
            for b in range(6):
                palette.extend([
                    int(r * 255 / 5),
                    int(g * 255 / 5),
                    int(b * 255 / 5)
                ])
    
    # Colors 232-255: Grayscale ramp
    for i in range(24):
        val = int(8 + i * 10)
        palette.extend([val, val, val])
    
    return palette

def view_face(raw_file, width, height, output_png):
    """Convert raw pixel data to PNG"""
    with open(raw_file, 'rb') as f:
        pixels = f.read()
    
    if len(pixels) != width * height:
        print(f"Warning: Expected {width * height} pixels, got {len(pixels)}")
        # Pad or truncate
        if len(pixels) < width * height:
            pixels += b'\x00' * (width * height - len(pixels))
        else:
            pixels = pixels[:width * height]
    
    # Create paletted image
    img = Image.frombytes('P', (width, height), pixels)
    
    # Apply VGA palette
    palette = get_vga_palette()
    img.putpalette(palette)
    
    # Save as PNG
    img.save(output_png)
    print(f"Saved {output_png} ({width}x{height})")
    
    return img

if __name__ == '__main__':
    # View the test face with both possible dimensions
    import os
    
    if os.path.exists('test_face_33x37.raw'):
        print("Trying 33x37...")
        view_face('test_face_33x37.raw', 33, 37, 'test_face_33x37.png')
        
        print("\nTrying 37x33...")
        view_face('test_face_33x37.raw', 37, 33, 'test_face_37x33.png')
        
        print("\nBoth versions saved. Check which one looks correct.")
    else:
        print("test_face_33x37.raw not found")
