"""
Extract all 40 pilot faces from PEOPLE.DAT
"""
from PIL import Image
import struct
from pathlib import Path

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

def rle_decompress(data):
    """Decompress RLE data (no dimension header in stream)"""
    output = bytearray()
    pos = 0
    
    while pos < len(data):
        flag = data[pos]
        pos += 1
        
        if flag == 0:  # Stop marker
            break
        
        if flag & 0x80:  # Run-length encoding
            count = flag & 0x7F
            if pos >= len(data):
                break
            value = data[pos]
            pos += 1
            output.extend([value] * count)
        else:  # Literal run
            count = flag & 0x7F
            if pos + count > len(data):
                break
            output.extend(data[pos:pos+count])
            pos += count
    
    return bytes(output)

def extract_faces():
    """Extract all faces from PEOPLE.DAT"""
    game_dir = Path('../game')
    idx_file = game_dir / 'people.idx'
    dat_file = game_dir / 'people.dat'
    
    # Read files
    with open(idx_file, 'rb') as f:
        idx_data = f.read()
    
    with open(dat_file, 'rb') as f:
        dat_data = f.read()
    
    # Parse index: pairs of (offset, size) as uint16
    num_records = len(idx_data) // 4
    records = []
    
    for i in range(num_records):
        offset = struct.unpack('<H', idx_data[i*4:(i*4)+2])[0]
        size = struct.unpack('<H', idx_data[i*4+2:(i*4)+4])[0]
        records.append((offset, size))
    
    print(f"Found {num_records} faces in PEOPLE.DAT\n")
    
    # Create output directory
    output_dir = Path('graphics/faces')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare palette
    vga_palette = get_vga_palette()
    
    # Face dimensions (determined from testing)
    WIDTH = 33
    HEIGHT = 37
    
    # Extract each face
    success_count = 0
    for i in range(num_records):
        offset, size = records[i]
        end = offset + size
        record_data = dat_data[offset:end]
        
        if len(record_data) < 6:
            print(f"Face {i:02d}: Too small ({len(record_data)} bytes)")
            continue
        
        # Parse header
        magic = struct.unpack('<H', record_data[0:2])[0]
        x_coord = struct.unpack('<H', record_data[2:4])[0]
        y_coord = struct.unpack('<H', record_data[4:6])[0]
        
        if magic != 0x0400:
            print(f"Face {i:02d}: Invalid magic 0x{magic:04X}")
            continue
        
        # Decompress RLE data (skip 6-byte header)
        compressed_data = record_data[6:]
        pixels = rle_decompress(compressed_data)
        
        expected_pixels = WIDTH * HEIGHT
        if len(pixels) != expected_pixels:
            print(f"Face {i:02d}: Got {len(pixels)} pixels, expected {expected_pixels}")
            # Try to use it anyway if close
            if len(pixels) < expected_pixels:
                pixels += b'\x00' * (expected_pixels - len(pixels))
            else:
                pixels = pixels[:expected_pixels]
        
        # Create image
        img = Image.frombytes('P', (WIDTH, HEIGHT), pixels)
        img.putpalette(vga_palette)
        
        # Save as PNG
        output_file = output_dir / f'face_{i:02d}.png'
        img.save(output_file)
        
        print(f"Face {i:02d}: Saved {WIDTH}x{HEIGHT} at screen pos ({x_coord},{y_coord})")
        success_count += 1
    
    print(f"\n=== Summary ===")
    print(f"Successfully extracted: {success_count}/{num_records} faces")
    print(f"Output directory: {output_dir}")
    
    # Create a contact sheet
    if success_count > 0:
        print("\nCreating contact sheet...")
        cols = 10
        rows = (success_count + cols - 1) // cols
        
        sheet = Image.new('P', (WIDTH * cols, HEIGHT * rows), 0)
        sheet.putpalette(vga_palette)
        
        for i in range(success_count):
            face_file = output_dir / f'face_{i:02d}.png'
            if face_file.exists():
                face = Image.open(face_file)
                x = (i % cols) * WIDTH
                y = (i // cols) * HEIGHT
                sheet.paste(face, (x, y))
        
        sheet_file = output_dir / 'all_faces_sheet.png'
        sheet.save(sheet_file)
        print(f"Contact sheet saved: {sheet_file}")

if __name__ == '__main__':
    extract_faces()
