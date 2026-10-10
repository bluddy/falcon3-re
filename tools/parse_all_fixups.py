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

records_with_fixups = {}

for r in sorted_recs:
    if r['B'] == 0 or r['A'] < r['B']:
        continue
    off, A, B = r['off'], r['A'], r['B']
    code_size = A - B
    fixup_off = off + A - B
    fixup_data = t[fixup_off:fixup_off + B]
    
    # Parse as 4-byte entries: type (uint16) + offset (uint16)
    entries = []
    fixup_bytes = fixup_data
    for i in range(0, len(fixup_bytes) - 3, 4):
        if i + 3 >= len(fixup_bytes):
            break
        typ = struct.unpack_from('<H', fixup_bytes, i)[0]
        offset = struct.unpack_from('<H', fixup_bytes, i + 2)[0]
        entries.append((typ, offset))
    
    # Filter valid entries (offset within code)
    valid_entries = [(typ, offset) for typ, offset in entries if 0 <= offset < code_size]
    
    # Group by type
    by_type = {}
    for typ, offset in valid_entries:
        if typ not in by_type:
            by_type[typ] = []
        by_type[typ].append(offset)
    
    records_with_fixups[r['id']] = dict(
        id=r['id'],
        seg=r['seg'],
        off=r['off'],
        code_size=code_size,
        fixup_size=r['B'],
        fixup_entries=len(valid_entries),
        types=list(by_type.keys()),
        type_counts={k: len(v) for k, v in by_type.items()},
        fixups_by_type={k: v for k, v in by_type.items()},
    )

# Save parsed fixups
out = Path('analysis/ida_falconcd/fixup_tables_parsed.json')
out.parent.mkdir(parents=True, exist_ok=True)
with open(out, 'w') as f:
    json.dump(records_with_fixups, f, indent=1)

print(f"Parsed fixup tables for {len(records_with_fixups)} records")

# Summary by type
all_types = {}
for r in records_with_fixups.values():
    for typ, count in r['type_counts'].items():
        all_types[typ] = all_types.get(typ, 0) + count

print("\nFixup types across all records:")
for typ, count in sorted(all_types.items(), key=lambda x: -x[1]):
    print(f"  0x{typ:04x}: {count} entries")

# Records with fixups
print(f"\nRecords with fixups: {len(records_with_fixups)}")
for id, r in sorted(records_with_fixups.items()):
    if r['fixup_entries'] > 0:
        types_str = ', '.join(f'0x{typ:04x}({cnt})' for typ, cnt in r['type_counts'].items())
        print(f"  id={r['id']:3d} seg={r['seg']:04x} code={r['code_size']:5d} fixups={r['fixup_entries']:4d} types={types_str}")

# Detailed view of id7 (the big one)
r7 = next(r for r in sorted_recs if r['id'] == 7)
off, A, B = r7['off'], r7['A'], r7['B']
code_size = A - B
fixup_data = t[r7['off'] + r7['A'] - B: r7['off'] + r7['A']]

print(f"\n=== id7 fixup table detail (first 64 entries) ===")
fixup_bytes = fixup_data
for i in range(0, min(len(fixup_bytes), 256), 4):
    if i + 3 >= len(fixup_bytes):
        break
    typ = struct.unpack_from('<H', fixup_bytes, i)[0]
    offset = struct.unpack_from('<H', fixup_bytes, i + 2)[0]
    if offset < code_size:
        print(f"  [{i//4:3d}] type=0x{typ:04x} offset=0x{offset:04x} (code_off={offset:04x})")