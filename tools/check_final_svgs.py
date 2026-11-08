import sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

for name in ['BOS', 'HOK', 'IRQ', 'ISR', 'KOR', 'NEL', 'PAN']:
    with open('analysis/isldat_svgs_final/ISLDAT_{0}_coastline.svg'.format(name), 'r', encoding='utf-8') as f:
        content = f.read()
    paths = re.findall(r'<path d="([^"]*)"', content)
    print('{0}: {1} paths'.format(name, len(paths)))