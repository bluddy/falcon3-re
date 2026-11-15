"""
Try to extract pilot faces from PEOPLE.DAT.
Hypothesis: Same 6-byte header as .DAT files (00 04 + width + height),
but data might be uncompressed since faces don't compress well with RLE.
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

def extract_people_faces():
    """Extract faces from PEOPLE.DAT."""
    
    # Parse index
    with open('../game/PEOPLE.IDX', 'rb') as f:
        idx_data = f.read()
    
    with open('../game/PEOPLE.DAT', 'rb') as f:
        dat_data = f.read()
    
    print("Extracting pilot faces from PEOPLE.DAT")
    print("=" * 80)
    
    num_entries = len(idx_data) // 4
    output_dir = Path('../graphics/faces')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    palette = make_grey_palette()
    
    extracted = 0
    
    for i in range(num_entries):
        pos = i * 4
        offset, size = struct.unpack('<HH', idx_data[pos:pos+4])
        
        data = dat_data[offset:offset+size]
        
        if len(data) < 6:
            print(f"Face {i:2}: Too small ({len(data)} bytes)")
            continue
        
        # Parse header
        magic = struct.unpack('<H', data[0:2])[0]
        width = struct.unpack('<H', data[2:4])[0]
        height = struct.unpack('<H', data[4:6])[0]
        
        pixel_data = data[6:]
        
        print(f"Face {i:2}: magic=0x{magic:04X}, header says {width}x{height}, "
              f"data={len(pixel_data)} bytes", end='')
        
        # Check if it's the right magic
        if magic != 0x0400:
            print(f" - WRONG MAGIC")
            continue
        
        # Try different interpretations
        # 630-690 bytes suggests faces around 25-35 pixels per side
        attempts = [
            (33, 20, f"33x20"),
            (30, 22, f"30x22"),  
            (26, 26, f"26x26 square"),
            (32, 20, f"32x20"),
            (35, 19, f"35x19"),
            # Try calculated from actual data size
        ]
        
        # Add calculated possibilities
        for h in [18, 19, 20, 21, 22, 23, 24, 25, 26]:
            if len(pixel_data) % h == 0:
                w = len(pixel_data) // h
                if 20 <= w <= 45:
                    attempts.append((w, h, f"calculated {w}x{h}"))
        
        success = False
        for w, h, desc in attempts:
            expected_pixels = w * h
            if expected_pixels == len(pixel_data):
                print(f" - MATCH! {w}x{h} ({desc})")
                
                # Create image
                img = Image.new('P', (w, h))
                img.putpalette(palette)
                img.putdata(pixel_data)
                
                out_file = output_dir / f"face_{i:02d}_{w}x{h}.png"
                img.save(out_file)
                
                extracted += 1
                success = True
                break
        
        if not success:
            # Show what sizes would work
            possible = []
            for h in range(10, 50):
                if len(pixel_data) % h == 0:
                    w = len(pixel_data) // h
                    if 10 <= w <= 50:
                        possible.append(f"{w}x{h}")
            if possible:
                print(f" - Possible: {', '.join(possible[:5])}")
            else:
                print(f" - No match")
    
    print("\n" + "=" * 80)
    print(f"Extracted {extracted} / {num_entries} faces to {output_dir}/")

if __name__ == '__main__':
    extract_people_faces()
