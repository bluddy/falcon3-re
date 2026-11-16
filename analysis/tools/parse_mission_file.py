"""
Parse .MIS mission file format
Based on observed patterns from SQUAD0.MIS and SQUAD1.MIS
"""

import struct
import sys

def parse_mission_file(filepath):
    """Parse .MIS mission file structure"""
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print("=" * 80)
    print(f"MISSION FILE: {filepath}")
    print(f"Size: {len(data)} bytes (0x{len(data):X})")
    print("=" * 80)
    print()
    
    offset = 0
    
    # Header analysis
    print("HEADER SECTION:")
    print("-" * 80)
    
    if len(data) >= 12:
        # First few bytes
        b0 = data[0]
        b1 = data[1]
        word0 = struct.unpack('<H', data[0:2])[0]
        
        print(f"+0x0000: {b0:3d} (0x{b0:02X}) = byte[0]")
        print(f"+0x0001: {b1:3d} (0x{b1:02X}) = byte[1]")
        print(f"         Word: {word0} (0x{word0:04X})")
        print()
        
        b2 = data[2]
        b3 = data[3]
        print(f"+0x0002: {b2:3d} (0x{b2:02X}) = byte[2]")
        print(f"+0x0003: {b3:3d} (0x{b3:02X}) = byte[3]")
        print()
        
        # Next several bytes
        for i in range(4, 12):
            b = data[i]
            print(f"+0x{i:04X}: {b:3d} (0x{b:02X}) = byte[{i}]")
        
        print()
        offset = 12
    
    # Look for array of mission records
    print("\nMISSION RECORDS SECTION:")
    print("-" * 80)
    
    # Pattern observed: sequences of [index byte] [00] [data byte] [data byte] [00] [flags byte] [80/81]
    # This looks like mission slot records
    
    record_count = 0
    current_offset = offset
    
    print(f"{'Offset':<8} {'Idx':<5} {'B2':<5} {'B3':<5} {'B4':<5} {'Flags':<7} {'Hex':<20}")
    print("-" * 70)
    
    while current_offset < len(data) - 6:
        # Check if this looks like a mission record
        idx = data[current_offset]
        b1 = data[current_offset + 1]
        b2 = data[current_offset + 2]
        b3 = data[current_offset + 3]
        b4 = data[current_offset + 4]
        flags = data[current_offset + 5]
        
        # Stop if we hit a long run of zeros or obvious end marker
        if (idx == 0 and b1 == 0 and b2 == 0 and b3 == 0) or current_offset > 0x100:
            break
        
        # Check for pattern: [idx] [00] [data] [data] [00/data] [flags with high bit]
        if b1 == 0x00 and (flags & 0x80):
            hex_str = " ".join(f"{data[current_offset+i]:02X}" for i in range(6))
            print(f"+0x{current_offset:04X}  {idx:3d}   {b2:3d}   {b3:3d}   {b4:3d}   0x{flags:02X}    {hex_str}")
            record_count += 1
            current_offset += 6
        elif b1 == 0x00:
            # Might be different record type
            hex_str = " ".join(f"{data[current_offset+i]:02X}" for i in range(6))
            print(f"+0x{current_offset:04X}  {idx:3d}   {b2:3d}   {b3:3d}   {b4:3d}   0x{flags:02X}    {hex_str} (no flag)")
            record_count += 1
            current_offset += 6
        else:
            current_offset += 1
    
    print(f"\nFound {record_count} mission records")
    print(f"Records end at offset: 0x{current_offset:04X}")
    
    # Analyze remaining data
    print("\n\nREMAINING DATA SECTIONS:")
    print("-" * 80)
    
    remaining = data[current_offset:]
    print(f"Remaining bytes: {len(remaining)} (0x{len(remaining):X})")
    print()
    
    # Look for large structures
    # Pattern: 20-byte or 23-byte records?
    
    # Try 20-byte records
    print("Attempting 20-byte record parse:")
    offset_rem = current_offset
    rec_num = 0
    
    while offset_rem + 20 <= len(data) and rec_num < 20:
        rec_data = data[offset_rem:offset_rem+20]
        
        # Check if this looks like a mission slot
        label_0 = rec_data[0]
        label_1 = rec_data[1]
        field_2 = struct.unpack('<H', rec_data[2:4])[0]
        
        # Only show non-zero records
        if any(b != 0 for b in rec_data[:10]):
            hex_preview = " ".join(f"{rec_data[i]:02X}" for i in range(min(10, len(rec_data))))
            
            label_str = ""
            if 32 <= label_0 < 127:
                label_str = f" ('{chr(label_0)}')"
            
            print(f"Record {rec_num:2d} @ 0x{offset_rem:04X}:")
            print(f"  +0x00: 0x{label_0:02X} = {label_0:3d}{label_str}")
            print(f"  +0x01: 0x{label_1:02X} = {label_1:3d}")
            print(f"  +0x02: 0x{field_2:04X} = {field_2:5d}")
            print(f"  First 10 bytes: {hex_preview}")
            print()
        
        rec_num += 1
        offset_rem += 20
    
    # Statistics
    print("\nFILE STATISTICS:")
    print("-" * 80)
    print(f"Total size: {len(data)} bytes")
    print(f"Header: ~{offset} bytes")
    print(f"Mission records: {record_count} records (~{record_count*6} bytes)")
    print(f"Remaining: {len(data) - offset - record_count*6} bytes")

if __name__ == '__main__':
    files = [
        r'C:\Users\ybarnoy\projects\falcon3\game\SQUAD0.MIS',
        r'C:\Users\ybarnoy\projects\falcon3\game\SQUAD1.MIS',
    ]
    
    for filepath in files:
        try:
            parse_mission_file(filepath)
            print("\n\n")
        except Exception as e:
            print(f"ERROR parsing {filepath}: {e}")
            import traceback
            traceback.print_exc()
