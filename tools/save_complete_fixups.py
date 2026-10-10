from pathlib import Path
import struct
import json

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

# Parse all fixup tables
records_with_fixups = {}

for r in sorted_recs:
    if r['B'] < 4 or r['A'] < r['B']:
        continue
    off, A, B = r['off'], r['A'], r['B']
    code_size = A - B
    fixup_off = off + A - B
    fixup_data = t[fixup_off:fixup_off + B]
    
    entries = []
    for i in range(0, len(fixup_data) - 3, 4):
        typ = struct.unpack_from('<H', fixup_data, i)[0]
        offset = struct.unpack_from('<H', fixup_data, i + 2)[0]
        if 0 <= offset < code_size:
            entries.append((typ, offset))
    
    if entries:
        by_type = {}
        for typ, offset in entries:
            if typ not in by_type:
                by_type[typ] = []
            by_type[typ].append(offset)
        
        records_with_fixups[r['id']] = dict(
            id=r['id'],
            seg=r['seg'],
            off=r['off'],
            code_size=code_size,
            fixup_size=r['B'],
            total_entries=len(entries),
            type_counts={k: len(v) for k, v in by_type.items()},
            fixups_by_type={k: v for k, v in by_type.items()},
        )

# Save complete fixup data
out = Path('analysis/ida_falconcd/fixup_tables_complete.json')
out.parent.mkdir(parents=True, exist_ok=True)
with open(out, 'w') as f:
    json.dump(records_with_fixups, f, indent=1)

print(f"Saved fixup tables for {len(records_with_fixups)} records to {out}")

# Summary
total_fixups = sum(r['total_entries'] for r in records_with_fixups.values())
print(f"Total fixup entries: {total_fixups}")

for id, r in sorted(records_with_fixups.items()):
    types_str = ', '.join(f'0x{typ:04x}({cnt})' for typ, cnt in r['type_counts'].items())
    print(f"  id={r['id']:3d} seg={r['seg']:04x} code={r['code_size']:5d} fixups={r['total_entries']:4d} types={types_str}")