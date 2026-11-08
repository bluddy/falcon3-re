import sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('analysis/isldat_svgs_final/ISLDAT_ISR_coastline.svg', 'r', encoding='utf-8') as f:
    content = f.read()

paths = re.findall(r'<path d="([^"]*)"', content)
for i, path in enumerate(paths[:3]):
    coords = re.findall(r'[ML]\s+([-\d.]+)\s+([-\d.]+)', path)
    print('Path', i, ':', len(coords), 'coords')
    print('  First few:', coords[:5])

print('Done')