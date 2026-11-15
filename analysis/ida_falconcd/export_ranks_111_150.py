import json

with open('top_200_functions.json') as f:
    data = json.load(f)

print("rank,address,name,size,calls")
for i, f in enumerate(data[150:200], 151):
    print(f"{i},{f['address']},{f['name']},{f['size']},{f['calls']}")
