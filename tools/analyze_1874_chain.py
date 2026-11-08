#!/usr/bin/env python3
"""Visualize the connectivity from sub-record chain for tile 0x1874."""
import struct, os

with open('game/ISLDAT.ISR', 'rb') as f:
    data = f.read()
body = data[9:]

gridB = body[0x000:0x000+4*256]
t1_base = struct.unpack_from('<H', data, 4)[0]
t1_table = body[t1_base:]

quad = 0
col = 150
row_data = gridB[quad*256:(quad+1)*256]
t1_idx = row_data[col]
t1_off = row_data[col] * 2
rec_off = struct.unpack_from('<H', t1_table, t1_off)[0]
attr20 = struct.unpack_from('<H', body, rec_off + 0x20)[0]

x, y, z = struct.unpack_from('<iii', body, attr20)
tx = x / 65536.0
ty = y / 65536.0

pts_off = attr20 + 0x38
pts = []
for i in range(200):
    if pts_off + 6 > len(body): break
    px, mid, py = struct.unpack_from('<hhh', body, pts_off)
    if mid != 0: break
    pts.append((px, py))
    pts_off += 6
    if len(pts) > 200: break

world_pts = [(tx + px/65536.0, ty + py/65536.0) for px, py in pts]

# Sub-record chain nodes (divided by 16 for line table indices)
# From sub-record 0 at offset 0x1918
chain_nodes = [0x1000, 0x0001, 0x0006, 0x0000, 0x0010, 0x0020, 0x0090, 0x00a0, 0x00b0, 0x0000, 0x0008, 0x0020, 0x0030, 0x0040, 0x0050, 0x0060, 0x0070, 0x0080, 0x0090, 0x0020, 0x0006, 0x00c0, 0x00d0, 0x00e0, 0x00f0, 0x0100, 0x0110, 0x00c0]

# Divide by 16 to get line table entry indices
chain_indices = [n // 16 for n in chain_nodes]

# Skip first 4 header values
chain = chain_indices[4:]

print("Line table entry indices from sub-record chain:")
for i, idx in enumerate(chain):
    if idx == 0xFFFF:
        print(f"  {i}: END")
    else:
        print(f"  {i}: {idx}")

# Now let's see what these indices might mean
# They could be indices into the line table built by the grid walk
# Each line table entry = 16 bytes = 8 words
# The line table is built at 0x441E by line_draw_441e

# The user says: points 0-11 = main body (closes 11->0), points 12-17 = small body (closes 17->12)
# Let's see if the chain indices correspond to point indices

print("Chain indices (after header):")
for i, idx in enumerate(chain):
    if idx == 0xFFFF:
        print(f"  {i}: END")
    else:
        print(f"  {i}: {idx}")

# The user says: main body points 0-11 (closes 11->0), small body 12-17 (closes 17->12)
# Let's see if the chain indices match point indices
# Point indices are 0-17

print("\nPoint mapping:")
for i, (wx, wy) in enumerate([(tx + px/65536.0, ty + py/65536.0) for px, py in pts]):
    print(f"  Point {i}: ({wx:.4f}, {wy:.4f})")

# The chain indices (divided by 16) are: 1, 2, 9, 10, 11, 0, 8, 2, 3, 4, 5, 6, 7, 8, 9, 2, 6, 12, 13, 14, 15, 16, 17, 12
# These are line table entry indices, not point indices directly
# But notice: 0-11 appear (main body points), 12-17 appear (small body points)

print("\nChain indices that are point indices (0-17):")
point_indices = [idx for idx in chain if idx <= 17]
print(f"  Found: {sorted(set(point_indices))}")

# The sequence visits point indices in some order
# Let's trace the implied line segments
print("\nImplied line segments from chain (consecutive pairs):")
for i in range(len(chain)-1):
    if chain[i] <= 17 and chain[i+1] <= 17:
        print(f"  {chain[i]} -> {chain[i+1]}")