#!/usr/bin/env python3
"""
Decode ISLDAT.ISR file structure based on loader analysis.

From isldat_state_load @ 0x12FC4:
Header (18 bytes starting at file offset 0):
  word[0] @ +0: Size of data to read (NOT point count)
  word[1] @ +2: word_11C16 - offset to coastline index table?
  word[2] @ +4: word_11C18 - offset to another index table
  word[3] @ +6: word_11C1A - offset to pointer table
  byte[4] @ +8: byte_11C0A - some flag/count

From pos_neighbor_norm_scan @ 0x14B4F:
The header offsets are used to build index addresses:
  si = (grid_coord >> 2) + word_11C16 + word_11CC6
  al = [si]  ; load index byte
  si = (al * 2) + word_11C1A  ; index into pointer table
  si = [si]  ; load pointer to record list
  Loop: ax = [si], si += 2
        if ax == 0xFFFF: break
        else: process point at ax

Data structure appears to be:
1. Header (18 bytes)
2. Coastline index grid (byte per cell)
3. Another index grid (for different feature type)
4. Pointer table (word pointers)
5. Coastline point lists (terminated with 0xFFFF)
"""

import struct
import sys

def decode_isldat(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f"=== ISLDAT File: {filename} ===")
    print(f"Total size: {len(data)} bytes (0x{len(data):X})")
    print()
    
    # Parse header (18 bytes = 9 words)
    print("=== HEADER (18 bytes) ===")
    header = struct.unpack('<9H', data[0:18])
    
    data_size = header[0]
    offset_table1 = header[1]  # word_11C16
    offset_table2 = header[2]  # word_11C18
    offset_ptrs = header[3]    # word_11C1A
    flag_byte = data[8]        # byte_11C0A
    
    print(f"word[0] data_size:    0x{data_size:04X} ({data_size})")
    print(f"word[1] offset_table1: 0x{offset_table1:04X} ({offset_table1}) <- word_11C16")
    print(f"word[2] offset_table2: 0x{offset_table2:04X} ({offset_table2}) <- word_11C18")
    print(f"word[3] offset_ptrs:   0x{offset_ptrs:04X} ({offset_ptrs}) <- word_11C1A")
    print(f"byte[8] flag:          0x{flag_byte:02X} ({flag_byte})")
    print(f"word[4] = 0x{header[4]:04X}")
    print(f"word[5] = 0x{header[5]:04X}")
    print(f"word[6] = 0x{header[6]:04X}")
    print(f"word[7] = 0x{header[7]:04X}")
    print(f"word[8] = 0x{header[8]:04X}")
    print()
    
    # Data starts at offset 58 (0x3A) based on loader
    data_start = 58
    print(f"=== DATA SECTION (starts at offset {data_start} / 0x{data_start:02X}) ===")
    
    # Dump first 128 bytes of data section
    print("First 128 bytes of data:")
    for i in range(0, min(128, len(data) - data_start), 16):
        offset = data_start + i
        hex_bytes = ' '.join(f'{b:02X}' for b in data[offset:offset+16])
        ascii_bytes = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[offset:offset+16])
        print(f"  {offset:04X}: {hex_bytes:<48} {ascii_bytes}")
    print()
    
    # Try to interpret the index tables
    print("=== INDEX TABLE ANALYSIS ===")
    
    # Table 1 appears at offset_table1 from data_start
    if offset_table1 < len(data) - data_start:
        abs_offset = data_start + offset_table1
        print(f"Table1 @ {abs_offset} (0x{abs_offset:X}), size ~{offset_table2 - offset_table1} bytes:")
        for i in range(min(32, offset_table2 - offset_table1)):
            idx = abs_offset + i
            if idx < len(data):
                print(f"  [{i:02}] = 0x{data[idx]:02X} ({data[idx]})")
        print()
    
    # Pointer table at offset_ptrs
    if offset_ptrs < len(data) - data_start:
        abs_offset = data_start + offset_ptrs
        print(f"Pointer Table @ {abs_offset} (0x{abs_offset:X}):")
        ptr_count = min(16, (len(data) - abs_offset) // 2)
        for i in range(ptr_count):
            idx = abs_offset + i * 2
            if idx + 1 < len(data):
                ptr = struct.unpack('<H', data[idx:idx+2])[0]
                print(f"  ptr[{i:02}] = 0x{ptr:04X} ({ptr})")
        print()
    
    # Look for 0xFFFF terminators (coastline list ends)
    print("=== 0xFFFF TERMINATORS (coastline list ends) ===")
    terminator_count = 0
    for i in range(data_start, len(data) - 1, 2):
        if data[i] == 0xFF and data[i+1] == 0xFF:
            terminator_count += 1
            if terminator_count <= 10:
                print(f"  Terminator at offset {i} (0x{i:04X})")
    print(f"Total terminators found: {terminator_count}")
    print()

if __name__ == '__main__':
    decode_isldat('game/israel_theater/ISLDAT.ISR')
