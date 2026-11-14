#!/usr/bin/env python3
"""Parse supply and inventory data from campaign files."""

import struct
import sys

# Known weapon types in Falcon 3.0
WEAPONS = [
    "AIM-9 Sidewinder",
    "AIM-120 AMRAAM", 
    "AGM-65 Maverick",
    "AGM-88 HARM",
    "Mk-82 Bomb (500lb)",
    "Mk-84 Bomb (2000lb)",
    "CBU Cluster Bomb",
    "Rockets/Other",
]

def parse_supply_inventory(data):
    """Parse the supply/inventory section at 0x2D8E."""
    
    # Supply data starts at 0x2D8E (after all targets and padding)
    offset = 0x2D8E
    
    if offset + 100 > len(data):
        print(f'Error: File too small (need at least {offset + 100} bytes)')
        return None
    
    section = data[offset:offset+200]
    
    print('=== FALCON 3.0 SUPPLY & INVENTORY ===')
    print()
    
    # Parse as uint16 array
    def u16(idx):
        return struct.unpack('<H', section[idx:idx+2])[0]
    
    # Header/Unknown fields
    print('Header:')
    print(f'  +0x00-0x03: {section[0]:02X} {section[1]:02X} {section[2]:02X} {section[3]:02X} (unknown)')
    print(f'  +0x04: {u16(0x04)} (0x{u16(0x04):04X}) - unknown value')
    print(f'  +0x06: {u16(0x06)} - campaign flags?')
    print()
    
    # Weapon stockpiles
    print('Weapon Stockpiles:')
    weapon_offsets = [0x08, 0x0A, 0x0C, 0x0E, 0x10, 0x14, 0x16, 0x18, 0x1A, 0x1C, 0x1E]
    
    # First weapon array (possibly initial/max quantities)
    print('  Primary stores:')
    for i, off in enumerate(weapon_offsets[:8]):
        val = u16(off)
        weapon_name = WEAPONS[i] if i < len(WEAPONS) else f"Weapon{i+1}"
        print(f'    {weapon_name:25s}: {val:4d}')
    
    # Second set (possibly current quantities or alternate loadout)
    print()
    print('  Secondary stores (or different category):')
    for i, off in enumerate([0x12, 0x20, 0x22, 0x24, 0x26]):
        val = u16(off)
        print(f'    Slot {i+1:2d}: {val:4d}')
    
    print()
    
    # Fuel
    print('Fuel Reserves:')
    fuel1 = u16(0x28)
    fuel2 = u16(0x2A)
    print(f'  Value 1: {fuel1:5d} (0x{fuel1:04X})')
    print(f'  Value 2: {fuel2:5d} (0x{fuel2:04X})')
    if fuel1 == fuel2:
        print(f'  (Values match - likely fuel in gallons or lbs)')
    print()
    
    # Campaign state
    print('Campaign State:')
    print(f'  +0x2C: {u16(0x2C):3d} - unknown counter')
    print(f'  +0x2E: {u16(0x2E):5d} (0x{u16(0x2E):04X}) - unknown value')
    print(f'  +0x30: {u16(0x30):3d} - small counter (campaign day?)')
    print(f'  +0x32: {u16(0x32):3d} - small counter')
    print()
    
    # Aircraft inventory
    print('Aircraft Inventory:')
    aircraft_count = u16(0x34)
    print(f'  F-16s Available:  {aircraft_count:2d} *** PRIMARY AIRCRAFT COUNT ***')
    print(f'  +0x36: {u16(0x36):2d} - aircraft damaged?')
    print(f'  +0x38: {u16(0x38):2d} - maintenance queue?')
    print(f'  +0x3A: {u16(0x3A):2d} - pilots available?')
    print(f'  +0x3C: {u16(0x3C):2d} - unknown counter')
    print(f'  +0x3E: {u16(0x3E):2d} - flag/status')
    print()
    
    # Additional counters
    print('Additional Counters:')
    print(f'  +0x40: {u16(0x40):3d}')
    print(f'  +0x42: {u16(0x42):3d}')
    print()
    
    # Summary
    print('=== SUMMARY ===')
    print()
    total_aa = u16(0x08) + u16(0x0A)  # Sidewinder + AMRAAM
    total_ag = u16(0x0C) + u16(0x0E)  # Maverick + HARM
    total_bombs = u16(0x10) + u16(0x14)  # Mk-82 + Mk-84 approx
    
    print(f'Aircraft:        {aircraft_count:3d} F-16s')
    print(f'AA Missiles:     ~{total_aa:3d} (AIM-9 + AIM-120)')
    print(f'AG Missiles:     ~{total_ag:3d} (Maverick + HARM)')
    print(f'Bombs:           ~{total_bombs:3d} (Mk-82 + Mk-84 approx)')
    print(f'Fuel:            {fuel1:5d} units')
    
    return {
        'aircraft': aircraft_count,
        'fuel': fuel1,
        'weapons': {
            WEAPONS[i]: u16(weapon_offsets[i]) 
            for i in range(min(len(WEAPONS), len(weapon_offsets)))
        }
    }

def main():
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = '../game/SQUAD0.CAM'
    
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f'Campaign file: {filename}')
    print(f'Size: {len(data)} bytes')
    print()
    
    result = parse_supply_inventory(data)
    
    if result:
        print()
        print('=' * 60)
        print()
        print('Supply data successfully parsed!')
        print(f'This squadron has {result["aircraft"]} F-16s and {result["fuel"]} fuel units.')

if __name__ == '__main__':
    main()
