"""Extract calls and loops from view_projection analysis."""
import json

with open('view_projection_detailed.json') as f:
    data = json.load(f)

print("=" * 80)
print(f"VIEW_PROJECTION ANALYSIS SUMMARY")
print("=" * 80)
print(f"Address: {data['address']}")
print(f"Size: {data['size']} bytes")
print(f"Instructions: {data['num_instructions']}")
print(f"Calls: {data['num_calls']}")
print(f"Loops: {data['num_loops']}")
print(f"Data refs: {data['num_data_refs']}")
print(f"Branches: {data['num_branches']}")

print("\n" + "=" * 80)
print("FUNCTION CALLS")
print("=" * 80)
for call in data['calls']:
    print(f"  {call['from']} -> {call['to']} ({call['target']})")

print("\n" + "=" * 80)
print("LOOPS (first 20)")
print("=" * 80)
for i, loop in enumerate(data['loops'][:20]):
    print(f"  Loop {i+1}: {loop['type']} from {loop['branch_from']} to {loop['branch_to']}")

print("\n" + "=" * 80)
print("DATA REFERENCES (all)")
print("=" * 80)
for ref in data['data_refs']:
    print(f"  {ref['from']} -> {ref['name']} ({ref['to']})")
    print(f"    {ref['instruction']}")
