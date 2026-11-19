import struct
from collections import deque

with open('game/ISRAEL.MAP', 'rb') as f:
    w, h = struct.unpack('<HH', f.read(4))
    raw = f.read(w * h)

# Connected components of water (tile < 40)
visited = set()
components = []

for y in range(h):
    for x in range(w):
        if (x, y) not in visited and raw[y * w + x] < 40:
            # BFS
            comp = []
            queue = deque([(x, y)])
            visited.add((x, y))
            while queue:
                cx, cy = queue.popleft()
                comp.append((cx, cy))
                for nx, ny in [(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)]:
                    if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited and raw[ny * w + nx] < 40:
                        visited.add((nx, ny))
                        queue.append((nx, ny))
            components.append(comp)

# Sort by size
components.sort(key=len, reverse=True)
print(f"Total water components in ISRAEL.MAP: {len(components)}")
for i, comp in enumerate(components[:10]):
    xs = [p[0] for p in comp]
    ys = [p[1] for p in comp]
    print(f"Water #{i}: size={len(comp)} tiles, X=[{min(xs):3d}..{max(xs):3d}], Y=[{min(ys):3d}..{max(ys):3d}]")
