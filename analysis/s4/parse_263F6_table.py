#!/usr/bin/env python3
"""Parse the embedded dispatch table in sub_263F6."""
import json
import struct

# Load function_bytes
fb = json.load(open("../ida_falconcd/function_bytes.json"))

# Get sub_263F6 bytes
func_data = fb['sub_263F6']
bytes_hex = func_data['bytes']
all_bytes = bytes.fromhex(bytes_hex)

print(f"sub_263F6 total size: {len(all_bytes)} bytes")
print(f"Expected: 122 bytes\n")

# First 6 bytes are code:
# 2E FF 1E 10 2A  = call far dword ptr cs:[2A10h]
# CB               = retf
code_bytes = all_bytes[:6]
table_bytes = all_bytes[6:]

print(f"Code bytes (6): {code_bytes.hex()}")
print(f"Table bytes ({len(table_bytes)}): {table_bytes.hex()[:40]}...\n")

# Parse as dword array (far pointers: offset:segment)
print("="*80)
print("DISPATCH TABLE - Parsed as far pointers (offset:segment dwords)")
print("="*80)
print(f"{'Index':<6} {'Offset':<8} {'Bytes (LE)':<12} {'Offset':<8} {'Segment':<8} {'IDA Address':<12}")
print("-"*80)

entries = []
for i in range(0, len(table_bytes), 4):
    if i + 4 > len(table_bytes):
        break
    
    # Read as little-endian dword
    dword_bytes = table_bytes[i:i+4]
    offset = struct.unpack('<H', dword_bytes[0:2])[0]
    segment = struct.unpack('<H', dword_bytes[2:4])[0]
    
    # Convert to IDA linear address: segment * 16 + offset + 0x10000
    if segment > 0:
        ida_addr = segment * 16 + offset + 0x10000
    else:
        ida_addr = 0
    
    hex_str = " ".join([f"{b:02X}" for b in dword_bytes])
    ida_str = f"0x{ida_addr:05X}" if ida_addr > 0 else "NULL"
    
    entries.append({
        'index': i // 4,
        'offset': offset,
        'segment': segment,
        'ida_address': ida_addr,
        'is_null': (offset == 0 and segment == 0)
    })
    
    print(f"{i//4:<6} 0x{i+6:04X}    {hex_str:<12} 0x{offset:04X}   0x{segment:04X}   {ida_str:<12}")

print(f"\n Total entries: {len(entries)}")

# Analysis
null_entries = [e for e in entries if e['is_null']]
valid_entries = [e for e in entries if not e['is_null']]

print(f"\nSTATISTICS:")
print(f"  Null entries: {len(null_entries)}")
print(f"  Valid entries: {len(valid_entries)}")

# Check if valid entries point to code
print(f"\nVALID ENTRIES ANALYSIS:")
print(f"{'Index':<6} {'Segment':<8} {'IDA Addr':<12} {'In FB?':<8} {'Function Name'}")
print("-"*80)

for e in valid_entries:
    ida_addr = e['ida_address']
    # Check if this address is in function_bytes
    in_fb = False
    func_name = "???"
    
    for fname, fdata in fb.items():
        if fdata['ea'] == ida_addr:
            in_fb = True
            func_name = fname
            break
        # Check if address is inside function range
        if fdata['ea'] <= ida_addr < fdata['ea'] + fdata.get('size', 0):
            in_fb = True
            func_name = f"{fname}+{ida_addr - fdata['ea']}"
            break
    
    in_fb_str = "YES" if in_fb else "NO"
    print(f"{e['index']:<6} 0x{e['segment']:04X}   0x{ida_addr:05X}    {in_fb_str:<8} {func_name}")

# Save to JSON
output = {
    'function': 'sub_263F6',
    'description': 'Embedded dispatch table (far pointer array)',
    'code_bytes': 6,
    'table_bytes': len(table_bytes),
    'total_entries': len(entries),
    'null_entries': len(null_entries),
    'valid_entries': len(valid_entries),
    'entries': entries
}

json.dump(output, open('sub_263F6_table.json', 'w'), indent=2)
print(f"\nSaved analysis to sub_263F6_table.json")
