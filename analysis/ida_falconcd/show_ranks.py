import json

with open('top_200_functions.json') as f:
    data = json.load(f)

print("\nRanks 111-120:")
for i, f in enumerate(data[110:120], 111):
    print(f"  {i}. {f['name']} @ {f['address']}: {f['calls']} calls, {f['size']}B")
