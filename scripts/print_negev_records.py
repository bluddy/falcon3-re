import struct

with open('game/ISLDAT.ISR', 'rb') as f:
    raw = f.read()
body = raw[9:]

def print_rec_details(r):
    tx = struct.unpack_from('<i', body, r)[0] / 65536.0
    ty = struct.unpack_from('<i', body, r+4)[0] / 65536.0
    attr = struct.unpack_from('<H', body, r+0x20)[0]
    pc = struct.unpack_from('<H', body, r+0x2E)[0]
    pts = [struct.unpack_from('<hhh', body, r+0x38+6*i) for i in range(pc)]
    print(f"\nRec 0x{r:04X} a=0x{attr:02X} tx={tx:.2f} ty={ty:.2f} ({pc} pts):")
    for i, p in enumerate(pts):
        # Local y=p[0], x=p[2]
        print(f"  pt {i:2d}: local (y={p[0]:6d}, x={p[2]:6d}) -> world (X={tx+p[2]/2000.0:.2f}, Y={ty+p[0]/2000.0:.2f})")

for r in [0x1192, 0x11FE, 0x1284, 0x1302, 0x13E2, 0x1478]:
    print_rec_details(r)
