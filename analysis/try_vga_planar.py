"""
Try interpreting PEOPLE.DAT as VGA planar format.
VGA Mode 12h uses 4 bitplanes interleaved.
"""
import struct
from pathlib import Path
from PIL import Image

def make_vga_palette():
    """Standard VGA palette."""
    palette = []
    palette.append((0, 0, 0))
    
    ega = [(0,0,170), (0,170,0), (0,170,170), (170,0,0), (170,0,170),
           (170,85,0), (170,170,170), (85,85,85), (85,85,255), (85,255,85),
           (85,255,255), (255,85,85), (255,85,255), (255,255,85), (255,255,255)]
    palette.extend(ega)
    
    for i in range(16, 256):
        grey = int(i * 255 / 255)
        palette.append((grey, grey, grey))
    
    flat = []
    for r, g, b in palette:
        flat.extend([r, g, b])
    return flat

def deinterleave_planar(data, width, height):
    """
    Convert VGA planar format to linear.
    In planar mode, 4 bitplanes are stored sequentially or interleaved.
    Each plane holds 1 bit per pixel.
    """
    # Calculate bytes per plane
    pixels = width * height
    bits_per_plane = pixels
    bytes_per_plane = (bits_per_plane + 7) // 8
    
    if len(data) < bytes_per_plane * 4:
        return None
    
    # Try sequential planes first
    result = []
    for pixel_idx in range(pixels):
        byte_idx = pixel_idx // 8
        bit_idx = 7 - (pixel_idx % 8)
        
        # Read one bit from each plane
        pixel_value = 0
        for plane in range(4):
            plane_offset = plane * bytes_per_plane
            if plane_offset + byte_idx < len(data):
                byte_val = data[plane_offset + byte_idx]
                bit = (byte_val >> bit_idx) & 1
                pixel_value |= (bit << plane)
        
        result.append(pixel_value)
    
    return result

def try_planar_extraction():
    """Try extracting face 0 as VGA planar."""
    
    with open('../game/PEOPLE.IDX', 'rb') as f:
        idx_data = f.read()
    
    with open('../game/PEOPLE.DAT', 'rb') as f:
        dat_data = f.read()
    
    print("Trying VGA PLANAR format extraction")
    print("=" * 80)
    
    offset, size = struct.unpack('<HH', idx_data[0:4])
    face0 = dat_data[offset:offset+size]
    
    # Skip 6-byte header
    pixel_data = face0[6:]
    
    print(f"Data size: {len(pixel_data)} bytes")
    
    # Try different dimensions with planar format
    attempts = [
        (33, 20),
        (32, 20),
        (30, 22),
        (22, 30),
        (40, 16),
        (48, 13),
    ]
    
    palette = make_vga_palette()
    output_dir = Path('../graphics/faces_planar_test')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for w, h in attempts:
        pixels_needed = w * h
        bytes_for_planar = ((pixels_needed + 7) // 8) * 4  # 4 bitplanes
        
        print(f"\nTrying {w}x{h}:")
        print(f"  Pixels: {pixels_needed}")
        print(f"  Bytes needed (planar): {bytes_for_planar}")
        print(f"  Available: {len(pixel_data)}")
        
        if bytes_for_planar <= len(pixel_data):
            result = deinterleave_planar(pixel_data, w, h)
            if result and len(result) == pixels_needed:
                img = Image.new('P', (w, h))
                img.putpalette(palette)
                img.putdata(result)
                
                out_file = output_dir / f"face_00_planar_{w}x{h}.png"
                img.save(out_file)
                print(f"  Saved: {out_file.name}")
                
                # Check if it looks reasonable
                unique = len(set(result))
                print(f"  Unique colors: {unique}")

if __name__ == '__main__':
    try_planar_extraction()
