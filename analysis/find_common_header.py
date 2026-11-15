"""
Find where the common header/template ends and unique pixel data begins.
"""
import struct
from pathlib import Path

def find_unique_data_start():
    """Find where faces start differing."""
    
    with open('../game/PEOPLE.IDX', 'rb') as f:
        idx_data = f.read()
    
    with open('../game/PEOPLE.DAT', 'rb') as f:
        dat_data = f.read()
    
    print("Finding common header length in PEOPLE.DAT")
    print("=" * 80)
    
    num_entries = len(idx_data) // 4
    
    # Load all faces
    faces = []
    for i in range(num_entries):
        pos = i * 4
        offset, size = struct.unpack('<HH', idx_data[pos:pos+4])
        data = dat_data[offset:offset+size]
        faces.append(data)
    
    # Find common prefix length for groups with same val1/val2
    groups = {}
    for i, face in enumerate(faces):
        if len(face) < 6:
            continue
        val1 = struct.unpack('<H', face[2:4])[0]
        val2 = struct.unpack('<H', face[4:6])[0]
        key = (val1, val2)
        if key not in groups:
            groups[key] = []
        groups[key].append((i, face))
    
    print(f"Found {len(groups)} groups with same val1/val2:")
    for key, members in groups.items():
        print(f"\n  Group ({key[0]}, {key[1]}): {len(members)} faces")
        
        if len(members) < 2:
            continue
        
        # Find common prefix
        first_face = members[0][1]
        common_len = 0
        for pos in range(len(first_face)):
            # Check if all faces have same byte at this position
            byte_val = first_face[pos]
            if all(len(face[1]) > pos and face[1][pos] == byte_val for face in members):
                common_len = pos + 1
            else:
                break
        
        print(f"    Common prefix: {common_len} bytes")
        print(f"    Hex: {first_face[:common_len].hex()}")
        
        # Show where unique data starts
        print(f"    Unique data starts at byte {common_len}")
        
        # Calculate actual image sizes
        for idx, face in members[:3]:
            unique_size = len(face) - common_len
            print(f"      Face {idx:2}: total={len(face):3}B, unique={unique_size:3}B")
            
            # Try to find dimensions
            for h in range(15, 30):
                if unique_size % h == 0:
                    w = unique_size // h
                    if 20 <= w <= 45:
                        print(f"                possible: {w}x{h}")
                        break

if __name__ == '__main__':
    find_unique_data_start()
