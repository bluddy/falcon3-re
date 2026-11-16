import json

d = json.load(open('top_500_functions.json'))
print('='*70)
print('TOP 500 EXTRACTION - SUMMARY')
print('='*70)
print(f'Total: {d["total"]}')
print(f'Needs work: {d["needs_work"]}')
print()
print('Categories:')
for cat, count in d['summary'].items():
    print(f'  {cat:<20s}: {count:>3d}')

print()
print('='*70)
print(f'FUNCTIONS NEEDING WORK ({len([f for f in d["functions"] if f["category"] in ["uncategorized", "utility", "undocumented"]])} total)')
print('='*70)

needs_work = [f for f in d['functions'] if f['category'] in ['uncategorized', 'utility', 'undocumented']]
for i, f in enumerate(needs_work):
    print(f'Rank #{f["rank"]:3d}: 0x{f["address"]:06X} - {f["name"]:<45s} {f["xrefs"]:2d} xrefs, {f["calls"]:2d} calls, {f["size"]:4d}B')
    if i >= 29:
        print(f'\n... and {len(needs_work) - 30} more')
        break
