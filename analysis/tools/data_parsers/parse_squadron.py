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
    
    # Pilot records start at offset 0x3C (60 bytes)
    # Each pilot record is 66 bytes (0x42)
    
    pilot_start = 0x3C
    pilot_size = 0x42  # 66 bytes
    pilot_count = 30
    
    print()
    print(f"PILOTS ({pilot_count} records @ {pilot_size} bytes each)")
    print("-"*70)
    print(f"{'#':>2} {'Callsign':<16} {'Nickname':<16} {'ID':>5} {'Rank':>4} Stats")
    print("-"*70)
    
    pilots_found = 0
    
    for i in range(pilot_count):
        offset = pilot_start + (i * pilot_size)
        
        if offset + pilot_size > len(data):
            print(f"[ERROR] Pilot {i+1} extends beyond file")
            break
        
        pilot_data = data[offset:offset+pilot_size]
        
        # Structure (66 bytes):
        # +0x00-0x01: Unknown (status flags?)
        # +0x02:      Rank or type byte
        # +0x03-0x12: Callsign (first byte at +0x03, rest follows)
        # +0x13-0x21: Nickname
        # +0x22-0x25: ID code (3 letters + 'd')
        # +0x26-0x29: Stats? (abilities/fatigue?)
        # +0x2A+:     More data
        
        status_bytes = pilot_data[0:2]
        rank_byte = pilot_data[2]
        
        # Callsign: starts at +0x03, ~15 bytes
        callsign_bytes = pilot_data[3:3+15]
        null_pos = callsign_bytes.find(b'\x00')
        if null_pos > 0:
            callsign = callsign_bytes[:null_pos].decode('ascii', errors='ignore')
        else:
            callsign = callsign_bytes.decode('ascii', errors='ignore').rstrip('\x00')
        
        # Nickname: starts at +0x13 (19), ~15 bytes
        name_bytes = pilot_data[0x13:0x13+15]
        null_pos = name_bytes.find(b'\x00')
        if null_pos > 0:
            name = name_bytes[:null_pos].decode('ascii', errors='ignore')
        else:
            name = name_bytes.decode('ascii', errors='ignore').rstrip('\x00')
        
        # ID code: starts at +0x22 (34), 4 bytes
        id_bytes = pilot_data[0x22:0x26]
        pilot_id = id_bytes.decode('ascii', errors='ignore').rstrip('\x00').rstrip('d').strip()
        
        # Stats (guess): around +0x26-0x2A
        stats = pilot_data[0x26:0x2A]
        
        # Only print if callsign has letters
        if callsign.strip() and any(c.isalpha() for c in callsign):
            stats_hex = ' '.join(f'{b:02X}' for b in stats)
            print(f"{i+1:2d} {callsign:<16} {name:<16} {pilot_id:>5} {rank_byte:4d} {stats_hex}")
            pilots_found += 1
            
            if verbose and i < 3:  # Show first 3 in detail
                print(f"    Raw data @ 0x{offset:04X}:")
                for j in range(0, min(pilot_size, 66), 16):
                    row = pilot_data[j:j+16]
                    hex_str = ' '.join(f'{b:02X}' for b in row)
                    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in row)
                    print(f"      {j:04X}: {hex_str:47s}  {ascii_str}")
                print()
    
    print()
    print(f"Found {pilots_found} valid pilots")
    
    # Supply/aircraft data
    print()
    print("SUPPLY/AIRCRAFT DATA")
    print("-"*70)
    
    supply_offset = pilot_start + (pilot_count * pilot_size)
    remaining = len(data) - supply_offset
    
    print(f"Pilots end at:    0x{supply_offset:04X} ({supply_offset})")
    print(f"File ends at:     0x{len(data):04X} ({len(data)})")
    print(f"Remaining bytes:  {remaining}")
    
    if remaining > 0:
        print()
        print("Last 128 bytes of file (supply/aircraft data):")
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
