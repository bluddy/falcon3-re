#!/usr/bin/env python3
"""Find mission-related strings in IDA data symbols."""

import json

# Load data symbols
with open('ida_falconcd/data_symbols.json', 'r') as f:
    symbols = json.load(f)

# Find mission-related strings
keywords = ['cap', 'escort', 'bomb', 'strike', 'intercept', 'sead', 'cas', 'loiter', 'patrol', 'takeoff', 'land']

mission_strings = []
for sym in symbols:
    name = sym.get('ida_name', '').lower()
    if any(kw in name for kw in keywords):
        mission_strings.append(sym)
        ea = sym['ea']
        print(f"EA: 0x{ea:06X} ({ea:7d}) - {sym['ida_name']:30s} - Size: {sym['size']}")

print(f'\nFound {len(mission_strings)} mission-related strings')
print('\nNow search IDA disassembly for references to these addresses...')
