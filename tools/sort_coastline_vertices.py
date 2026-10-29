#!/usr/bin/env python3
"""Extract coastline by sorting all western vertices by Y (south to north)."""
import struct
from collections import defaultdict

with open('game/ISLDAT.ISR', 'rb') as f:
    data = f.read()
body = data[9:]

gridB = body[0x000:0x000+4*256]
t1_base = struct.unpack_from('<H', data, 4)[0]
t1_table = body[t1_base:]

# Collect ALL Mediterranean tiles from all 4 quadrants
med_tiles = {}
for quad in range(4):
    row_data = gridB[quad*256:(quad+1)*256]
    for col, t1_idx in enumerate(row_data):
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
                            tx = x / 65536.0
                            ty = y / 65536.0
                            if tx < -5:
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
                                    if attr20 not in med_tiles:
                                        med_tiles[attr20] = (tx, ty, pts)

print(f"Unique Mediterranean tiles: {len(med_tiles)}")

# Collect ALL western vertices from all tiles
all_west_vertices = []
for coast_off, (tx, ty, pts) in med_tiles.items():
    world_pts = [(tx + px/65536.0, ty + py/65536.0) for px, py in pts]
    west_pts = [p for p in world_pts if p[0] < -5]
    for wx, wy in west_pts:
        all_west_vertices.append((wx, wy, coast_off))

print(f"Total western vertices: {len(all_west_vertices)}")

# Sort by Y (south to north)
all_west_vertices.sort(key=lambda p: p[1])

# Deduplicate nearby points
deduped = []
for wx, wy, coast_off in all_west_vertices:
    if deduped:
        last_wx, last_wy, _ = deduped[-1]
        if abs(wx - last_wx) < 0.02 and abs(wy - last_wy) < 0.02:
            continue
    deduped.append((wx, wy, coast_off))

print(f"Deduped vertices: {len(deduped)}")

# Now sort by Y (south to north)
deduped.sort(key=lambda p: p[1])

# Output the coastline points
print(f"\nCoastline points (south to north):")
for i, (wx, wy, coast_off) in enumerate(deduped):
    print(f"  {i:3d}: ({wx:8.4f}, {wy:8.4f}) Coast {coast_off:#06x}")

# Also try to sort by angle from center for a closed polygon
# Find center
cx = sum(p[0] for p in deduped) / len(deduped)
cy = sum(p[1] for p in deduped) / len(deduped)
print(f"\nCenter: ({cx:.2f}, {cy:.2f})")

# Sort by angle from center
import math
angle_sorted = sorted(deduped, key=lambda p: math.atan2(p[1] - cy, p[0] - cx))

print(f"\nVertices sorted by angle from center:")
for i, (wx, wy, coast_off) in enumerate(angle_sorted):
    angle = math.atan2(wy - cy, wx - cx)
    print(f"  {i:3d}: ({wx:8.4f}, {wy:8.4f}) angle={angle:.3f} Coast {coast_off:#06x}")

import math