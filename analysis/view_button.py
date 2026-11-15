"""
Better button preview with proper contrast mapping.
"""
from PIL import Image
from pathlib import Path
import sys

def preview_button(filepath, chars=' .:+#@'):
    """Preview button with better contrast."""
    img = Image.open(filepath)
    pixels = list(img.getdata())
    width, height = img.size
    
    print(f"\n{'='*80}")
    print(f"File: {filepath.name}")
    print(f"Size: {width}x{height}")
    
    # Get color range
    unique_colors = sorted(set(pixels))
    min_color = min(pixels)
    max_color = max(pixels)
    color_range = max_color - min_color if max_color > min_color else 1
    
    print(f"Colors: {len(unique_colors)} unique (range {min_color}-{max_color})")
    
    # Map colors to ASCII based on their relative value
    def map_to_ascii(pixel):
        # Normalize to 0-1 range
        normalized = (pixel - min_color) / color_range
        # Map to character set
        idx = int(normalized * (len(chars) - 1))
        return chars[idx]
    
    # Draw the image
    print(f"\n{filepath.stem}:")
    print('-' * min(width, 80))
    
    for y in range(height):
        row = []
        for x in range(width):
            pixel_idx = y * width + x
            row.append(map_to_ascii(pixels[pixel_idx]))
        print(''.join(row))
    print('-' * min(width, 80))

def main():
    base_dir = Path('../graphics/buttons')
    
    if len(sys.argv) > 1:
        # Show specific file
        filepath = Path(sys.argv[1])
        if not filepath.is_absolute():
            filepath = base_dir / filepath
        if filepath.exists():
            preview_button(filepath)
        else:
            print(f"Not found: {filepath}")
        return
    
    # Show a variety of buttons
    samples = [
        ('button1/record_00_112x16.png', 'Large button 1'),
        ('button1/record_03_54x16.png', 'Medium button'),
        ('button1/record_12_16x16.png', 'Small square button'),
        ('button2/record_16_24x24.png', 'Icon 24x24'),
        ('button3/record_02_13x13.png', 'Tiny icon'),
        ('button1/record_20_120x22.png', 'Large wide button'),
    ]
    
    for sample_path, description in samples:
        filepath = base_dir / sample_path
        if filepath.exists():
            print(f"\n{description}:")
            preview_button(filepath)
        else:
            print(f"\nSkipping {description} - not found")

if __name__ == '__main__':
    main()
