#!/usr/bin/env python3
"""Find top overlay targets for analysis."""
import json
from pathlib import Path

# Load function_bytes for address mapping
fb = json.load(open("../ida_falconcd/function_bytes.json"))

# Load callgraph for dynamic call counts
cg = json.load(open("../traces/callgraph_partial.json"))
dyn_target_calls = cg.get('dyn_target_calls', {})
named_set = set(cg.get('named', []))

# Filter to overlay functions (ea >= 0x1FBC0)
overlay_calls = []
for func_name, call_count in dyn_target_calls.items():
    if func_name in fb:
        ea = fb[func_name]['ea']
        if ea >= 0x1FBC0:  # Overlay range
            is_named = func_name in named_set
            overlay_calls.append((func_name, call_count, ea, is_named))

# Sort by call count
overlay_calls.sort(key=lambda x: x[1], reverse=True)

print(f"Total overlay functions with dynamic calls: {len(overlay_calls)}\n")

print("=" * 80)
print("TOP 30 OVERLAY FUNCTIONS BY CALL FREQUENCY")
print("=" * 80)
print(f"{'Rank':<5} {'Function':<15} {'Calls':>10} {'Address':<10} {'Named?':<7}")
print("-" * 80)

for i, (func, calls, ea, is_named) in enumerate(overlay_calls[:30], 1):
    status = "YES" if is_named else "NO"
    print(f"{i:<5} {func:<15} {calls:>10,} 0x{ea:05X}    {status:<7}")

# Show unnamed high-value targets
print("\n" + "=" * 80)
print("TOP 20 UNNAMED OVERLAY FUNCTIONS")
print("=" * 80)

unnamed = [x for x in overlay_calls if not x[3]]
print(f"{'Rank':<5} {'Function':<15} {'Calls':>10} {'Address':<10} {'Size':>6}")
print("-" * 80)

for i, (func, calls, ea, _) in enumerate(unnamed[:20], 1):
    size = fb[func].get('size', 0)
    print(f"{i:<5} {func:<15} {calls:>10,} 0x{ea:05X}    {size:>6}B")

# Export top 20 unnamed for analysis
output = {
    'top_20_unnamed': [
        {
            'rank': i,
            'function': func,
            'calls': calls,
            'address': f"0x{ea:05X}",
            'size': fb[func].get('size', 0),
            'bytes_hex': fb[func].get('bytes', '')
        }
        for i, (func, calls, ea, _) in enumerate(unnamed[:20], 1)
    ]
}

output_path = Path("top_overlay_targets.json")
json.dump(output, open(output_path, 'w'), indent=2)
print(f"\nExported top 20 unnamed to {output_path}")

# Show address range distribution of top overlay targets
print("\n" + "=" * 80)
print("ADDRESS RANGE DISTRIBUTION (Top 50 Overlay Functions)")
print("=" * 80)

from collections import Counter
ranges = Counter()
for func, calls, ea, _ in overlay_calls[:50]:
    # Group by overlay record (rough 0x10000 blocks)
    block = (ea // 0x10000) * 0x10000
    ranges[block] += 1

for block in sorted(ranges.keys()):
    print(f"  0x{block:05X}+: {ranges[block]} functions")
