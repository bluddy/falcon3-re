import struct

with open('game/ISLDAT.ISR', 'rb') as f:
    raw = f.read()

body = raw[9:]

def check_rec(r):
    tx = struct.unpack_from('<i', body, r)[0] / 65536.0
    ty = struct.unpack_from('<i', body, r+4)[0] / 65536.0
    pc = struct.unpack_from('<H', body, r+0x2E)[0]
    pts = [struct.unpack_from('<hhh', body, r+0x38+6*i) for i in range(pc)]
    return tx, ty, pts

tx1, ty1, pts1 = check_rec(0x0F06)
tx2, ty2, pts2 = check_rec(0x0F6C)

print(f"Rec 0x0F06: tx={tx1:.2f}, ty={ty1:.2f}")
print("Points as (w0=Y, w2=X):")
for p in pts1:
    wy = ty1 + p[0] / 2000.0
    wx = tx1 + p[2] / 2000.0
    print(f"   local: y={p[0]:6d}, x={p[2]:6d} -> world: (X={wx:.3f}, Y={wy:.3f})")

print(f"\nRec 0x0F6C: tx={tx2:.2f}, ty={ty2:.2f}")
print("Points as (w0=Y, w2=X):")
for p in pts2:
    wy = ty2 + p[0] / 2000.0
    wx = tx2 + p[2] / 2000.0
    print(f"   local: y={p[0]:6d}, x={p[2]:6d} -> world: (X={wx:.3f}, Y={wy:.3f})")
