import struct

with open('game/ISLDAT.ISR', 'rb') as f:
    raw = f.read()

body = raw[9:]
t1, t2 = struct.unpack_from('<HH', raw, 4)

def u16(o): return struct.unpack_from('<H', body, o)[0]
def i32(o): return struct.unpack_from('<i', body, o)[0]

def table_extent(base, limit):
    best = 0
    for k in range(1, (limit - base) // 2 + 1):
        if min(u16(base + 2 * j) for j in range(k)) == base + 2 * k:
            best = k
    return [u16(base + 2 * j) for j in range(best)]

recs = set()
for ptr in table_extent(t1, t2) + table_extent(t2, len(body)):
    o = ptr
    while o + 2 <= len(body) and u16(o) != 0xFFFF:
        recs.add(u16(o))
        o += 2

records = []
for r in sorted(recs):
    tx = i32(r) / 65536.0
    ty = i32(r + 4) / 65536.0
    attr = u16(r + 0x20)
    records.append((r, attr, tx, ty))

# Print sorted by ty
print("--- Records sorted by ty ---")
for r, attr, tx, ty in sorted(records, key=lambda x: x[3]):
    print(f"0x{r:04X} a=0x{attr:02X} tx={tx:7.3f} ty={ty:7.3f}")

# Print sorted by tx
print("\n--- Records sorted by tx ---")
for r, attr, tx, ty in sorted(records, key=lambda x: x[2]):
    print(f"0x{r:04X} a=0x{attr:02X} tx={tx:7.3f} ty={ty:7.3f}")
