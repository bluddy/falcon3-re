import struct

with open('game/OBJECTS', 'rb') as f:
    d = f.read()

off = struct.unpack_from('<I', d, 12)[0]
f16 = d[off:off+3124]

blocks = [
    (0, 0x0232, 0x0288),
    (1, 0x028a, 0x02de),
    (2, 0x02e0, 0x0330),
    (3, 0x0332, 0x0382),
    (4, 0x0384, 0x03ce),
    (5, 0x03d0, 0x041a),
    (6, 0x041c, 0x0466),
    (7, 0x0468, 0x04c6),
]

all_unique_ptrs = set()
for b_idx, start, end in blocks:
    ptrs = []
    for p in range(start, end, 2):
        val = struct.unpack_from('<H', f16, p)[0]
        ptrs.append(val)
        all_unique_ptrs.add(val)
    terminator = struct.unpack_from('<H', f16, end)[0]
    print(f"Block {b_idx} ({start:#06x}..{end:#06x}): {len(ptrs)} pointers, term={terminator:#06x}")
    print(f"   ptrs: {[f'{x:#06x}' for x in ptrs]}")

print(f"\nTotal unique polygon pointers across all 8 blocks: {len(all_unique_ptrs)}")
print(f"Min pointer: {min(all_unique_ptrs):#06x}, Max pointer: {max(all_unique_ptrs):#06x}")
