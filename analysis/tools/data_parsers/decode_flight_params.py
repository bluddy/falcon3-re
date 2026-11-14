#!/usr/bin/env python3
"""
Decode the 23-byte flight parameter structures found in mission files.

These structures appear to be per-flight parameters that specify
altitude, speed, and action codes for waypoint execution.
"""

import sys
import struct

# Action code hypothesis (from manual)
ACTION_NAMES = {
    0: "TAKEOFF/NOTHING",
    1: "NOTHING",
    2: "CAP",
    3: "INTERCEPT",
    4: "ESCORT",
    5: "BOMB",
    6: "CAS",
    7: "SEAD",
    8: "LOITER",
    9: "LAND",
}

def decode_flight_params(data, offset):
    """
    Decode a 23-byte flight parameter structure.
    
    Format (hypothesis based on analysis):
    +0x00-01: uint16 - Unknown (180 for first flight, 0 for others)
    +0x02:    uint8  - Altitude / 100 (feet)
    +0x03:    uint8  - Unknown (always 0x00 so far)
    +0x04:    uint8  - Unknown (0 or 2)
    +0x05:    uint8  - Unknown (always 2)
    +0x06:    uint8  - Action code (0-9)
    +0x07-19: zeros  - Reserved/padding
    +0x14-15: uint8  - Always 30 (0x1E) - timeout/fuel limit?
    +0x16:    uint8  - Always 0
    """
    if offset + 23 > len(data):
        return None
    
    block = data[offset:offset+23]
    
    mystery_uint16 = struct.unpack('<H', block[0:2])[0]
    altitude_byte = block[2]
    byte_3 = block[3]
    byte_4 = block[4]
    byte_5 = block[5]
    action_code = block[6]
    pair_30 = (block[20], block[21])
    
    result = {
        'offset': offset,
        'mystery_uint16': mystery_uint16,
        'altitude_feet': altitude_byte * 100,
        'altitude_raw': altitude_byte,
        'byte_3': byte_3,
        'byte_4': byte_4,
        'byte_5': byte_5,
        'action_code': action_code,
        'action_name': ACTION_NAMES.get(action_code, f"UNKNOWN_{action_code}"),
        'pair_30': pair_30,
        'raw_bytes': block.hex().upper(),
    }
    
    return result

def find_flight_param_structures(data):
    """
    Find all 23-byte flight parameter structures in a mission file.
    
    Pattern: uint16, altitude_byte, 0x00, xx, 0x02, action, zeros..., 0x1E, 0x1E, 0x00
    """
    structures = []
    
    # Look for the pattern: ... XX 00 02 02 ... with 0x1E 0x1E at +20,+21
    for i in range(8, len(data) - 23):  # Start after 8-byte header
        # Check for possible pattern markers
        if data[i+5] == 0x02 and i+22 < len(data):
            if data[i+20] == 0x1E and data[i+21] == 0x1E and data[i+22] == 0x00:
                # Found a candidate
                params = decode_flight_params(data, i)
                if params:
                    structures.append(params)
    
    return structures

def analyze_mission_file(filename):
    """Analyze a mission file and extract flight parameters."""
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f"=== {filename} ===")
    print(f"File size: {len(data)} bytes\n")
    
    # Read header
    if len(data) >= 8:
        flight_count = data[0]
        print(f"Header byte 0: {flight_count} (flight count?)")
        print()
    
    # Find flight parameter structures
    structures = find_flight_param_structures(data)
    
    if structures:
        print(f"Found {len(structures)} flight parameter structure(s):\n")
        for i, params in enumerate(structures, 1):
            print(f"Flight {i} at offset 0x{params['offset']:04X}:")
            print(f"  Mystery uint16:  {params['mystery_uint16']:5d} (0x{params['mystery_uint16']:04X})")
            print(f"  Altitude:        {params['altitude_feet']:5d} feet (raw: {params['altitude_raw']})")
            print(f"  Action code:     {params['action_code']} = {params['action_name']}")
            print(f"  Byte +0x04:      {params['byte_4']}")
            print(f"  Byte +0x05:      {params['byte_5']}")
            print(f"  Pair at +0x14:   {params['pair_30']} (timeout/fuel?)")
            print(f"  Raw hex: {params['raw_bytes']}")
            print()
    else:
        print("No flight parameter structures found.")
    
    return structures

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python decode_flight_params.py <mission_file.MIS>")
        sys.exit(1)
    
    for filename in sys.argv[1:]:
        analyze_mission_file(filename)
        print()
