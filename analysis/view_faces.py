"""
View extracted faces as ASCII art to verify they look reasonable.
"""
from PIL import Image
from pathlib import Path
import sys

def view_face(filepath):
    """View a face as ASCII."""
    img = Image.open(filepath)
    pixels = list(img.getdata())
    width, height = img.size
    
    print(f"\n{filepath.name}")
    print("=" * width)
    
    # Map pixels to ASCII based on brightness
    chars = ' .:+#@'
    
    min_p = min(pixels)
    max_p = max(pixels)
    p_range = max_p - min_p if max_p > min_p else 1
    
    for y in range(height):
        row = []
        for x in range(width):
            p = pixels[y * width + x]
            normalized = (p - min_p) / p_range
            char_idx = int(normalized * (len(chars) - 1))
            row.append(chars[char_idx])
        print(''.join(row))
    
    print("=" * width)
    print(f"Size: {width}x{height}, Colors: {min_p}-{max_p}, Unique: {len(set(pixels))}")

def main():
    faces_dir = Path('../graphics/faces_fixed')
    
    if not faces_dir.exists():
        print(f"Directory not found: {faces_dir}")
        return
    
    faces = sorted(faces_dir.glob('face_*.png'))
    
    if not faces:
        print("No faces found!")
        return
    
    print(f"Found {len(faces)} faces")
    print("\nShowing first 5 faces:")
    
    for face in faces[:5]:
        view_face(face)

if __name__ == '__main__':
    main()
