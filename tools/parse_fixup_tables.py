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

# Parse fixup tables from record ends
for r in sorted_recs:
    if r['B'] == 0 or r['A'] < r['B']:
        continue
    off, A, B = r['off'], r['A'], r['B']
    code_size = A - B
    fixup_table_off = off + code_size  # offset in tail
    fixup_data = t[fixup_table_off:fixup_table_off + B]
    
    # Parse as words (16-bit offsets within the code segment)
    words = struct.unpack(f'<{B//2}H', fixup_data[:B - B%2])
    
    # Filter valid offsets (within code_size)
    valid_fixups = [(i, w) for i, w in enumerate(words) if 0 <= w < code_size]
    
    entries = B // 2 if B >= 2 else 0
    ratio = len(valid_fixups) / entries * 100 if entries > 0 else 0
    print(f"id={r['id']:3d} seg={r['seg']:04x} code={code_size:5d} fixup_bytes={B:4d} entries={entries:4d} valid={len(valid_fixups):4d} ratio={ratio:.1f}%")
    if valid_fixups:
        print(f"  First 16 valid: {[(idx, f'{w:04x}') for idx, w in valid_fixups[:16]]}")

# Also check the fixup stub code (gap) for patterns
print("\n=== Fixup stub code analysis ===")
sorted_recs = sorted([r for r in recs if r['A'] > 0], key=lambda x: x['off'])
for i in range(len(sorted_recs)-1):
    r = sorted_recs[i]
    next_r = sorted_recs[i+1]
    gap = next_r['off'] - (r['off'] + r['A'])
    if gap > 10:
        gap_data = t[r['off']+r['A']:next_r['off']]
        # Look for INT 21h, segment register loads, etc.
        has_int21 = b'\xcd\x21' in gap_data
        has_seg_load = any(b in gap_data for b in [0x8e, 0x8c])  # MOV seg, ...
        has_pop = any(b in gap_data for b in [0x07, 0x1f, 0x06, 0x0e, 0x17, 0x1f, 0x58, 0x59, 0x5a, 0x5b, 0x5c, 0x5d, 0x5e, 0x5f])
        print(f"id={r['id']:3d} gap={next_r['off']-(r['off']+r['A']):4d} int21={has_int21} seg_load={has_seg_load} pop={has_pop}  {gap_data[:32].hex()}")