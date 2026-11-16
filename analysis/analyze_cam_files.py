#!/usr/bin/env python3
"""
Analyze .CAM campaign file format.
"""

import os
import struct

def analyze_cam_file(filename):
    """Analyze a .CAM file structure."""
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f"{'='*80}")
    print(f"Analyzing: {os.path.basename(filename)}")
    print(f"Size: {len(data)} bytes")
    print(f"{'='*80}\n")
    
    # Show first 256 bytes in hex dump format
    print("First 256 bytes:")
    for offset in range(0, min(256, len(data)), 16):
        hex_bytes = ' '.join(f'{b:02X}' for b in data[offset:offset+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[offset:offset+16])
        print(f"  {offset:04X}: {hex_bytes:<47}  {ascii_str}")
    print()
    
    # Try to identify structure patterns
    print("Structure Analysis:")
    print()
    
    # Byte 0-3: Likely header or version
    print(f"  [0x0000-0x0003]: {' '.join(f'{data[i]:02X}' for i in range(4))}")
    print()
    
    # Look for repeating patterns (potential records)
    # Check for 66-byte (0x42) pilot records
    pilot_size = 0x42  # 66 bytes
    print(f"Checking for {pilot_size}-byte pilot records...")
    
    # .CAM files are 11828 bytes
    # Let's see if there's a pattern
    
    # Based on .SQU files, we know:
    # - Header: 60 bytes
    # - 30 pilots: 30 * 66 = 1980 bytes
    # - 10 extended: 10 * 66 = 660 bytes  
    # - Footer: 3 bytes
    # Total: 2703 bytes
    
    # .CAM might have multiple missions or squadrons
    # 11828 / 2703 = 4.37 (not an exact fit)
    
    # Let's look for squadron-sized chunks
    print(f"  File size: {len(data)} bytes")
    print(f"  11828 / 66 = {11828 / 66:.2f} (potential 66-byte records)")
    print(f"  11828 / 130 = {11828 / 130:.2f} (potential 130-byte flight records)")
    print()
    
    # Look for 0xFF markers (empty pilot slots)
    print("Looking for 0xFF markers (empty slots):")
    ff_positions = [i for i, b in enumerate(data) if b == 0xFF]
    print(f"  Found {len(ff_positions)} 0xFF bytes")
    if ff_positions:
        # Show first 20 positions
        for pos in ff_positions[:20]:
            context = data[max(0, pos-2):min(len(data), pos+3)]
            hex_context = ' '.join(f'{b:02X}' for b in context)
            print(f"    {pos:04X}: ...{hex_context}...")
    print()
    
    return data

def compare_cam_files(file1, file2):
    """Compare two .CAM files to find differences."""
    with open(file1, 'rb') as f:
        data1 = f.read()
    with open(file2, 'rb') as f:
        data2 = f.read()
    
    print(f"\n{'='*80}")
    print(f"Comparing {os.path.basename(file1)} vs {os.path.basename(file2)}")
    print(f"{'='*80}\n")
    
    if len(data1) != len(data2):
        print(f"WARNING: Different sizes - {len(data1)} vs {len(data2)} bytes\n")
    
    # Find all differences
    diffs = []
    for i in range(min(len(data1), len(data2))):
        if data1[i] != data2[i]:
            diffs.append(i)
    
    print(f"Found {len(diffs)} different bytes")
    print()
    
    if diffs:
        print("First 50 differences:")
        for diff_pos in diffs[:50]:
            print(f"  {diff_pos:04X}: {data1[diff_pos]:02X} -> {data2[diff_pos]:02X}")
        
        # Show difference ranges
        print("\nDifference ranges:")
        if diffs:
            start = diffs[0]
            end = diffs[0]
            
            for pos in diffs[1:]:
                if pos == end + 1:
                    end = pos
                else:
                    print(f"  {start:04X}-{end:04X} ({end-start+1} bytes)")
                    start = pos
                    end = pos
            
            print(f"  {start:04X}-{end:04X} ({end-start+1} bytes)")

if __name__ == "__main__":
    cam_dir = r"C:\Users\ybarnoy\projects\falcon3\game"
    
    squad0 = os.path.join(cam_dir, "SQUAD0.CAM")
    squad1 = os.path.join(cam_dir, "SQUAD1.CAM")
    
    # Analyze both files
    data0 = analyze_cam_file(squad0)
    data1 = analyze_cam_file(squad1)
    
    # Compare them
    compare_cam_files(squad0, squad1)
    
    # Save analysis
    output_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\cam_file_analysis.txt"
    with open(output_path, 'w') as f:
        f.write("CAMPAIGN FILE (.CAM) ANALYSIS\n")
        f.write("="*80 + "\n\n")
        f.write(f"SQUAD0.CAM: {len(data0)} bytes\n")
        f.write(f"SQUAD1.CAM: {len(data1)} bytes\n\n")
        f.write("File structure hypothesis:\n")
        f.write("  - Size: 11828 bytes\n")
        f.write("  - Potential: 179 records of 66 bytes\n")
        f.write("  - Or: 91 records of 130 bytes\n")
        f.write("  - Or: Mixed structure with header + multiple record types\n")
    
    print(f"\n[+] Analysis saved to {output_path}")
