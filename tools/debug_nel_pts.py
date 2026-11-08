#!/usr/bin/env python3
import sys, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('game/ISLDAT.NEL', 'rb') as f:
    data = f.read()
body = data[9:]

r_off = 0x051C
pts_off = r_off + 0x38

for i in range(50):
    if pts_off + 6 > len(body): break
    px, mid, py = struct.unpack_from('<hhh', body, pts_off)
    print(f'pt {i}: ({px}, {py}) mid={mid}')
    pts_off += 6
    if i > 100: break