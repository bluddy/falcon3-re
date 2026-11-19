import json

with open('analysis/viewer/assets_database.json', 'r') as f:
    db = json.load(f)

print("Top keys:", list(db.keys())[:10])
for k, v in db.items():
    if isinstance(v, list):
        print(f"Key '{k}' has list of {len(v)} items")
