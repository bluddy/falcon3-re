import struct

with open('game/OBJECTS', 'rb') as f:
    d = f.read()

off = struct.unpack_from('<I', d, 12)[0]
f16 = d[off:off+3124]

# Let's inspect each of the 8 blocks and see what polygons are drawn in each block
# The 8 blocks in LOD 0:
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

for b_idx, start, end in blocks:
    ptrs = []
    for p in range(start, end, 2):
        val = struct.unpack_from('<H', f16, p)[0]
        if val == 0xffff: break
        ptrs.append(val)
    print(f"Block {b_idx}: {len(ptrs)} pointers")
    # For each pointer, let's see what record it points to
    polys = []
    for ptr in ptrs:
        # Check if ptr points into 0x4c6..0x874
        if 0x4c6 <= ptr < 0x874:
            # Let's parse the record at ptr
            # Remember in FalconCD assembly:
            # SI = ptr
            # lodsw -> word0 (flags)
            # if flags & 0x1000: chained subrecords!
            # lodsb -> col1
            # lodsb -> col2
            # di = word [si]
            w0 = struct.unpack_from('<H', f16, ptr)[0]
            is_chained = bool(w0 & 0x1000)
            col1, col2 = struct.unpack_from('<2B', f16, ptr + 2)
            # If chained, loop subrecords
            sub_recs = []
            if is_chained:
                cur_si = ptr + 4
                while cur_si + 2 <= len(f16):
                    di = struct.unpack_from('<h', f16, cur_si)[0]
                    if di == -1: break
                    cnt = di
                    v_words = struct.unpack_from(f'<{cnt+1}H', f16, cur_si + 2)
                    sub_recs.append((cnt, [w // 16 for w in v_words]))
                    cur_si += (cnt + 2) * 2
            else:
                cnt = struct.unpack_from('<H', f16, ptr + 4)[0]
                if 3 <= cnt <= 8 and ptr + 6 + (cnt+1)*2 <= len(f16):
                    v_words = struct.unpack_from(f'<{cnt+1}H', f16, ptr + 6)
                    sub_recs.append((cnt, [w // 16 for w in v_words]))
            polys.append((ptr, w0, col1, is_chained, len(sub_recs)))
    print(f"   Parsed {len(polys)} polygon objects. Sample: {polys[:4]}")
