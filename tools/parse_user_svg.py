#!/usr/bin/env python3
"""Parse user's hand-drawn Israel coastline SVG."""
import re

svg = r'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="210mm" height="297mm" viewBox="0 0 210 297" version="1.1" xmlns="http://www.w3.org/2000/svg">
  <g id="layer1">
    <path d="M 1.8655779,199.61683 14.924623,187.67713" id="path994" />
    <path d="M 14.924623,187.67713 57.459797,175.36432" id="path996" />
    <path d="M 57.459797,175.36432 94.025124,95.890703 97.383166,95.144472 124.6206,32.08794" id="path998" />
    <path d="M 124.6206,32.087939 134.69472,-7.8354271" id="path1000" />
    <path d="m 134.69472,-7.8354271 7.0892,-29.8492449" id="path1002" />
    <path d="m 141.78392,-37.684672 9.701,-73.876888" id="path1006" />
    <path d="m 151.48492,-111.56156 17.16332,0.37312" id="path1008" />
    <path d="m 168.64824,-111.18844 9.701,-80.59296" id="path1012" />
    <path d="m 182.0804,-195.51256 23.13316,-28.35679" id="path1014" />
    <path d="m 205.21356,-223.86935 22.38694,-128.72487 27.23744,-34.32663" id="path1016" />
    <path d="m 254.83794,-386.92084 8.95477,-80.21987" id="path1018" />
    <path d="m 263.79271,-467.14071 -1.86558,-47.38565" id="path1020" />
    <path d="m 261.92713,-514.52636 33.58041,-1.11935" id="path1022" />
    <path d="M 295.50754,-515.64571 324.23743,-594" id="path1026" />
    <path d="m 324.23743,-594 -25.37185,-32.46104" id="path1028" />
    <path d="m 298.86558,-626.46104 23.87938,-45.14699" id="path1030" />
    <path d="m 322.74496,-671.60803 35.81911,-29.47612" id="path1032" />
    <path d="M 358.56407,-701.08415 451.46983,-807.4221" id="path1034" />
    <path d="m 451.46983,-807.4221 -83.57788,-214.9146 64.92212,-264.1658 -73.87688,-213.4221" id="path1036" />
    <path d="M 358.93719,-1499.9246 216.40703,-1661.1105" id="path1038" />
    <path d="m 216.40703,-1661.1105 187.30403,-223.1232" id="path1040" />
    <path d="M 403.71106,-1884.2337 273.86682,-2184.2186" id="path1042" />
  </g>
</svg>'''

# Extract path coordinates
paths = re.findall(r'd="([^"]*)"', svg)

all_points = []
for i, path in enumerate(paths):
    # Parse path commands
    tokens = re.findall(r'[MmLlCcZz]|-?\d+\.?\d*', path)
    print(f'Path {i}: {tokens[:20]}...')
    
    x = y = 0
    j = 0
    while j < len(tokens):
        cmd = tokens[j]
        if cmd in ('M', 'm'):
            j += 1
            if j + 1 < len(tokens):
                dx = float(tokens[j]); dy = float(tokens[j+1])
                if cmd == 'M':
                    x, y = dx, dy
                else:
                    x += dx; y += dy
                all_points.append((x, y))
                j += 2
        elif cmd in ('L', 'l'):
            j += 1
            while j + 1 < len(tokens) and tokens[j] not in ('M', 'm', 'L', 'l', 'C', 'c', 'Z', 'z'):
                dx = float(tokens[j]); dy = float(tokens[j+1])
                if cmd == 'L':
                    x, y = dx, dy
                else:
                    x += dx; y += dy
                all_points.append((x, y))
                j += 2
        elif cmd in ('C', 'c'):
            # Skip cubic bezier for now
            j += 7
        elif cmd in ('Z', 'z'):
            pass
        else:
            j += 1

print(f'\nTotal points: {len(all_points)}')
print('First 20 points:')
for i, (x, y) in enumerate(all_points[:20]):
    print(f'  {i}: ({x:.2f}, {y:.2f})')
print('Last 20 points:')
for i, (x, y) in enumerate(all_points[-20:]):
    print(f'  {len(all_points)-20+i}: ({x:.2f}, {y:.2f})')

# Coordinate ranges
xs = [p[0] for p in all_points]
ys = [p[1] for p in all_points]
print(f'\nX range: {min(xs):.2f} to {max(xs):.2f}')
print(f'Y range: {min(ys):.2f} to {max(ys):.2f}')