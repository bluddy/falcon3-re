"""
Hex dump and analyze .MIS mission file format
"""

import sys
import struct

def hex_dump(data, offset=0, length=None):
    """Create formatted hex dump"""
    if length:
        data = data[offset:offset+length]
    else:
        data = data[offset:]
    
    for i in range(0, len(data), 16):
        # Offset
        hex_offset = f"{offset + i:04X}"
        
        # Hex bytes
        hex_bytes = " ".join(f"{b:02X}" for b in data[i:i+16])
        hex_bytes = hex_bytes.ljust(47)  # 16*3-1 = 47
        
        # ASCII representation
        ascii_repr = "".join(chr(b) if 32 <= b < 127 else "." for b in data[i:i+16])
        
        print(f"{hex_offset}  {hex_bytes}  {ascii_repr}")

def analyze_mission_file(filepath):
    """Analyze .MIS mission file structure"""
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print("=" * 80)
    print(f"MISSION FILE: {filepath}")
    print(f"Size: {len(data)} bytes (0x{len(data):X})")
    print("=" * 80)
    print()
    
    # Show full hex dump
    print("FULL HEX DUMP:")
    print("-" * 80)
    hex_dump(data)
    print()
    
    # Try to identify structure
    print("\nSTRUCTURE ANALYSIS:")
    print("-" * 80)
    
    if len(data) >= 4:
        # First few bytes often indicate structure
        header_bytes = data[0:20]
        print(f"First 20 bytes: {' '.join(f'{b:02X}' for b in header_bytes)}")
        print()
        
        # Check if it's a record-based format
        # Pattern: [count] [type] [size] [data]...
        offset = 0
        record_num = 0
        
        print("RECORD STRUCTURE HYPOTHESIS:")
        print(f"{'Offset':<8} {'Byte':<6} {'Word':<8} {'Description'}")
        print("-" * 60)
        
        for i in range(0, min(100, len(data)), 4):
            if i+3 < len(data):
                b0 = data[i]
                b1 = data[i+1]
                word = struct.unpack('<H', data[i:i+2])[0]
                b2 = data[i+2]
                b3 = data[i+3]
                
                print(f"+0x{i:04X}   {b0:02X}     0x{word:04X}   Byte={b0}, Word={word}")
    
    # Look for patterns
    print("\n\nPATTERN ANALYSIS:")
    print("-" * 80)
    
    # Count frequency of bytes
    byte_freq = {}
    for b in data:
        byte_freq[b] = byte_freq.get(b, 0) + 1
    
    print("Most common bytes:")
    for byte_val, count in sorted(byte_freq.items(), key=lambda x: x[1], reverse=True)[:10]:
        pct = count * 100.0 / len(data)
        print(f"  0x{byte_val:02X} ({byte_val:3d}): {count:4d} times ({pct:5.1f}%)")
    
    # Look for repeating patterns (potential array stride)
    print("\nPotential array strides:")
    for stride in [20, 23, 28, 40, 60, 66, 130]:
        matches = 0
        for i in range(0, len(data) - stride):
            if data[i] == data[i + stride] and data[i] != 0:
                matches += 1
        if matches > 0:
            print(f"  Stride {stride:3d}: {matches:3d} matching bytes")

if __name__ == '__main__':
    files = [
        r'C:\Users\ybarnoy\projects\falcon3\game\SQUAD0.MIS',
        r'C:\Users\ybarnoy\projects\falcon3\game\SQUAD1.MIS',
    ]
    
    for filepath in files:
        analyze_mission_file(filepath)
        print("\n\n")
