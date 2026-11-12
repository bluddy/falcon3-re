import json

with open('segments_list.json') as f:
    data = json.load(f)

segs = data['segments']
print(f"Total: {len(segs)} segments\n")

# Look for data-like segments (at end, large)
print("Segments over 10KB:")
for s in segs:
    if s['size'] > 10000:
        print(f"  {s['name']}: {s['start']} - {s['end']}, {s['size']:,} bytes, selector={s['selector']}")

print("\nLast 5 segments:")
for s in segs[-5:]:
    print(f"  {s['name']}: {s['start']} - {s['end']}, {s['size']:,} bytes, selector={s['selector']}")
