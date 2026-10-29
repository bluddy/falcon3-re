#!/usr/bin/env python3
"""Extract coastline from tile edges - find boundary of union."""
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

# Extract all edges from all tiles
edge_to_tiles = defaultdict(list)
for coast_off, (tx, ty, pts) in med_tiles.items():
    world_pts = [(tx + px/65536.0, ty + py/65536.0) for px, py in pts]
    west_pts = [p for p in world_pts if p[0] < -5]
    if len(west_pts) < 3:
        continue
    for i in range(len(west_pts)):
        p1 = west_pts[i]
        p2 = west_pts[(i + 1) % len(west_pts)]
        if p1 < p2:
            edge = (p1, p2)
        else:
            edge = (p2, p1)
        edge_to_tiles[edge].append(coast_off)

print("Edge analysis:")
boundary_edges = []
internal_edges = []
for edge, tiles in edge_to_tiles.items():
    if len(tiles) == 1:
        boundary_edges.append(edge)
    else:
        internal_edges.append(edge)

print(f"Total edges: {len(edge_to_tiles)}")
print(f"Boundary edges (coastline): {len(boundary_edges)}")
print(f"Internal edges (shared): {len(internal_edges)}")

# Now connect boundary edges into continuous paths
# Build adjacency: vertex -> edges
vertex_to_edges = defaultdict(list)
for edge in boundary_edges:
    p1, p2 = edge
    vertex_to_edges[p1].append((p2, edge))
    vertex_to_edges[p2].append((p1, edge))

print(f"\nVertices on boundary: {len(vertex_to_edges)}")

# Trace paths from boundary edges
visited_edges = set()
paths = []

for edge in boundary_edges:
    if edge in visited_edges:
        continue
    # Start a new path
    path = []
    current_edge = edge
    current_vertex = current_edge[1]  # start from p2
    
    while current_edge not in visited_edges:
        visited_edges.add(current_edge)
        p1, p2 = current_edge
        path.append(p1)
        current_vertex = p2
        
        # Find next edge from current_vertex
        next_edges = [e for e in vertex_to_edges[current_vertex] if e[1] not in visited_edges]
        if not next_edges:
            break
        # Choose the edge that continues the path
        next_edge = next_edges[0][1]
        current_edge = next_edge
    
    if len(path) > 2:
        paths.append(path)

print(f"\nFound {len(paths)} boundary paths:")
for i, path in enumerate(paths):
    print(f"  Path {i}: {len(path)} vertices")
    for p in path[:5]:
        print(f"  {p}")
    if len(path) > 5:
        print(f"  ...")
    for p in path[-3:]:
        print(f"  {p}")