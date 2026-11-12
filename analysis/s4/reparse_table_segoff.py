#!/usr/bin/env python3
"""
Reparse sub_263F6 table as SEGMENT:OFFSET format (not offset:segment).

Far pointers in DOS are stored as segment:offset, both little-endian words.
Bytes: [seg_lo, seg_hi, off_lo, off_hi]
"""
import json
import struct

# Load function bytes
fb = json.load(open('../ida_falconcd/function_bytes.json'))
data = fb['sub_263F6']
all_bytes = bytes.fromhex(data['bytes'])

# Skip first 6 bytes (code)
code_bytes = all_bytes[:6]
table_bytes = all_bytes[6:]

print("="*80)
print("RE-PARSING DISPATCHER TABLE AS SEGMENT:OFFSET")
print("="*80)
print(f"\nCode: {code_bytes.hex()}")
print(f"Table: {len(table_bytes)} bytes\n")

print(f"{'Index':<6} {'Bytes':<14} {'Segment':<10} {'Offset':<10} {'IDA Linear':<12}")
print("-"*70)

entries = []
for i in range(0, len(table_bytes), 4):
    if i + 4 > len(table_bytes):
        break
    
    # Read as segment:offset (both little-endian words)
    dword = table_bytes[i:i+4]
    segment = struct.unpack('<H', dword[0:2])[0]
    offset = struct.unpack('<H', dword[2:4])[0]
    
    # Convert to IDA linear: segment * 16 + offset + 0x10000
    if segment > 0 or offset > 0:
        ida_linear = segment * 16 + offset + 0x10000
    else:
        ida_linear = 0
    
    hex_str = ' '.join(f"{b:02X}" for b in dword)
    
    entries.append({
        'index': i // 4,
        'segment': segment,
        'offset': offset,
        'ida_linear': ida_linear,
        'is_null': (segment == 0 and offset == 0)
    })
    
    print(f"{i//4:<6} {hex_str:<14} 0x{segment:04X}     0x{offset:04X}     0x{ida_linear:05X}")

# Statistics
valid = [e for e in entries if not e['is_null']]
null = [e for e in entries if e['is_null']]

print(f"\n\nStatistics:")
print(f"  Total entries: {len(entries)}")
print(f"  Valid: {len(valid)}")
print(f"  Null: {len(null)}")

# Check if IDA addresses match functions
print(f"\n\nChecking against function_bytes.json...")
print(f"{'Index':<6} {'IDA Addr':<12} {'Function':<30} {'Size':<8} {'Named?'}")
print("-"*90)

results = []
for e in valid:
    ida_addr = e['ida_linear']
    
    # Look for function
    found = None
    is_named = False
    for fname, fdata in fb.items():
        if fdata['ea'] == ida_addr:
            found = fname
            is_named = not fname.startswith('sub_')
            size = fdata['size']
            break
    
    if found:
        named_str = "YES" if is_named else "NO"
        print(f"{e['index']:<6} 0x{ida_addr:05X}    {found:<30} {size:<8}B {named_str}")
        results.append({'index': e['index'], 'function': found, 'is_named': is_named})
    else:
        print(f"{e['index']:<6} 0x{ida_addr:05X}    NO MATCH")
        results.append({'index': e['index'], 'function': None, 'is_named': False})

# Summary
matched = [r for r in results if r['function']]
named = [r for r in results if r['is_named']]

print(f"\n\nRESULTS:")
print(f"  Valid entries: {len(valid)}")
print(f"  Matched functions: {len(matched)} ({100*len(matched)//len(valid) if valid else 0}%)")
print(f"  Named functions: {len(named)}")

# Save
output = {
    'format': 'segment:offset (corrected)',
    'total_entries': len(entries),
    'valid_entries': len(valid),
    'null_entries': len(null),
    'matched_functions': len(matched),
    'entries': [
        {
            **e,
            'function': results[i]['function'] if i < len(results) else None,
            'is_named': results[i]['is_named'] if i < len(results) else False
        }
        for i, e in enumerate(entries) if not e['is_null']
    ]
}

json.dump(output, open('dispatcher_corrected.json', 'w'), indent=2)
print(f"\n\nSaved to dispatcher_corrected.json")
