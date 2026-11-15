"""
Summarize the loadout menu deep-dive analysis
"""
import json
from collections import Counter

# Load the analysis
with open('ida_scripts/loadout_menu_deepdive.json', 'r') as f:
    data = json.load(f)

print("="*80)
print("UI_LOADOUT_MENU_ENTER DEEP-DIVE SUMMARY")
print("="*80)

# Function overview
func = data['function']
print(f"\nFunction: {func['name']}")
print(f"Address: {func['hex_addr']}")
print(f"Size: {func['size']} bytes")
print(f"Instructions: {func['instruction_count']}")
print(f"Basic blocks: {func['basic_block_count']}")
print(f"Unique data references: {func['unique_data_refs']}")
print(f"Unique function calls: {func['unique_calls']}")

# Instruction statistics
print(f"\n{'='*80}")
print("INSTRUCTION STATISTICS")
print("="*80)

instr_counts = data['instruction_counts']
print("\nTop 20 most used instructions:")
for i, (mnem, count) in enumerate(sorted(instr_counts.items(), key=lambda x: x[1], reverse=True)[:20]):
    print(f"  {i+1:2d}. {mnem:10s}: {count:4d}")

# Call statistics
print(f"\n{'='*80}")
print("FUNCTION CALLS")
print("="*80)

call_stats = data['call_statistics']
total_calls = sum(call_stats.values())
print(f"\nTotal call sites: {total_calls}")
print(f"Unique functions called: {len(call_stats)}")

print(f"\nTop 20 most frequently called functions:")
for i, (name, count) in enumerate(sorted(call_stats.items(), key=lambda x: x[1], reverse=True)[:20]):
    print(f"  {i+1:2d}. {name:50s}: {count:3d} calls")

# Data references
print(f"\n{'='*80}")
print("DATA REFERENCES")
print("="*80)

data_refs = data['data_references']
print(f"\nUnique data addresses: {len(data_refs)}")

# Group by reference count
ref_counts = Counter(d['ref_count'] for d in data_refs)
print(f"\nReference frequency distribution:")
for count, num_addrs in sorted(ref_counts.items(), reverse=True)[:10]:
    print(f"  {num_addrs:3d} addresses referenced {count} times")

print(f"\nTop 30 most referenced data:")
for i, d in enumerate(sorted(data_refs, key=lambda x: x['ref_count'], reverse=True)[:30]):
    dtype = d['type'] if d['type'] else 'unknown'
    print(f"  {i+1:2d}. {d['name']:45s}: {d['ref_count']:3d} refs ({dtype})")

# Basic blocks
print(f"\n{'='*80}")
print("CONTROL FLOW")
print("="*80)

blocks = data['basic_blocks']
print(f"\nBasic blocks: {len(blocks)}")

block_sizes = [b['end'] - b['start'] for b in blocks]
print(f"Average block size: {sum(block_sizes) / len(block_sizes):.1f} bytes")
print(f"Smallest block: {min(block_sizes)} bytes")
print(f"Largest block: {max(block_sizes)} bytes")

# Analyze instruction patterns
print(f"\n{'='*80}")
print("INSTRUCTION PATTERNS")
print("="*80)

instructions = data['instructions']

# Count push/pop pairs
pushes = sum(1 for i in instructions if i['mnem'] == 'push')
pops = sum(1 for i in instructions if i['mnem'] == 'pop')
print(f"\nStack operations:")
print(f"  PUSH instructions: {pushes}")
print(f"  POP instructions: {pops}")
print(f"  Balance: {pushes - pops} (should be ~0 for balanced function)")

# Count jumps
jumps = sum(1 for i in instructions if i['mnem'].startswith('j'))
print(f"\nConditional logic:")
print(f"  Jump instructions: {jumps}")
print(f"  Basic blocks: {len(blocks)}")
print(f"  Average jumps per block: {jumps / len(blocks):.2f}")

# Count calls
calls = sum(1 for i in instructions if i['mnem'] in ['call', 'callf'])
print(f"\nFunction calls:")
print(f"  CALL instructions: {calls}")
print(f"  Unique callees: {len(call_stats)}")
print(f"  Average calls per unique function: {calls / len(call_stats):.2f}")

# Save summary
summary = {
    'overview': func,
    'top_instructions': dict(sorted(instr_counts.items(), key=lambda x: x[1], reverse=True)[:20]),
    'top_calls': dict(sorted(call_stats.items(), key=lambda x: x[1], reverse=True)[:20]),
    'top_data_refs': sorted(data_refs, key=lambda x: x['ref_count'], reverse=True)[:30],
    'statistics': {
        'pushes': pushes,
        'pops': pops,
        'stack_balance': pushes - pops,
        'jumps': jumps,
        'calls': calls,
        'basic_blocks': len(blocks),
        'avg_block_size': sum(block_sizes) / len(block_sizes),
        'total_instructions': len(instructions)
    }
}

with open('loadout_menu_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\n{'='*80}")
print("Summary saved to: analysis/loadout_menu_summary.json")
print("="*80)
