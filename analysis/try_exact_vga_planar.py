"""
Implement EXACT VGA planar RLE decompressor from disassembly at 0x88460
"""
import struct

def rle_decompress_exact_planar(data):
    """
    Exact implementation of decompressor at 0x88460
    
    Input data format (from [SI]):
      [0:2] width (word) - in pixels
      [2:4] height (word) - in pixels  
      [4:...] RLE compressed data for 4 bit planes
    """
    if len(data) < 4:
        return None, 0, 0
    
    # Read width/height (0x88473-0x88477: lodsw; mov bx,ax; lodsw; mov bp,ax)
    width = struct.unpack('<H', data[0:2])[0]
    height = struct.unpack('<H', data[2:4])[0]
    
    print(f"Width={width} (0x{width:04X}), Height={height} (0x{height:04X})")
    
    # Validate
    if width == 0 or height == 0 or width > 320 or height > 200:
        print(f"  Invalid dimensions!")
        return None, 0, 0
    
    # 0x88484-0x88486: shr bx,1; shr bx,1 
    # Width in bytes = width / 4 (VGA planar, 4 pixels per byte)
    width_bytes = width // 4
    
    print(f"Width in bytes: {width_bytes}")
    print(f"Expected output per plane: {width_bytes * height} bytes")
    
    # Decompress 4 bit planes
    planes = []
    pos = 4  # Start after width/height
    
    # 0x88488-0x884CD: Loop through 4 planes (al starts at 1, shifts left each iteration)
    for plane_idx in range(4):
        plane_data = bytearray()
        
        print(f"\nPlane {plane_idx}:")
        
        # Decompress this plane
        # 0x8848C-0x884C0: For each scanline (bp = height)
        for y in range(height):
            # 0x8848E: mov bp,bx  (bp = width_bytes, countdown)
            bytes_remaining = width_bytes
            
            # Decompress one scanline
            while bytes_remaining > 0:
                if pos >= len(data):
                    print(f"  Plane {plane_idx}, line {y}: RAN OUT OF DATA at pos {pos}")
                    break
                
                # 0x88492: lodsb (load flag byte)
                flag = data[pos]
                pos += 1
                
                # 0x88493: test al, 80h
                if flag & 0x80:
                    # Run-length: 0x88497-0x884A8
                    # and al, 7Fh; mov cl,al; sub bp,cx; lodsb; mov ah,al
                    count = flag & 0x7F
                    if pos >= len(data):
                        break
                    value = data[pos]
                    pos += 1
                    
                    # Output 'count' bytes of 'value'
                    # 0x884A0-0x884A8: shr cx,1; rep stosw; adc cx,cx; rep stosb
                    plane_data.extend([value] * count)
                    bytes_remaining -= count
                else:
                    # Literal: 0x884AA-0x884B4
                    # mov cl,al; sub bp,cx; shr cx,1; rep movsw; adc cx,cx; rep movsb
                    count = flag & 0x7F
                    if pos + count > len(data):
                        break
                    plane_data.extend(data[pos:pos+count])
                    pos += count
                    bytes_remaining -= count
                
                # 0x884B6: or bp,bp; jg loc_88492
                if bytes_remaining <= 0:
                    break
            
            if pos >= len(data):
                break
        
        planes.append(bytes(plane_data))
        print(f"  Decompressed {len(plane_data)} bytes (expected {width_bytes * height})")
    
    # Now convert from VGA planar to linear format
    # In VGA mode, pixels are stored with bit planes
    # Each byte in a plane represents 1 bit of 8 pixels
    pixels = bytearray(width * height)
    
    for y in range(height):
        for x_byte in range(width_bytes):
            plane_offset = y * width_bytes + x_byte
            
            # Each byte represents 8 pixels (1 bit per pixel per plane)
            for bit in range(8):
                pixel_x = x_byte * 8 + bit
                if pixel_x >= width:
                    continue
                
                # Build pixel value from 4 planes (4 bits)
                pixel_val = 0
                for plane_idx in range(4):
                    if plane_offset < len(planes[plane_idx]):
                        byte_val = planes[plane_idx][plane_offset]
                        bit_val = (byte_val >> (7 - bit)) & 1
                        pixel_val |= (bit_val << plane_idx)
                
                pixel_offset = y * width + pixel_x
                if pixel_offset < len(pixels):
                    pixels[pixel_offset] = pixel_val
    
    return bytes(pixels), width, height

# Test on first face
dat = open('../game/people.dat', 'rb').read()
record = dat[6:666]  # Skip 6-byte file header

print("Attempting exact planar RLE decompression...")
print("="*60)
pixels, w, h = rle_decompress_exact_planar(record)

if pixels:
    print(f"\n SUCCESS! Decompressed {len(pixels)} pixels as {w}x{h}")
    
    # Save it
    with open('exact_planar_face.raw', 'wb') as f:
        f.write(pixels)
    print("Saved to exact_planar_face.raw")
else:
    print("\nFailed")
