"""
Preview button graphics as ASCII art and show statistics.
"""
from PIL import Image
from pathlib import Path
import sys

def analyze_image(filepath):
    """Analyze and display image info."""
    img = Image.open(filepath)
    pixels = list(img.getdata())
    
    print(f"\n{'='*70}")
    print(f"File: {filepath.name}")
    print(f"Size: {img.size[0]}x{img.size[1]} = {len(pixels)} pixels")
    
    # Color statistics
    unique_colors = sorted(set(pixels))
    print(f"Colors used: {len(unique_colors)} (range: {min(pixels)}-{max(pixels)})")
    
    # Show most common colors
    from collections import Counter
    counts = Counter(pixels)
    print(f"\nTop 5 colors:")
    for color, count in counts.most_common(5):
        pct = count / len(pixels) * 100
        print(f"  Color {color:3}: {count:5} pixels ({pct:5.1f}%)")
    
    # ASCII preview (scaled if too large)
    print(f"\nASCII Preview:")
    width, height = img.size
    
    # Scale down if needed
    scale_x = max(1, width // 80)
    scale_y = max(1, height // 40)
    
    # Create ASCII mapping based on color value
    def pixel_to_char(p):
        if p == 0:
            return ' '
        elif p < 50:
            return '.'
        elif p < 100:
            return ':'
        elif p < 150:
            return '+'
        elif p < 200:
            return '#'
        else:
            return '@'
    
    for y in range(0, height, scale_y):
        row = []
        for x in range(0, width, scale_x):
            pixel_idx = y * width + x
            row.append(pixel_to_char(pixels[pixel_idx]))
        print(''.join(row))

def main():
    if len(sys.argv) > 1:
        # Preview specific file
        filepath = Path(sys.argv[1])
        if filepath.exists():
            analyze_image(filepath)
        else:
            print(f"File not found: {filepath}")
        return
    
    # Preview a few interesting buttons
    base_dir = Path('../graphics/buttons')
    
    samples = [
        'button1/record_00_112x16.png',  # Large button
        'button1/record_12_16x16.png',   # Small square
        'button2/record_00_88x16.png',   # Medium button
        'button3/record_02_13x13.png',   # Tiny icon
        'button1/record_20_120x22.png',  # Largest button
    ]
    
    for sample in samples:
        filepath = base_dir / sample
        if filepath.exists():
            analyze_image(filepath)
        else:
            print(f"\nSkipping {sample} (not found)")

if __name__ == '__main__':
    main()
