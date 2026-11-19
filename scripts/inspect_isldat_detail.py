import struct

with open('game/ISLDAT.ISR', 'rb') as f:
    raw = f.read()

body = raw[9:]
t1, t2 = struct.unpack_from('<HH', raw, 4)

def u16(o): return struct.unpack_from('<H', body, o)[0]
def i16(o): return struct.unpack_from('<h', body, o)[0]
def i32(o): return struct.unpack_from('<i', body, o)[0]

print(f"t1={t1:04X}, t2={t2:04X}, len(body)={len(body)}")

# Let's inspect the first 3 records in ISLDAT.ISR
# First let's find the record offsets from T1 and T2
t1_recs = []
o = t1
while o + 2 <= len(body):
    v = u16(o)
    o += 2
    if v == 0xFFFF: break
    lo = v
    while lo + 2 <= len(body):
        r = u16(lo)
        lo += 2
        if r == 0xFFFF: break
        t1_recs.append(r)

print(f"T1 records ({len(t1_recs)}): {[hex(r) for r in t1_recs[:10]]}")

for r in t1_recs[:5]:
    x = i32(r) / 65536.0
    y = i32(r+4) / 65536.0
    z = i32(r+8) / 65536.0
    attr = u16(r + 0x20)
    w22 = u16(r + 0x22)
    w24 = u16(r + 0x24)
    w26 = u16(r + 0x26)
    w28 = u16(r + 0x28)
    w2A = u16(r + 0x2A)
    w2C = u16(r + 0x2C)
    w2E = u16(r + 0x2E)
    w30 = u16(r + 0x30)
    w32 = u16(r + 0x32)
    w34 = u16(r + 0x34)
    w36 = u16(r + 0x36)
    print(f"\n--- Record 0x{r:04X} ---")
    print(f"X={x:.2f}, Y={y:.2f}, Z={z:.2f}")
    print(f"attr(+20)={attr:04X}, +22={w22:04X}, +24={w24:04X}, +26={w26:04X}, +28={w28:04X}")
    print(f"+2A={w2A:04X}, +2C={w2C:04X}, +2E={w2E:04X}, +30={w30:04X}, +32={w32:04X}, +34={w34:04X}, +36={w36:04X}")
    
    # Check what [di+22h] points to:
    if w22 < len(body):
        p1 = u16(w22)
        p2 = u16(w22+2)
        p3 = u16(w22+4)
        print(f"[+22h] -> {w22:04X}: [0]={p1:04X}, [2]={p2:04X}, [4]={p3:04X}")
        if p3 < len(body):
            q1 = u16(p3)
            q2 = u16(p3+2)
            q3 = u16(p3+4)
            print(f"  [[+22h]+4] -> {p3:04X}: [0]={q1:04X}, [2]={q2:04X}, [4]={q3:04X}")
