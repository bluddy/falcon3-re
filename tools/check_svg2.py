import sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('analysis/isldat_svgs_final/ISLDAT_NEL_coastline.svg', 'r', encoding='utf-8') as f:
    content = f.read()

import re
paths = re.findall(r'<path d="([^"]*)"', content)
for i, path in enumerate(paths):
    coords = re.findall(r'[ML]\s+([-\d.]+)\s+([-\d.]+)', path)
    print(f'Path {i}: {len(coords)} coords')
    print('  First few:', coords[:5])