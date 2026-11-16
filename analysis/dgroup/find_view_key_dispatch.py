"""
Find dispatch logic for number keys (view switching).
Scan codes: 0x02-0x0B (1-9, 0)

Strategy:
1. Find all places that read input_flag_pending_2
2. Look for comparisons with 0x02-0x0B
3. Find switch tables or conditional chains
"""

import json

# Load the input_flag_refs.json
with open(r"c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\input_flag_refs.json", 'r') as f:
    data = json.load(f)

# Number key scan codes
VIEW_KEYS = list(range(0x02, 0x0C))  # 0x02-0x0B
VIEW_KEYS_HEX = [hex(x) for x in VIEW_KEYS]

print("=" * 80)
print("SEARCHING FOR VIEW KEY DISPATCH")
print("=" * 80)
print(f"View key scan codes: {VIEW_KEYS_HEX}")
print()

# Find all MOV reads
reads = [ref for ref in data['references'] if 'mov' in ref['insn'].lower() and 'es:input_flag_pending_2' in ref['insn'] and ref['insn'].startswith('mov     ax,')]

print(f"Found {len(reads)} read operations")
print()

# Group by function
by_func = {}
for ref in reads:
    func = ref['func']
    if func not in by_func:
        by_func[func] = []
    by_func[func].append(ref)

print("Reads by function:")
for func, refs in sorted(by_func.items()):
    print(f"  {func}: {len(refs)} read(s) in {refs[0]['segment']}")

# Now we need to look at instructions AFTER each read
# This requires IDA API, but let's at least identify candidates
print()
print("=" * 80)
print("CANDIDATE FUNCTIONS FOR MANUAL INSPECTION:")
print("=" * 80)
print()
print("These functions read input_flag_pending_2 and may dispatch view keys:")
for func, refs in sorted(by_func.items()):
    print(f"\n{func} ({refs[0]['segment']}):")
    for ref in refs:
        print(f"  Read at {ref['addr']}")
    
print()
print("=" * 80)
print("NEXT STEP:")
print("=" * 80)
print("We need to examine the code AFTER each read instruction to find:")
print("1. Comparisons with 0x02-0x0B")
print("2. Switch/jump tables indexed by scan code")
print("3. Conditional chains for different scan codes")
print()
print("Priority candidates (game mode coordinators):")
priority = [
    "r29_tactical_screen_coordinator",
    "overlay_r45_logic",
    "overlay_r48_processor",
    "overlay_r49_handler",
    "game_mode_r53_main_coordinator"
]
for func in priority:
    if func in by_func:
        print(f"  - {func}: {by_func[func][0]['addr']} in {by_func[func][0]['segment']}")
