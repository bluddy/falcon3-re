"""
Analyze the callees of squadron_mission_file_loader (0x17B437)
"""
import json

data = json.load(open('all_functions_categorized.json'))
callees = ['0x13aa6a', '0x138e6a', '0x138f9c', '0x225b6', '0x13b243', '0x129468', '0x1293f0', '0x135c57', '0x13aac0']

print("Callees of squadron_mission_file_loader (0x17B437):\n")
print(f"{'Address':<12} {'Name':<35} {'Size':<8} {'Callers':<10}")
print("=" * 75)

funcs = [f for f in data['all_functions'] if f['address'].lower() in callees]
# Sort by address
funcs.sort(key=lambda x: int(x['address'], 16))

for f in funcs:
    addr = f['address']
    name = f['name']
    size = f['size']
    callers = f.get('calls', '?')
    print(f"{addr:<12} {name:<35} {size:<8} {callers:<10}")

print("\n\nHigh caller count functions (potentially important):")
high_callers = [f for f in funcs if f.get('calls', 0) > 20]
for f in sorted(high_callers, key=lambda x: x.get('calls', 0), reverse=True):
    print(f"  {f['address']} {f['name']}: {f['calls']} callers")
