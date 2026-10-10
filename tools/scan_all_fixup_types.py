from pathlib import Path
import struct

d = Path('game/FALCONCD.EXE').read_bytes()
tail = 0x1fb51
t = d[tail:]

base = 0x2c00 + 0x1AA3 * 16 + 0x0C1F
recs = []
for i in range(100):
    o = base + i * 18
    if o + 18 > len(d):
        break
    w = struct.unpack_from('<9H', d, o)
    if not (0x100 <= w[0] <= 0x9000):
        break
    recs.append(dict(id=w[7], seg=w[0], off=w[2], A=w[4], B=w[5], C=w[6]))

sorted_recs = sorted([r for r in recs if r['A'] > 0], key=lambda x: x['off'])

# Scan all fixup tables for 0x33ae type
print(f"{'id':>4} {'seg':>4} {'B':>6} {'total_entries':>6} {'33ae_count':>6} {'other_types'}")
print("-" * 80)

for r in sorted_recs:
    if r['B'] < 4 or r['A'] < r['B']:
        continue
    fixup_off = r['off'] + r['A'] - r['B']
    fixup_data = t[fixup_off:fixup_off + r['B']]
    
    # Parse as 4-byte entries
    entries_33ae = 0
    other_types = set()
    for i in range(0, len(fixup_data) - 3, 4):
        typ = struct.unpack_from('<H', fixup_data, i)[0]
        offset = struct.unpack_from('<H', fixup_data, i + 2)[0]
        if typ == 0x33ae and 0 <= offset < (r['A'] - r['B']):
            pass  # valid 33ae entry
        elif typ != 0:
            other_types.add(f"0x{typ:04x}")
    
    count_33ae = sum(1 for i in range(0, len(fixup_data) - 3, 4) 
                     if struct.unpack_from('<H', fixup_data, i)[0] == 0x33ae and 
                     struct.unpack_from('<H', fixup_data, i + 2)[0] < (r['A'] - r['B']))
    
    total_entries = r['B'] // 4
    if count_33ae > 0 or len(other_types) > 0:
        print(f"id={r['id']:3d} seg={r['seg']:04x} B={r['B']:4d} entries={r['B']//4:4d} 33ae={count_33ae:4d} other={len(other_types)} types={sorted(other_types)[:5]}")

print("\n=== Records with significant 0x33ae fixups ===")
for r in sorted_recs:
    if r['B'] < 4 or r['A'] < r['B']:
        continue
    fixup_off = r['off'] + r['A'] - r['B']
    fixup_data = t[fixup_off:fixup_off + r['B']]
    
    count_33ae = sum(1 for i in range(0, len(fixup_data) - 3, 4) 
                     if struct.unpack_from('<H', fixup_data, i)[0] == 0x33ae and 
                     struct.unpack_from('<H', fixup_data, i + 2)[0] < (r['A'] - r['B']))
    
    if count_33ae > 5:
        print(f"id={r['id']:3d} seg={r['seg']:04x} B={r['B']:4d} 33ae_fixups={count_33ae}")