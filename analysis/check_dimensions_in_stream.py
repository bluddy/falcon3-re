"""
Check if dimensions are embedded in the compressed stream
"""
import struct

dat = open('../game/people.dat', 'rb').read()

# First record: offset 0, size 666
record = dat[0:666]

print("Checking for dimensions in compressed stream...")
print("="*60)

# Skip 6-byte header
compressed = record[6:]

print(f"Compressed data: {len(compressed)} bytes\n")

# Try reading first 2 words as width/height
if len(compressed) >= 4:
    width = struct.unpack('<H', compressed[0:2])[0]
    height = struct.unpack('<H', compressed[2:4])[0]
    
    print(f"If first 4 bytes are dimensions:")
    print(f"  Width:  0x{width:04X} = {width}")
    print(f"  Height: 0x{height:04X} = {height}")
    print(f"  Total pixels: {width * height}")
    
    if width > 0 and width <= 320 and height > 0 and height <= 200:
        print("  ✓ Plausible!")
        
        # Try decompressing from byte 4 onwards
        rle_data = compressed[4:]
        print(f"\n  RLE data starts at offset 4: {len(rle_data)} bytes")
        print(f"  First 10 RLE bytes: {' '.join(f'{b:02X}' for b in rle_data[:10])}")
    else:
        print("  ✗ Not plausible")

print("\n" + "="*60)
print("But wait - let's check if this is VGA planar format!")
print("="*60)

# The disassembly shows the decompressor writes to VGA planes
# Maybe dimensions are passed differently, or the format is something else

# Let's look at what the menu loader does
print("\nThe idx_dat_loader at 0x139909 calls:")
print("  1. File I/O to load .IDX and .DAT")
print("  2. graphics_record_processor at 0x2BFC3")
print("  3. Which jumps to an OVERLAY at r02_farptr_pair_call_entry")
print("\nThe real decompressor is in the OVERLAY, not at 0x88460!")
print("0x88460 is for VGA planar blitting - different format.")
