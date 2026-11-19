import struct

with open('game/OBJECTS', 'rb') as f:
    d = f.read()

off = struct.unpack_from('<I', d, 12)[0]
f16 = d[off:off+3124]

# Function to parse a polygon record at a given offset
def parse_polygon_record(f16_data, poly_off):
    if poly_off + 4 > len(f16_data):
        return None
    col, cnt = struct.unpack_from('<2H', f16_data, poly_off)
    if not (1 <= col <= 255 and 3 <= cnt <= 8):
        return None
    # Read cnt+1 vertices
    rec_len = 4 + (cnt + 1) * 2 + 2
    if poly_off + rec_len > len(f16_data):
        return None
    v_words = struct.unpack_from(f'<{cnt+1}H', f16_data, poly_off + 4)
    trailing = struct.unpack_from('<H', f16_data, poly_off + 4 + (cnt+1)*2)[0]
    indices = [w // 16 for w in v_words]
    return {
        'offset': poly_off,
        'color': col,
        'count': cnt,
        'v_words': v_words,
        'indices': indices,
        'trailing': trailing
    }

# Check all pointers in Block 0
block0_ptrs = [
    0x0466, 0x04c6, 0x0562, 0x0786, 0x0778, 0x07c2, 0x0794, 0x07b2,
    0x075a, 0x07a2, 0x068a, 0x0642, 0x05ea, 0x060a, 0x04bc, 0x052c,
    0x04d6, 0x05fa, 0x05da, 0x070a, 0x072a, 0x0508, 0x04e6, 0x0856,
    0x083a, 0x07d0, 0x0800, 0x07e0, 0x080e, 0x07f0, 0x082c, 0x06ca,
    0x06ea, 0x04b2, 0x05ba, 0x0594, 0x05aa, 0x06aa, 0x06ba, 0x061a,
    0x066a, 0x05ca, 0x04f6
]

print(f"Parsing {len(block0_ptrs)} records in Block 0:")
for p in block0_ptrs:
    rec = parse_polygon_record(f16, p)
    if rec:
        print(f"  {p:#06x}: col={rec['color']:3d}, cnt={rec['count']}, indices={rec['indices'][:-1]}")
    else:
        # Check raw bytes at p
        raw = f16[p:p+12]
        words = [f'{w:04x}' for w in struct.unpack(f'<{len(raw)//2}H', raw)]
        print(f"  {p:#06x}: NOT A POLYGON RECORD! Raw: {' '.join(words)}")
