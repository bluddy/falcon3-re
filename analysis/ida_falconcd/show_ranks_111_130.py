import json

with open('top_200_functions.json') as f:
    data = json.load(f)

print("\nRanks 111-130:")
for i, f in enumerate(data[110:130], 111):
    print(f"{i:3}. {f['name']:35} @ {f['address']:8} : {f['calls']:2} calls, {f['size']:4}B")
