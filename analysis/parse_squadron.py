#!/usr/bin/env python3
"""
Falcon 3.0 Squadron File (.SQU) Parser

Squadron files are 2,703 bytes and contain:
- Squadron header (theater name, etc.)
- 30 pilot records (~88 bytes each)
- Aircraft inventory
- Supply data

Based on documentation from:
- Falcon Campaign Editor (FCE)
- Falcon Squadron Manager (FSM)
- Strategic Falcon (SF)

Pilot record contains:
- Callsign
- Name/nickname
- Rank
- Status (Active, KIA, MIA, Court Martialed)
- Abilities: Dogfighting, Bombing, Flying (0-100)
- Fatigue level (0-100)

Usage:
    python parse_squadron.py SQUAD0.SQU
    python parse_squadron.py SQUAD0.SQU --verbose
"""

import struct
import sys
import os

def parse_squadron(filepath, verbose=False):
    """Parse a .SQU squadron file"""
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    if len(data) != 2703:
        print(f"WARNING: Expected 2703 bytes, got {len(data)}")
    
    print("="*70)
    print(f"Squadron File: {os.path.basename(filepath)}")
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
    
    # Calculate pilot data start
    # Based on observations: pilots start around offset 64
    # With 30 pilots and ~2640 bytes remaining, that's 88 bytes per pilot
    
    pilot_start = 64
    pilot_size = 88
    pilot_count = 30
    
    print()
    print(f"PILOTS (estimated {pilot_count} pilots @ {pilot_size} bytes each)")
    print("-"*70)
    print(f"{'#':>2} {'Callsign':<16} {'Nickname':<16} {'ID':>4} {'Stats'}")
    print("-"*70)
    
    for i in range(pilot_count):
        offset = pilot_start + (i * pilot_size)
        
        if offset + pilot_size > len(data):
            print(f"[ERROR] Pilot {i+1} extends beyond file")
            break
        
        pilot_data = data[offset:offset+pilot_size]
        
        # Try different field offsets based on hex dump patterns
        # Callsign appears to be at start of record
        callsign_bytes = pilot_data[2:18]  # Skip 2 bytes, read 16
        null_pos = callsign_bytes.find(b'\x00')
        if null_pos > 0:
            callsign = callsign_bytes[:null_pos].decode('ascii', errors='replace')
        else:
            callsign = callsign_bytes.decode('ascii', errors='replace').rstrip('\x00')
        
        # Nickname/name appears after callsign
        name_bytes = pilot_data[18:34]
        null_pos = name_bytes.find(b'\x00')
        if null_pos > 0:
            name = name_bytes[:null_pos].decode('ascii', errors='replace')
        else:
            name = name_bytes.decode('ascii', errors='replace').rstrip('\x00')
        
        # 3-letter ID code (appears after name, followed by 'd')
        id_bytes = pilot_data[34:38]
        pilot_id = id_bytes.decode('ascii', errors='replace').rstrip('\x00').rstrip('d')
        
        # Stats (abilities and fatigue) - location unclear, try around offset 40
        stats_offset = 40
        stats = pilot_data[stats_offset:stats_offset+8]
        
        # Only print if callsign looks valid (has letters)
        if callsign.strip() and any(c.isalpha() for c in callsign):
            stats_hex = ' '.join(f'{b:02X}' for b in stats[:4])
            print(f"{i+1:2d} {callsign:<16} {name:<16} {pilot_id:>4} {stats_hex}")
            
            if verbose and i < 5:  # Show first 5 in detail
                print(f"    Raw data @ 0x{offset:04X}:")
                for j in range(0, min(pilot_size, 64), 16):
                    row = pilot_data[j:j+16]
                    hex_str = ' '.join(f'{b:02X}' for b in row)
                    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in row)
                    print(f"      {j:04X}: {hex_str:47s}  {ascii_str}")
                print()
    
    # Try to find supply/aircraft data at end of file
    print()
    print("SUPPLY/AIRCRAFT DATA (estimated location)")
    print("-"*70)
    
    supply_offset = pilot_start + (pilot_count * pilot_size)
    if supply_offset < len(data):
        remaining = len(data) - supply_offset
        print(f"Remaining bytes: {remaining}")
        print(f"Location: 0x{supply_offset:04X} - 0x{len(data):04X}")
        
        # Show last 128 bytes
        print()
        print("Last 128 bytes of file:")
        tail_data = data[-128:]
        for j in range(0, len(tail_data), 16):
            row = tail_data[j:j+16]
            addr = len(data) - 128 + j
            hex_str = ' '.join(f'{b:02X}' for b in row)
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in row)
            print(f"  {addr:04X}: {hex_str:47s}  {ascii_str}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_squadron.py SQUAD0.SQU [--verbose]")
        sys.exit(1)
    
    filepath = sys.argv[1]
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    parse_squadron(filepath, verbose)

if __name__ == "__main__":
    main()
