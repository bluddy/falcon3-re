import json

data = json.load(open('func_15a8b0.json'))

# Filter out self-references (internal jumps)
real_callees = [c for c in data['callees'] if c['addr'].lower() != data['address'].lower()]

print(f'Real external callees: {len(real_callees)}\n')

# Categorize by interest
interesting = []
for c in real_callees:
    name = c['name']
    if 'undoc' in name.lower() or 'sub_' in name:
        interesting.append(c)

print('=== All Real Callees ===')
for c in real_callees:
    print(f'{c["addr"]}: {c["name"]}')

print(f'\n=== Undocumented/Generic Names ({len(interesting)}) ===')
for c in interesting:
    print(f'{c["addr"]}: {c["name"]}')
