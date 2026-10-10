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

# Deep dive into id7 fixup table
r7 = next(r for r in sorted_recs if r['id'] == 7)
off, A, B = r7['off'], r7['A'], r7['B']
code_size = A - B
fixup_off = r7['off'] + r7['A'] - r7['B']
fixup_data = t[fixup_off:fixup_off + r7['B']]

print(f"id7 fixup table: {len(fixup_data)} bytes")
print(f"Code size: {code_size}")

# Parse ALL entries and count types
type_counts = {}
offsets_by_type = {}

for i in range(0, len(fixup_data) - 3, 4):
    typ = struct.unpack_from('<H', fixup_data, i)[0]
    offset = struct.unpack_from('<H', fixup_data, i + 2)[0]
    
    if typ not in type_counts:
        type_counts[typ] = 0
        offsets_by_type[typ] = []
    type_counts[typ] = type_counts.get(typ, 0) + 1
    if 0 <= offset < 12544:
        offsets_by_type[typ].append(offset)

print(f"Total entries: {sum(type_counts.values())}")
print("\nType counts:")
for typ, count in sorted(type_counts.items(), key=lambda x: -x[1]):
    valid = len([o for o in offsets_by_type[typ] if 0 <= o < 12544])
    print(f"  0x{typ:04x}: {count:4d} total, {valid:4d} valid offsets")

# Check first 50 entries in detail
print("\nFirst 50 entries:")
for i in range(0, min(200, len(fixup_data)), 4):
    if i + 3 >= len(fixup_data):
        break
    typ = struct.unpack_from('<H', fixup_data, i)[0]
    offset = struct.unpack_from('<H', fixup_data, i + 2)[0]
    valid = "VALID" if 0 <= offset < 12544 else "INVALID"
    print(f"  [{i//4:3d}] type=0x{typ:04x} offset=0x{offset:04x} {valid}")

# Also check if there's a pattern in the types
print("\n=== Type value analysis ===")
for typ in sorted(type_counts.keys()):
    print(f"  0x{typ:04x}: high={typ>>8:02x} low={typ&0xff:02x}")