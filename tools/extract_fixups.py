#!/usr/bin/env python3
"""
Extract RTLink overlay records with their fixup stubs.
Each record's fixup stub is the gap to the next record in FILE OFFSET order.
"""
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

# Sort by file offset
sorted_recs = sorted([r for r in recs if r['A'] > 0], key=lambda x: x['off'])

# Build complete record map with fixup stubs
records = {}
for i, r in enumerate(sorted_recs):
    off, A, B, C, seg, id = r['off'], r['A'], r['B'], r['C'], r['seg'], r['id']
    end = off + A
    
# Fixup stub is gap to next record in FILE OFFSET ORDER
    next_r = sorted_recs[i+1] if i+1 < len(sorted_recs) else None
    if next_r:
        fixup_off = off + A
        fixup_size = next_r['off'] - fixup_off
        fixup_data = t[fixup_off:next_r['off']] if fixup_off < next_r['off'] else b''
        fixup_next_id = next_r['id']
    else:
        fixup_off = off + A
        fixup_size = 0
        fixup_data = b''
        fixup_next_id = None
    
    record_data = t[off:off+A]
    
    # Detect entry table (repeated segment in first words)
    sample = record_data[:min(A, 64)]
    if len(sample) % 2: sample = sample[:-1]
    word_count = len(sample) // 2
    words = struct.unpack(f'<{word_count}H', sample)
    repeated_seg = None
    if len(words) >= 4:
        segs = [w for w in words[::2]]
        if all(s == segs[0] for s in segs):
            repeated_seg = segs[0]
    
    records[id] = dict(
        id=id, seg=seg, off=off, A=A, B=B, C=C,
        record_data=record_data.hex(),
        record_size=A,
        fixup_off=fixup_off,
        fixup_size=fixup_size,
        fixup_data=fixup_data.hex(),
        fixup_next_id=fixup_next_id,
        repeated_seg=repeated_seg,
        has_entry_table=repeated_seg is not None,
        segment_group=C,
    )

# Save complete record map
out = Path('analysis/ida_falconcd/rtlink_records.json')
out.parent.mkdir(parents=True, exist_ok=True)
with open(out, 'w') as f:
    json.dump(records, f, indent=1)

print(f"Extracted {len(records)} records with fixup stubs to {out}")

# Summary by segment group
groups = {}
for id, r in records.items():
    c = r['segment_group']
    if c not in groups:
        groups[c] = []
    groups[c].append(r)

print("\nRecords by segment group (C):")
for c in sorted(groups.keys()):
    gr = groups[c]
    total_A = sum(r['A'] for r in gr)
    total_fixup = sum(r['fixup_size'] for r in gr)
    segs = set(r['seg'] for r in gr)
    print(f"  C={c:04x}: {len(gr)} records, {total_A} code bytes, {total_fixup} fixup bytes, segs={sorted(segs)}")

# Records with entry tables
print("\nRecords with entry tables:")
for id, r in records.items():
    if r['has_entry_table']:
        sample = bytes.fromhex(r['record_data'])[:64]
        words = struct.unpack(f'<{len(sample)//2}H', sample[:64])
        entries = [(words[i], words[i+1]) for i in range(0, len(words), 2)][:8]
        print(f"  id={r['id']:3d} seg={r['seg']:04x} rep_seg={r['repeated_seg']:04x} entries={len(bytes.fromhex(r['record_data']))//4} first={entries[:4]}")

# Large fixup stubs
print("\nLarge fixup stubs (>200 bytes):")
for id, r in records.items():
    if r['fixup_size'] > 200:
        print(f"  id={r['id']:3d} seg={r['seg']:04x} fixup={r['fixup_size']:4d} next_id={r['fixup_next_id']}")

# Save binary fixup stubs for analysis
fixup_dir = Path('analysis/ida_falconcd/fixup_stubs')
fixup_dir.mkdir(parents=True, exist_ok=True)
for id, r in records.items():
    if r['fixup_size'] > 0:
        fixup_data = bytes.fromhex(r['fixup_data'])
        (fixup_dir / f"fixup_id{id:03d}_next{r['fixup_next_id']}.bin").write_bytes(fixup_data)

print(f"\nSaved {len([r for r in records.values() if r['fixup_size']>0])} fixup stubs to {fixup_dir}")