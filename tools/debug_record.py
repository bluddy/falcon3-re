#!/usr/bin/env python3
import sys, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('game/ISLDAT.ISR', 'rb') as f:
    data = f.read()
body = data[9:]

r_off = 0x08CA
print(f'r_off=0x{r_off:04X}')
attr = struct.unpack_from('<H', open('game/ISLDAT.ISR','rb').read()[9:], r_off + 0x20)[0]
print(f'attr=0x{attr:04X}')

with open('game/ISLDAT.ISR','rb') as f:
    data = f.read()
body = data[9:]

pc = struct.unpack_from('<H', open('game/ISLDAT.ISR','rb').read()[9:], 0x08CA + 0x2E)[0]
print(f'pc at 0x2E = {pc}')
pc2 = struct.unpack_from('<H', open('game/ISLDAT.ISR','rb').read()[9:], 0x08CA + 0x2C)[0]
print(f'pc at 0x2C = {pc2}')

# Check all 2-byte values around the header
with open('game/ISLDAT.ISR','rb') as f:
    data = f.read()
body = data[9:]
for i in range(0x20, 0x48, 2):
    v = struct.unpack_from('<H', open('game/ISLDAT.ISR','rb').read()[9:], 0x08CA + i)[0]
    print(f'  +0x{i:02X}: 0x{v:04X} ({v})')

# Check points
pts_off = 0x08CA + 0x38
with open('game/ISLDAT.ISR','rb') as f:
    data = f.read()
body = data[9:]
pts_off = 0x08CA + 0x38
for i in range(5):
    if pts_off + 6 > len(open('game/ISLDAT.ISR','rb').read()[9:]):
        break
    px, mid, py = struct.unpack_from('<hhh', open('game/ISLDAT.ISR','rb').read()[9:], pts_off)
    print(f'  pt: ({px}, {py}) mid={mid}')
    pts_off += 6