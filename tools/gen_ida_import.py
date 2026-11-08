#!/usr/bin/env python3
"""Generate IDC script for IDA with all ISLDAT analysis."""
import struct

with open('game/ISLDAT.ISR', 'rb') as f:
    data = f.read()
body = data[9:]

gridB = body[0x000:0x000+4*256]
t1_base = struct.unpack_from('<H', data, 4)[0]
t1_table = body[t1_base:]

idc = []
idc.append('// ISLDAT.ISR Analysis for IDA')
idc.append('// Generated automatically')
idc.append('')

# Coastline records
for quad in range(4):
    row_data = gridB[quad*256:(quad+1)*256]
    for col in range(256):
        t1_idx = row_data[col]
        if t1_idx != 0:
            t1_off = t1_idx * 2
            if t1_off < len(t1_table):
                rec_off = struct.unpack_from('<H', t1_table, t1_off)[0]
                if rec_off != 0xFFFF and rec_off < len(body):
                    attr20 = struct.unpack_from('<H', body, rec_off + 0x20)[0] if rec_off + 0x20 < len(body) else 0xFFFF
                    if attr20 != 0xffff and attr20 < len(body):
                        coast_attr = struct.unpack_from('<H', body, attr20 + 0x20)[0] if attr20 + 0x20 < len(body) else 0xFFFF
                        if coast_attr == 0x14:
                            x, y, z = struct.unpack_from('<iii', body, attr20)
                            pts_off = attr20 + 0x38
                            pts = []
                            for i in range(200):
                                if pts_off + 6 > len(body): break
                                px, mid, py = struct.unpack_from('<hhh', body, pts_off)
                                if mid != 0: break
                                pts.append((px, py))
                                pts_off += 6
                                if len(pts) > 200: break
                            if pts:
                                idc.append('// Coast {} at Grid[{},{}] {} pts'.format(attr20, quad, col, len(pts)))
                                idc.append('MakeUnknown(0x{:X}, 0x40, 0);'.format(attr20))
                                idc.append('OpAlt(0x{:X}, 0, "Coast_{:X}");'.format(attr20, attr20))
                                for i, (px, py) in enumerate(pts):
                                    idc.append('OpAlt(0x{:X}, 0, "pt{}_x");'.format(attr20 + 0x38 + i*6, i))
                                    idc.append('OpAlt(0x{:X}, 0, "pt{}_y");'.format(attr20 + 0x38 + i*6 + 2, i))
                                    idc.append('OpAlt(0x{:X}, 0, "pt{}_mid");'.format(attr20 + 0x38 + i*6 + 4, i))

# Orphans
orphans = [0x08ca, 0x0e80, 0x1192, 0x1542, 0x1956, 0x19f4]
idc.append('')
idc.append('// ===== ORPHAN COASTLINE RECORDS (not in grid) =====')
for r_off in orphans:
    x, y, z = struct.unpack_from('<iii', body, r_off)
    pts_off = r_off + 0x38
    pts = []
    for i in range(200):
        if pts_off + 6 > len(body): break
        px, mid, py = struct.unpack_from('<hhh', body, pts_off)
        if mid != 0: break
        pts.append((px, py))
        pts_off += 6
        if len(pts) > 200: break
    tx = x / 65536.0
    ty = y / 65536.0
    idc.append('// Orphan {:06x}: Tile=({:.2f},{:.2f}) {} pts'.format(r_off, tx, ty, len(pts)))
    idc.append('MakeUnknown(0x{:X}, 0x40, 0);'.format(r_off))
    idc.append('MakeStruct(0x{:X}, "ISLDAT_Record");'.format(r_off))

# Rivers
idc.append('')
idc.append('// ===== RIVER RECORDS (attr 0x32) =====')
river_offsets = [0x08e8, 0x096e, 0x09f4, 0x0a58, 0x0ace, 0x0b32, 0x0ba8, 0x0c0c, 0x0c70, 0x0cd4, 0x0db2]
for r_off in river_offsets:
    x, y, z = struct.unpack_from('<iii', body, r_off)
    pts_off = r_off + 0x38
    pts = []
    for i in range(200):
        if pts_off + 6 > len(body): break
        px, mid, py = struct.unpack_from('<hhh', body, pts_off)
        if mid != 0: break
        pts.append((px, py))
        pts_off += 6
        if len(pts) > 200: break
    idc.append('// River {:06x}: {} pts'.format(r_off, len(pts)))
    idc.append('MakeUnknown(0x{:X}, 0x40, 0);'.format(r_off))
    idc.append('MakeStruct(0x{:X}, "ISLDAT_Record");'.format(r_off))

# Write IDC file
import os
os.makedirs('analysis/ida_import', exist_ok=True)
with open('analysis/ida_import/isldat_isr.idc', 'w') as f:
    f.write('\n'.join(idc))

print('Wrote analysis/ida_import/isldat_isr.idc')
print('Lines:', len(idc))