import json

files = [
    'path_b_1ff5d_full.json',
    'path_b_21240_full.json',
    'path_b_20bce_full.json'
]

for fname in files:
    with open(fname) as f:
        data = json.load(f)
    
    print(f"\n{'='*60}")
    print(f"Function: {data['current_name']} @ {data['address']}")
    print(f"Size: {data['size']} bytes")
    print(f"Instructions: {data['instruction_count']}")
    print(f"Callers: {data['caller_count']}")
    print(f"Callees: {data['callee_count']}")
    
    if data['callees']:
        print("\nCallees:")
        for c in data['callees'][:10]:
            print(f"  - {c['name']} @ {c['addr']}")
    
    print("\nFirst 15 instructions:")
    for i, insn in enumerate(data['instructions'][:15], 1):
        print(f"  {i:2}. {insn['addr']}: {insn['disasm']}")
