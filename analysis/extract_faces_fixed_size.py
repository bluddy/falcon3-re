"""
Try extracting faces assuming fixed dimensions per group.
"""
import struct
from pathlib import Path
from PIL import Image

def make_grey_palette():
    """Create grey palette for menu graphics."""
    palette = []
    palette.append((0, 0, 0))  # 0: Black
    
    # EGA colors
    ega = [(0,0,170), (0,170,0), (0,170,170), (170,0,0), (170,0,170),
           (170,85,0), (170,170,170), (85,85,85), (85,85,255), (85,255,85),
           (85,255,255), (255,85,85), (255,85,255), (255,255,85), (255,255,255)]
    palette.extend(ega)
    
    # Grey ramp for 16-31
    for i in range(16):
        grey = int(32 + i * 14)
        palette.append((grey, grey, grey))
    
    # RGB cube  
    for r in range(6):
        for g in range(6):
            for b in range(6):
                if len(palette) < 232:
                    palette.append((r * 51, g * 51, b * 51))
    
    # Greyscale
    for i in range(24):
        grey = int(8 + i * 10.3)
        palette.append((grey, grey, grey))
    
    flat = []
    for r, g, b in palette:
        flat.extend([r, g, b])
    return flat

def extract_faces_fixed():
    """Extract faces assuming fixed size per coordinate group."""
    
    with open('../game/PEOPLE.IDX', 'rb') as f:
        idx_data = f.read()
    
    with open('../game/PEOPLE.DAT', 'rb') as f:
        dat_data = f.read()
    
    print("Extracting faces with FIXED dimensions per group")
    print("=" * 80)
    
    num_entries = len(idx_data) // 4
    output_dir = Path('../graphics/faces_fixed')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Clear directory
    for old in output_dir.glob('*.png'):
        old.unlink()
    
    palette = make_grey_palette()
    
    # Try different fixed dimensions for each group
    group_dims = {
        (78, 160): [(33, 20), (30, 22), (22, 30)],  # Try these dimensions
        (78, 168): [(32, 20), (37, 18), (35, 19)],
        (58, 176): [(25, 19), (19, 25), (32, 15)],
    }
    
    extracted = 0
    
    for i in range(num_entries):
        pos = i * 4
        offset, size = struct.unpack('<HH', idx_data[pos:pos+4])
        
        data = dat_data[offset:offset+size]
        
        if len(data) < 6:
            continue
        
        # Parse header
        magic = struct.unpack('<H', data[0:2])[0]
        x_coord = struct.unpack('<H', data[2:4])[0]
        y_coord = struct.unpack('<H', data[4:6])[0]
        
        if magic != 0x0400:
            continue
        
        coord_key = (x_coord, y_coord)
        
        if coord_key not in group_dims:
            print(f"Face {i:2}: Unknown group ({x_coord},{y_coord})")
            continue
        
        # Try each possible dimension for this group
        pixel_data = data[6:]
        
        for w, h in group_dims[coord_key]:
            expected = w * h
            if len(pixel_data) >= expected:
                # Extract exactly w*h pixels
                face_pixels = pixel_data[:expected]
                
                try:
                    img = Image.new('P', (w, h))
                    img.putpalette(palette)
                    img.putdata(face_pixels)
                    
                    out_file = output_dir / f"face_{i:02d}_{w}x{h}_try.png"
                    img.save(out_file)
                    
                    print(f"Face {i:2}: {w}x{h} extracted ({len(pixel_data)} bytes available)")
                    extracted += 1
                    break  # Take first match
                except Exception as e:
                    continue
    
    print("\n" + "=" * 80)
    print(f"Extracted {extracted} / {num_entries} faces (with fixed sizes)")
    print(f"Output: {output_dir}/")
    print("\nNote: Multiple attempts saved as *_try.png - compare to see which looks best")

if __name__ == '__main__':
    extract_faces_fixed()
