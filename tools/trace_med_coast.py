#!/usr/bin/env python3
"""Build continuous Mediterranean coastline from all 4 quadrants."""
import struct
from collections import defaultdict

with open('game/ISLDAT.ISR', 'rb') as f:
    data = f.read()
body = data[9:]

gridB = body[0x000:0x000+4*256]
t1_base = struct.unpack_from('<H', data, 4)[0]
t1_table = body[t1_base:]

# Collect ALL Mediterranean tiles from all 4 quadrants
med_tiles = {}  # coast_off -> (col, quad, tx, ty, pts)
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
                            if tx < -5:  # Mediterranean
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
                                        med_tiles[attr20] = (col, quad, tx, ty, pts)

print(f"Unique Mediterranean tiles: {len(med_tiles)}")
for coast_off, (col, quad, tx, ty, pts) in med_tiles.items():
    print(f"  Coast {coast_off:#06x} Grid[{quad},{col:3d}] Tile=({tx:7.2f},{ty:7.2f}) pts={len(pts)}")

# Build vertex -> tile mapping
vertex_to_tiles = defaultdict(list)
for coast_off, (col, quad, tx, ty, pts) in med_tiles.items():
    for px, py in pts:
        wx = tx + px / 65536.0
        wy = ty + py / 65536.0
        if wx < -5:
            key = (round(wx, 3), round(wy, 3))
            vertex_to_tiles[key].append(coast_off)

# Find shared vertices
shared = {k: v for k, v in vertex_to_tiles.items() if len(v) > 1}
print(f"\nShared vertices: {len(shared)}")
for vertex, coast_offs in shared.items():
    if len(coast_offs) > 1:
        print(f"  {vertex}: {coast_offs}")

# Build adjacency graph
adj = defaultdict(set)
for vertex, coast_offs in shared.items():
    if len(coast_offs) >= 2:
        for c1 in coast_offs:
            for c2 in coast_offs:
                if c1 != c2:
                    adj[c1].add(c2)

print(f"\nAdjacency graph:")
for c1 in sorted(adj.keys()):
    print(f"  {c1:#06x} -> {sorted(adj[c1])}")

# Find tile with minimum Y (southernmost)
min_y = float('inf')
start_tile = None
for coast_off, (col, quad, tx, ty, pts) in med_tiles.items():
    for px, py in pts:
        wy = ty + py / 65536.0
        if wy < min_y:
            min_y = wy
            start_tile = coast_off

print(f"\nSouthernmost tile: {start_tile:#06x} at Y={min_y:.2f}")

# Walk the adjacency graph from south to north
visited = set()
path_tiles = []
current = start_tile
prev = None

for _ in range(20):
    if current in visited:
        break
    visited.add(current)
    path_tiles.append(current)
    
    neighbors = [n for n in adj[current] if n != prev and n not in visited]
    if not neighbors:
        break
    
    # Choose neighbor that goes north (higher max Y)
    best = None
    best_y = -float('inf')
    for n in neighbors:
        col, quad, tx, ty, pts = med_tiles[n]
        max_y = max(ty + py/65536.0 for px, py in pts)
        if max_y > best_y:
            best_y = max_y
            best = n
    
    if best is None:
        break
    prev = current
    current = best

print(f"\nTraced {len(path_tiles)} tiles: {[f'{t:#06x}' for t in path_tiles]}")

# Now extract points in order
all_path_pts = []
for coast_off in path_tiles:
    col, quad, tx, ty, pts = med_tiles[coast_off]
    west_pts = [(tx + px/65536.0, ty + py/65536.0) for px, py in pts if (tx + px/65536.0) < -5]
    west_pts.sort(key=lambda p: p[1])  # sort by Y
    all_path_pts.extend(west_pts)

print(f"\nTotal path points: {len(all_path_pts)}")
for i, (wx, wy) in enumerate(all_path_pts):
    print(f"  {i}: ({wx:.3f},{wy:.3f})")