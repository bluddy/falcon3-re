import json

with open('registry/structs.json', 'r') as f:
    structs = json.load(f)

print(f"Total structs in registry: {len(structs)}")
for s in structs[:15]:
    print(f"  Struct: {s.get('name')} ({s.get('size')} bytes)")

with open('registry/functions.json', 'r') as f:
    funcs = json.load(f)

print(f"\nTotal functions in registry: {len(funcs)}")
obj_funcs = [fn for fn in funcs if any(k in fn.get('name', '').lower() for k in ['obj', 'poly', '3d', 'draw', 'mesh'])]
print(f"Matching 3D/object/poly functions: {len(obj_funcs)}")
for fn in obj_funcs[:15]:
    print(f"  0x{fn.get('address'):X}: {fn.get('name')}")
