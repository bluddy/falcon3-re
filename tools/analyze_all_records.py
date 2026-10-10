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

# Build complete record map with gaps
sorted_recs = sorted([r for r in recs if r['A'] > 0], key=lambda x: x['off'])

# For each record, extract: record_data, gap_fixup, next_record
record_map = {}
for i in range(len(sorted_recs)):
    r = sorted_recs[i]
    next_r = sorted_recs[i+1] if i+1 < len(sorted_recs) else None
    
    off, A, B, C, seg, id = r['off'], r['A'], r['B'], r['C'], r['seg'], r['id']
    
    # Record data
    record_data = t[off:off+A]
    
    # Gap/fixup stub
    gap = b''
    gap_size = 0
    if next_r:
        gap_start = off + A
        gap_end = next_r['off']
        gap_size = gap_end - gap_start
        if gap_size > 0:
            gap = t[gap_start:gap_end]
    
    # Analyze record data structure
    # Check if it starts with a table (repeated segment value)
    sample = record_data[:min(A, 64)]
    if len(sample) % 2:
        sample = sample[:-1]
    word_count = len(sample) // 2
    words = struct.unpack(f'<{word_count}H', sample)
    repeated_seg = None
    if len(words) >= 4:
        segs = [w for w in words[::2]]
        if all(s == segs[0] for s in segs):
            repeated_seg = segs[0]
    
    record_map[id] = dict(
        id=id, seg=seg, off=off, A=A, B=B, C=C,
        record_data=record_data,
        gap=gap,
        gap_size=gap_size,
        repeated_seg=repeated_seg,
        word_count=len(words),
    )

# Print summary
print(f"{'id':>4} {'seg':>4} {'off':>6} {'A':>6} {'B':>6} {'gap':>6} {'rep_seg':>6} {'type'}")
print("-" * 70)
for id in sorted(record_map.keys()):
    r = record_map[id]
    rtype = "entry_table" if r['repeated_seg'] else "code"
    if r['gap_size'] > 100:
        rtype += "+fixup_stub"
    elif r['gap_size'] > 0:
        rtype += "+fixup"
    print(f"{r['id']:4d} {r['seg']:04x} {r['off']:06x} {r['A']:6d} {r['B']:6d} {r['gap_size']:6d} {r['repeated_seg'] or 'none':>6} {rtype}")

# Detailed analysis of key records
print("\n=== Detailed: id52 (seg=569f, entry table) ===")
r52 = record_map[52]
print(f"  Record size: {r52['A']} bytes")
print(f"  Gap size: {r52['gap_size']} bytes")
print(f"  Repeated seg: {r52['repeated_seg']:04x}")
print(f"  Entry table entries: {len(r52['record_data']) // 4}")
print(f"  Entries: {[f'{w:04x}:{o:04x}' for w,o in zip(r52['record_data'][::4], r52['record_data'][2::4])][:8]}")

print("\n=== Detailed: id3 (seg=1cf6, first real record) ===")
r3 = record_map[3]
print(f"  Record size: {r3['A']} bytes")
print(f"  Gap size: {r3['gap_size']} bytes")
print(f"  Record head: {r3['record_data'][:32].hex()}")

print("\n=== Detailed: id7 (seg=1e10, large record) ===")
r7 = record_map[7]
print(f"  Record size: {r7['A']} bytes")
print(f"  Gap size: {r7['gap_size']} bytes")
print(f"  Record head: {r7['record_data'][:32].hex()}")

print("\n=== Detailed: id29 (seg=1e10, 1204 bytes) ===")
r29 = record_map[29]
print(f"  Record size: {r29['A']} bytes")
print(f"  Gap size: {r29['gap_size']} bytes")
print(f"  Record head: {r29['record_data'][:32].hex()}")

# Check which records have fixup stubs (gap > 50 bytes)
print("\n=== Records with significant fixup stubs (gap > 50) ===")
for id in sorted(record_map.keys()):
    r = record_map[id]
    if r['gap_size'] > 50:
        print(f"  id={id:3d} seg={r['seg']:04x} gap={r['gap_size']:4d} B={r['B']:4d} C={r['C']:04x}")