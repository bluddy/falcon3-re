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

# Sort by file offset (tail offset)
sorted_recs = sorted([r for r in recs if r['A'] > 0], key=lambda x: x['off'])

# For each record, the fixup stub is the gap to the next record in FILE OFFSET ORDER
print("Record -> Fixup Stub mapping (by file offset order):")
print(f"{'id':>4} {'seg':>4} {'off':>6} {'A':>6} {'end':>6} {'gap':>6} {'next_id':>6} {'next_off':>6}")
print("-" * 70)

for i in range(len(sorted_recs)):
    r = sorted_recs[i]
    end = r['off'] + r['A']
    next_r = sorted_recs[i+1] if i+1 < len(sorted_recs) else None
    if next_r:
        gap = next_r['off'] - (r['off'] + r['A'])
        print(f"{r['id']:4d} {r['seg']:04x} {r['off']:06x} {r['A']:6d} {r['off']+r['A']:06x} {next_r['off'] - (r['off'] + r['A']):6d} {next_r['id']:6d} {next_r['off']:06x}")
    else:
        print(f"{r['id']:4d} {r['seg']:04x} {r['off']:06x} {r['A']:6d} {r['off']+r['A']:06x} {'(last)':>6} {'-':>6} {'-':>6}")

# Now identify which gaps are actual fixup stubs (substantial size, contain code)
print("\n=== Likely fixup stubs (gap > 20 bytes) ===")
for i in range(len(sorted_recs)-1):
    r = sorted_recs[i]
    next_r = sorted_recs[i+1]
    gap = next_r['off'] - (r['off'] + r['A'])
    if gap > 20:
        gap_data = t[r['off'] + r['A']:next_r['off']]
        # Check if it looks like code (has INT 21h, MOV, etc.)
        has_int21 = b'\xcd\x21' in gap_data[:min(len(gap_data), 64)]
        has_mov = any(b in gap_data[:min(len(gap_data), 64)] for b in [0xb4, 0xb8, 0xba, 0xb9])
        print(f"  id={r['id']:3d} gap={next_r['off'] - (r['off'] + r['A']):4d} next_id={next_r['id']:3d} int21={has_int21} mov={has_mov} hex={bytes(t[r['off']+r['A']:r['off']+r['A']+min(16, next_r['off']-(r['off']+r['A']))]).hex()}")

# Key fixup stubs we've identified
print("\n=== Key fixup stubs (manual analysis) ===")
key_stubs = [
    (3, 4, 13),   # id3->id4
    (5, 61, -244), # overlap
    (61, 6, -939), # overlap
    (6, 7, 3),     # tiny
    (7, 62, -14861), # overlap - id7 spans many records
    (52, 53, 117), # id52 has large fixup stub
    (53, 54, 200),
    (55, 56, 494),
    (58, 59, 223),
    (29, 30, 266),
    (30, 31, 54),
    (31, 32, 1744),
    (71, None, 0), # last record
]
print("Note: id7 (16KB) spans ids 62-71 in file offset order - its fixup stub is at the END (after id71?)")
print("Actually, id7 ends at 0x616e, and the next record after ALL 569f records is id71 at 0x3ac0... no, id71 is at 0x3ac0 which is BEFORE id7's end.")
print("This is a complex interleaved layout. The fixup stub for a record is the gap to the NEXT record in FILE ORDER.")
print("For id7 (16KB at 0x22a5-0x616e), it encompasses ids 62-70. Its fixup stub would be after id71 (the last 569f record).")