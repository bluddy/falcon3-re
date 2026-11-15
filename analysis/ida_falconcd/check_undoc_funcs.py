import json

funcs = json.load(open('top_200_functions.json'))
targets = ['undoc_130C80', 'undoc_130CE7', 'undoc_130E48', 'undoc_131001', 'undoc_131235', 'undoc_1312DF']

found = [f for f in funcs if f.get('name') in targets]
print(f'Found {len(found)} of {len(targets)} targets in Top 200:')
for f in found:
    print(f"  {f['name']:20s} 0x{f['address']:6s} {f['size']:5d}B calls={f.get('calls',0):3d}")

print(f'\nNot in Top 200:')
found_names = {f['name'] for f in found}
for t in targets:
    if t not in found_names:
        print(f"  {t}")
