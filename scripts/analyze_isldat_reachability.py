import struct

with open('game/ISLDAT.ISR', 'rb') as f:
    raw = f.read()

body = raw[9:]
t1, t2 = struct.unpack_from('<HH', raw, 4)

def u16(b, o): return struct.unpack_from('<H', b, o)[0]
def i16(b, o): return struct.unpack_from('<h', b, o)[0]
def i32(b, o): return struct.unpack_from('<i', b, o)[0]

# Grids:
# 0x000..0x400: Grid B (4 quadrants of 256 bytes = 1024 bytes)
# 0x400..0x500: Grid A (4 quadrants of 64 bytes = 256 bytes)

grid_b = body[0x000:0x400]
grid_a = body[0x400:0x500]

print("=== GRID B Analysis ===")
# Which indices in Grid B are non-zero?
grid_b_entries = defaultdict = {}
for q in range(4):
    for idx in range(256):
        val = grid_b[q * 256 + idx]
        if val != 0:
            grid_b_entries[(q, idx)] = val

print(f"Grid B non-zero cells: {len(grid_b_entries)} / 1024")

print("\n=== GRID A Analysis ===")
grid_a_entries = {}
for q in range(4):
    for idx in range(64):
        val = grid_a[q * 64 + idx]
        if val != 0:
            grid_a_entries[(q, idx)] = val
print(f"Grid A non-zero cells: {len(grid_a_entries)} / 256")

# Now let's trace from Grid B -> T1 table -> record lists!
print("\n=== TRACING GRID B -> T1 -> RECORDS ===")
t1_table = body[t1:]
b_records_found = set()
for (q, cell), val in sorted(grid_b_entries.items()):
    t1_off = val * 2
    if t1_off + 2 <= len(t1_table):
        list_ptr = struct.unpack_from('<H', t1_table, t1_off)[0]
        if list_ptr < len(body):
            # walk record list
            o = list_ptr
            while o + 2 <= len(body):
                rec = u16(body, o)
                o += 2
                if rec == 0xFFFF: break
                b_records_found.add((rec, q, cell))

print(f"Unique records reached via Grid B: {len(set(r[0] for r in b_records_found))}")

# Now let's trace from Grid A -> T2 table -> record lists!
print("\n=== TRACING GRID A -> T2 -> RECORDS ===")
t2_table = body[t2:]
a_records_found = set()
for (q, cell), val in sorted(grid_a_entries.items()):
    t2_off = val * 2
    if t2_off + 2 <= len(t2_table):
        list_ptr = struct.unpack_from('<H', t2_table, t2_off)[0]
        if list_ptr < len(body):
            o = list_ptr
            while o + 2 <= len(body):
                rec = u16(body, o)
                o += 2
                if rec == 0xFFFF: break
                a_records_found.add((rec, q, cell))

print(f"Unique records reached via Grid A: {len(set(r[0] for r in a_records_found))}")

# Now print ALL unique records in ISLDAT.ISR and their info:
all_recs = sorted(list(set(r[0] for r in b_records_found) | set(r[0] for r in a_records_found)))
print(f"\nTotal reachable records in ISLDAT.ISR: {len(all_recs)}")

for r in all_recs:
    tx = i32(body, r) / 65536.0
    ty = i32(body, r+4) / 65536.0
    tz = i32(body, r+8) / 65536.0
    attr = u16(body, r + 0x20)
    pc = u16(body, r + 0x2E)
    pts_off = r + 0x38
    pts = [struct.unpack_from('<hhh', body, pts_off + 6 * i) for i in range(pc)]
    xs = [p[0] for p in pts]
    zs = [p[2] for p in pts]
    box = (min(xs), max(xs), min(zs), max(zs)) if xs else (0,0,0,0)
    in_b = [f"Q{q}c{c}" for rec, q, c in b_records_found if rec == r]
    in_a = [f"Q{q}c{c}" for rec, q, c in a_records_found if rec == r]
    print(f"Rec 0x{r:04X}: attr=0x{attr:02X}, tx={tx:6.2f}, ty={ty:6.2f}, pts={pc:2d}, box=[{box[0]:5d}..{box[1]:5d}, {box[2]:5d}..{box[3]:5d}], in_B={len(in_b)}, in_A={len(in_a)}")
