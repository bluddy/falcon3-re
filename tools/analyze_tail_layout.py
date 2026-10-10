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

# Sort by file offset
sorted_recs = sorted([r for r in recs if r['A'] > 0], key=lambda x: x['off'])

print("Record layout analysis:")
print(f"{'id':>4} {'seg':>4} {'off':>6} {'A':>6} {'B':>6} {'end':>6} {'gap':>6} {'next_id':>6} {'next_off':>6}")
print("-" * 80)

for i in range(len(sorted_recs)):
    r = sorted_recs[i]
    end = r['off'] + r['A']
    next_r = sorted_recs[i+1] if i+1 < len(sorted_recs) else None
    if next_r:
        gap = next_r['off'] - end
        print(f"{r['id']:4d} {r['seg']:04x} {r['off']:06x} {r['A']:6d} {r['B']:6d} {end:06x} {gap:6d} {next_r['id']:6d} {next_r['off']:06x}")
    else:
        print(f"{r['id']:4d} {r['seg']:04x} {r['off']:06x} {r['A']:6d} {r['B']:6d} {end:06x} {'(last)':>6} {'-':>6} {'-':>6}")

print("\n=== Checking record data for embedded fixup tables ===")
# For each record, check if the last B bytes of the record data look like a fixup table
for r in sorted_recs:
    if r['B'] > 0 and r['A'] >= r['B']:
        off, A, B = r['off'], r['A'], r['B']
        rec_data = t[off:off+A]
        # Check last B bytes
        if A >= B:
            potential_fixup = t[off+A-B:off+A]
            # Check if it looks like a fixup table (words pointing within record)
            words = struct.unpack(f'<{B//2}H', potential_fixup[:B - B%2])
            # Count how many point within record (0 to A)
            in_range = sum(1 for w in words if 0 <= w < A)
            print(f"id={r['id']:3d} A={r['A']:4d} B={r['B']:4d} last_B_words={len(words)} in_range={in_range}/{len(words)} first_words={words[:8]}")

print("\n=== Checking if fixup data is in the gap ===")
# The fixup stub in the gap might contain embedded fixup data
for i in range(len(sorted_recs)-1):
    r = sorted_recs[i]
    next_r = sorted_recs[i+1]
    gap = next_r['off'] - (r['off'] + r['A'])
    if gap > 0:
        gap_data = t[r['off']+r['A']:next_r['off']]
        # Check for relocation-like patterns
        if len(gap_data) >= 4:
            words = struct.unpack(f'<{len(gap_data)//2}H', gap_data[:gap - gap%2])
            # Look for words that could be offsets within the record
            in_rec = sum(1 for w in words if 0 <= w < r['A'])
            if in_range > 0 or len(gap_data) > 20:
                print(f"id={r['id']:3d} gap={gap:4d} B={r['B']:4d} words={len(words)} in_rec={in_rec} gap_start={gap_data[:16].hex()}")