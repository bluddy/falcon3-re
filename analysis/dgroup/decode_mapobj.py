#!/usr/bin/env python3
"""
Decode MAPOBJ.ISR file structure.

Hypothesis: MAPOBJ contains the actual 3D coordinate data that ISLDAT references.
ISLDAT stores indices/offsets pointing into MAPOBJ coordinate arrays.

File appears to have:
- Header with 0xFF padding
- Offset table starting around 0x48
- Data sections at various offsets
"""

import struct
import sys

def decode_mapobj(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f"=== MAPOBJ File: {filename} ===")
    print(f"Total size: {len(data)} bytes (0x{len(data):X})")
    print()
    
    # Find first non-FF byte
    first_data = 0
    for i in range(len(data)):
        if data[i] != 0xFF:
            first_data = i
            break
    
    print(f"Data starts at offset: {first_data} (0x{first_data:X})")
    print()
    
    # Dump header area (first non-FF section)
    print("=== HEADER AREA (0x48-0xC0) ===")
    for offset in range(0x48, 0xC0, 16):
        if offset >= len(data):
            break
        hex_bytes = ' '.join(f'{b:02X}' for b in data[offset:offset+16])
        
        # Try to interpret as dword offsets
        if offset + 15 < len(data):
            dw1 = struct.unpack('<I', data[offset:offset+4])[0]
            dw2 = struct.unpack('<I', data[offset+4:offset+8])[0]
            dw3 = struct.unpack('<I', data[offset+8:offset+12])[0]
            dw4 = struct.unpack('<I', data[offset+12:offset+16])[0]
            
            # Check if these look like offsets (within file size)
            if dw1 != 0xFFFFFFFF and dw1 < len(data):
                print(f"  {offset:04X}: {hex_bytes}")
                print(f"        -> {dw1:08X} ({dw1}), {dw2:08X} ({dw2}), {dw3:08X} ({dw3}), {dw4:08X} ({dw4})")
            else:
                print(f"  {offset:04X}: {hex_bytes}")
        else:
            print(f"  {offset:04X}: {hex_bytes}")
    print()
    
    # Check if offset 0x7008 (first ISLDAT pointer) exists
    check_offsets = [0x7008, 0x7808, 0x8008, 0x8A08, 0x9408]
    print("=== CHECKING ISLDAT POINTER OFFSETS ===")
    for offset in check_offsets:
        if offset < len(data):
            # Read as potential 12-byte point structure (3 x int32)
            if offset + 11 < len(data):
                x_low = struct.unpack('<H', data[offset:offset+2])[0]
                x_high = struct.unpack('<H', data[offset+2:offset+4])[0]
                y_low = struct.unpack('<H', data[offset+4:offset+6])[0]
                y_high = struct.unpack('<H', data[offset+6:offset+8])[0]
                z_low = struct.unpack('<H', data[offset+8:offset+10])[0]
                z_high = struct.unpack('<H', data[offset+10:offset+12])[0]
                
                x = (x_high << 16) | x_low
                y = (y_high << 16) | y_low
                z = (z_high << 16) | z_low
                
                # Convert to signed
                if x >= 0x80000000:
                    x -= 0x100000000
                if y >= 0x80000000:
                    y -= 0x100000000
                if z >= 0x80000000:
                    z -= 0x100000000
                
                hex_dump = ' '.join(f'{b:02X}' for b in data[offset:offset+12])
                print(f"  {offset:04X} ({offset}): {hex_dump}")
                print(f"        X={x:10d} (0x{x & 0xFFFFFFFF:08X})")
                print(f"        Y={y:10d} (0x{y & 0xFFFFFFFF:08X})")
                print(f"        Z={z:10d} (0x{z & 0xFFFFFFFF:08X})")
                print()
        else:
            print(f"  {offset:04X} - BEYOND FILE SIZE")
    
    # Look for patterns in first data section
    if 0x100 < len(data):
        print("=== DATA SECTION @ 0x100 (256) ===")
        print("First 64 bytes:")
        for i in range(0, min(64, len(data) - 0x100), 16):
            offset = 0x100 + i
            hex_bytes = ' '.join(f'{b:02X}' for b in data[offset:offset+16])
            print(f"  {offset:04X}: {hex_bytes}")

if __name__ == '__main__':
    decode_mapobj('game/israel_theater/MAPOBJ.ISR')
