#!/usr/bin/env python3
"""
Falcon 3.0 Squadron File (.SQU) Parser

Squadron files are 2,703 bytes and contain:
- Squadron header (theater name, etc.)
- 30 pilot records
- Aircraft inventory
- Supply data

Usage:
    python parse_squadron.py SQUAD0.SQU
"""

import struct
import sys

def parse_squadron(filepath):
    """Parse a .SQU squadron file"""
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    if len(data) != 2703:
        print(f"WARNING: Expected 2703 bytes, got {len(data)}")
    
    print("="*70)
    print(f"Squadron File: {filepath}")
    print("="*70)
    print()
    
    # Parse header
    print("HEADER")
    print("-"*70)
    
    offset = 0
    
    # First few bytes (unknown)
    header_bytes = data[0:3]
    print(f"Header bytes: {' '.join(f'{b:02X}' for b in header_bytes)}")
    offset += 3
    
    # Theater name (null-terminated string)
    theater_end = data.find(b'\x00', offset)
    if theater_end > offset:
        theater = data[offset:theater_end].decode('ascii', errors='replace')
        print(f"Theater: {theater}")
        offset = theater_end + 1
    
    # Skip to pilot data
    # Pilots seem to start around offset 50-60
    # Look for first callsign (starts with letters)
    
    # Try to find pilot records
    print()
    print("PILOTS")
    print("-"*70)
    
    # Each pilot record appears to be ~90 bytes
    # Format (approximate):
    #   Callsign (16 bytes, null-terminated?)
    #   Another name field (16 bytes?)
    #   Stats/flags
    
    # Manual pattern search
    pilot_offset = 64  # Starting guess based on hex dump
    pilot_count = 0
    max_pilots = 30
    
    for i in range(max_pilots):
        offset = pilot_offset + (i * 90)  # Guess: 90 bytes per pilot
        
        if offset + 32 > len(data):
            break
        
        # Try to extract callsign (assume first 16 bytes)
        callsign_bytes = data[offset:offset+16]
        
        # Find null terminator
        null_pos = callsign_bytes.find(b'\x00')
        if null_pos > 0:
            callsign = callsign_bytes[:null_pos].decode('ascii', errors='replace')
        else:
            callsign = callsign_bytes.decode('ascii', errors='replace').rstrip('\x00')
        
        # Check if it looks like a valid callsign (printable ASCII)
        if all(32 <= b < 127 or b == 0 for b in callsign_bytes):
            # Second name field
            name_bytes = data[offset+16:offset+32]
            null_pos = name_bytes.find(b'\x00')
            if null_pos > 0:
                name = name_bytes[:null_pos].decode('ascii', errors='replace')
            else:
                name = name_bytes.decode('ascii', errors='replace').rstrip('\x00')
            
            # Some stats bytes
            stats_offset = offset + 32
            stats = data[stats_offset:stats_offset+8]
            
            if callsign.strip():  # Non-empty callsign
                print(f"Pilot {i+1:2d}: {callsign:16s} | {name:16s} | Stats: {' '.join(f'{b:02X}' for b in stats[:8])}")
                pilot_count += 1
    
    print()
    print(f"Found {pilot_count} pilots")
    
    # Show raw structure around pilot area
    print()
    print("RAW PILOT DATA (first 3 pilots)")
    print("-"*70)
    for i in range(3):
        offset = pilot_offset + (i * 90)
        chunk = data[offset:offset+90]
        print(f"\nPilot {i+1} @ offset 0x{offset:04X}:")
        
        # Print in 16-byte rows
        for j in range(0, min(90, len(chunk)), 16):
            row = chunk[j:j+16]
            hex_str = ' '.join(f'{b:02X}' for b in row)
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in row)
            print(f"  {j:04X}: {hex_str:47s}  {ascii_str}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_squadron.py SQUAD0.SQU")
        sys.exit(1)
    
    filepath = sys.argv[1]
    parse_squadron(filepath)

if __name__ == "__main__":
    main()
