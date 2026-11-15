"""
Extract PEOPLE.DAT faces using the correct VGA planar RLE format
Based on disassembly of rle_vga_decompressor at 0x88460
"""
import struct
import os
from pathlib import Path

def rle_decompress_planar(data):
    """
    Decompress VGA planar RLE data
    
    Format discovered from disassembly:
    - First 2 bytes: magic number (0x0400)
    - Next 4 bytes: X coordinate (word), Y coordinate (word) - screen position, not dimensions
    - Remaining: width (word), height (word), then RLE compressed data for 4 bit planes
    
    RLE format:
    - Flag byte with bit 7 = 1: Run (low 7 bits = count, next byte = value)
    - Flag byte with bit 7 = 0: Literal (low 7 bits = count, next count bytes are data)
    """
    if len(data) < 10:
        return None, 0, 0
    
    # Skip 6-byte header (magic + X,Y coordinates)
    # These are screen coordinates for where to blit, not image dimensions
    magic = struct.unpack('<H', data[0:2])[0]
    x_coord = struct.unpack('<H', data[2:4])[0]
    y_coord = struct.unpack('<H', data[4:6])[0]
    
    if magic != 0x0400:
        return None, 0, 0
    
    # Read width/height from compressed data
    width, height = struct.unpack('<HH', data[6:10])
    
    print(f"DEBUG: magic=0x{magic:04X}, coords=({x_coord},{y_coord}), dims={width}x{height}")
    
    # Validate dimensions
    if width == 0 or height == 0 or width > 320 or height > 200:
        print(f"DEBUG: Invalid dimensions")
        return None, 0, 0
    
    # Calculate expected output size per plane
    pixels_per_plane = (width // 4) * height  # VGA mode 13h uses 4 pixels per byte in planar mode
    
    # Allocate output buffer for 4 planes
    planes = [bytearray() for _ in range(4)]
    
    # Decompress data for each plane
    pos = 10  # Start after 6-byte header + 4-byte width/height
    for plane_idx in range(4):
        plane_data = bytearray()
        
        # Decompress until we have enough data for this plane
        while len(plane_data) < pixels_per_plane:
            if pos >= len(data):
                break
            
            flag = data[pos]
            pos += 1
            
            if flag & 0x80:  # Run-length encoding
                count = flag & 0x7F
                if pos >= len(data):
                    break
                value = data[pos]
                pos += 1
                plane_data.extend([value] * count)
            else:  # Literal run
                count = flag & 0x7F
                if pos + count > len(data):
                    break
                plane_data.extend(data[pos:pos+count])
                pos += count
        
        planes[plane_idx] = plane_data[:pixels_per_plane]
    
    # Convert planar format to linear VGA format
    # In VGA mode 13h planar, each plane contributes 2 bits per pixel
    # Plane 0 = bits 0-1, Plane 1 = bits 2-3, Plane 2 = bits 4-5, Plane 3 = bits 6-7
    pixels = bytearray(width * height)
    
    bytes_per_line = width // 4
    for y in range(height):
        for x_byte in range(bytes_per_line):
            plane_offset = y * bytes_per_line + x_byte
            
            # Get byte from each plane
            for bit_pair in range(4):  # 4 pixel pairs per byte
                if plane_offset >= len(planes[0]):
                    continue
                
                pixel_val = 0
                for plane_idx in range(4):
                    if plane_offset < len(planes[plane_idx]):
                        plane_byte = planes[plane_idx][plane_offset]
                        # Extract the bit pair for this pixel
                        bit_shift = (3 - bit_pair) * 2
                        bits = (plane_byte >> bit_shift) & 0x03
                        pixel_val |= (bits << (plane_idx * 2))
                
                pixel_offset = y * width + (x_byte * 4 + bit_pair)
                if pixel_offset < len(pixels):
                    pixels[pixel_offset] = pixel_val
    
    return bytes(pixels), width, height

def extract_people():
    """Extract all faces from PEOPLE.DAT"""
    game_dir = Path('../game')
    idx_file = game_dir / 'people.idx'
    dat_file = game_dir / 'people.dat'
    
    # Read index
    with open(idx_file, 'rb') as f:
        idx_data = f.read()
    
    # Read data file
    with open(dat_file, 'rb') as f:
        dat_data = f.read()
    
    # Parse index: pairs of (offset, size) as uint16
    num_records = len(idx_data) // 4
    offsets = [(0, 0)] * (num_records + 1)  # Start, end pairs
    
    for i in range(num_records):
        offset = struct.unpack('<H', idx_data[i*4:(i*4)+2])[0]
        size = struct.unpack('<H', idx_data[i*4+2:(i*4)+4])[0]
        offsets[i] = (offset, offset + size)
    
    # The last entry is implicitly the end of the file
    if num_records > 0:
        last_offset, last_end = offsets[num_records - 1]
        offsets[num_records] = (last_end, len(dat_data))
    
    print(f"Found {num_records} records in PEOPLE.IDX")
    if num_records > 0:
        print(f"First 5 records: {offsets[:5]}")
    
    # Create output directory
    output_dir = Path('graphics/faces_planar')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract each record
    success_count = 0
    for i in range(num_records):
        start, end = offsets[i]
        record_data = dat_data[start:end]
        
        print(f"\nRecord {i}: offset=0x{start:X}, size={len(record_data)} bytes")
        
        # Decompress
        pixels, width, height = rle_decompress_planar(record_data)
        
        if pixels and width > 0 and height > 0:
            print(f"  Decompressed: {width}x{height} = {len(pixels)} pixels")
            
            # Save as raw pixel data
            output_file = output_dir / f'face_{i:02d}_{width}x{height}.raw'
            with open(output_file, 'wb') as f:
                f.write(pixels)
            
            success_count += 1
            print(f"  Saved: {output_file}")
        else:
            print(f"  Failed to decompress")
    
    print(f"\n=== Summary ===")
    print(f"Successfully extracted: {success_count}/{num_records}")
    print(f"Output directory: {output_dir}")

if __name__ == '__main__':
    extract_people()
