import json

d = json.load(open('top_500_functions.json'))
needs_work = [f for f in d['functions'] if f['category'] in ['uncategorized', 'utility', 'undocumented']]

print(f'Total needing work: {len(needs_work)}')
print(f'Batch 1 done: 20')
print(f'Remaining: {len(needs_work) - 20}')
print()

for f in needs_work[20:]:
    print(f'Rank #{f["rank"]:3d}: 0x{f["address"]:06X} {f["name"]:<50s} {f["xrefs"]}x {f["calls"]}c {f["size"]}B')
