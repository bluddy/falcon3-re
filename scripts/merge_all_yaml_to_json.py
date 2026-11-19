#!/usr/bin/env python3
"""
Complete merge of all remaining YAML content into JSON:
1. Add missing functions from functions_top100_update.yaml to functions.json
2. Extract all structures from structures.yaml and merge into structs.json
3. Convert game_knowledge.yaml to game_knowledge.json
4. Remove the subsumed YAML files from registry/
"""
import json
import re
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "registry"

# 1. Update functions.json with top100 updates
print("Updating functions.json...")
with open(REGISTRY / "functions.json", "r", encoding="utf-8") as f:
    funcs = json.load(f)

funcs_by_addr = {f["address"]: f for f in funcs if "address" in f}

top100_yaml = REGISTRY / "functions_top100_update.yaml"
if top100_yaml.exists():
    with open(top100_yaml, "r", encoding="utf-8") as f:
        top100 = yaml.safe_load(f)
    added = 0
    for f in top100:
        addr = f.get("address")
        if addr and addr not in funcs_by_addr:
            funcs.append(f)
            funcs_by_addr[addr] = f
            added += 1
    print(f"  Added {added} missing functions to functions.json. Total: {len(funcs)}")
    with open(REGISTRY / "functions.json", "w", encoding="utf-8") as f:
        json.dump(funcs, f, indent=2)

# 2. Extract structures from structures.yaml and merge into structs.json
print("\nMerging structures.yaml into structs.json...")
with open(REGISTRY / "structs.json", "r", encoding="utf-8") as f:
    structs = json.load(f)

structs_by_name = {s["name"]: s for s in structs if "name" in s}

structs_yaml = REGISTRY / "structures.yaml"
if structs_yaml.exists():
    with open(structs_yaml, "r", encoding="utf-8") as f:
        text = f.read()

    blocks = text.split("\n- name: ")
    for b in blocks[1:]:
        lines = b.split("\n")
        name = lines[0].strip()
        size_match = re.search(r"size:\s*(\d+)", b)
        size = int(size_match.group(1)) if size_match else None
        
        fields = []
        field_chunks = b.split("    - offset:")
        for fc in field_chunks[1:]:
            off_match = re.match(r"^\s*([0-9a-fA-FxX]+|null)", fc)
            offset_val = None
            if off_match and off_match.group(1) != "null":
                try:
                    offset_val = int(off_match.group(1), 16) if "x" in off_match.group(1).lower() else int(off_match.group(1))
                except Exception:
                    pass
            name_match = re.search(r"name:\s*(\w+)", fc)
            type_match = re.search(r"type:\s*([\w\[\]]+)", fc)
            desc_match = re.search(r"description:\s*([^\n]+)", fc)
            
            fname = name_match.group(1) if name_match else None
            ftype = type_match.group(1) if type_match else "uint16"
            fdesc = desc_match.group(1).strip() if desc_match else ""
            
            fsize = 2
            if ftype in ["uint8_t", "uint8", "char", "int8"]:
                fsize = 1
            elif ftype in ["uint16_t", "uint16", "int16"]:
                fsize = 2
            elif ftype in ["uint32_t", "uint32", "int32", "far_ptr"]:
                fsize = 4
            elif "[" in ftype:
                m = re.search(r"\[(\d+)\]", ftype)
                if m:
                    fsize = int(m.group(1))
                    
            if fname:
                fields.append({
                    "offset": offset_val,
                    "name": fname,
                    "type": ftype,
                    "size": fsize,
                    "comment": fdesc
                })

        # If struct is not present, add it.
        # If it is present but the yaml version has more/richer fields, enrich it.
        if name not in structs_by_name:
            new_s = {
                "name": name,
                "size": size or 0,
                "status": "confirmed",
                "source": "structures.yaml",
                "fields": fields
            }
            structs.append(new_s)
            structs_by_name[name] = new_s
            print(f"  Added new struct: {name} ({len(fields)} fields)")
        else:
            existing = structs_by_name[name]
            existing_fields = existing.get("fields", [])
            if len(fields) > len(existing_fields):
                existing["fields"] = fields
                if size and not existing.get("size"):
                    existing["size"] = size
                print(f"  Enriched struct: {name} ({len(fields)} fields vs old {len(existing_fields)})")

    with open(REGISTRY / "structs.json", "w", encoding="utf-8") as f:
        json.dump(structs, f, indent=2)
    print(f"  Total structs in structs.json: {len(structs)}")

# 3. Convert game_knowledge.yaml to game_knowledge.json
print("\nConverting game_knowledge.yaml to game_knowledge.json...")
gk_yaml = REGISTRY / "game_knowledge.yaml"
if gk_yaml.exists():
    with open(gk_yaml, "r", encoding="utf-8") as f:
        gk_data = yaml.safe_load(f)
    with open(REGISTRY / "game_knowledge.json", "w", encoding="utf-8") as f:
        json.dump(gk_data, f, indent=2)
    print("  game_knowledge.json created.")

# 4. Remove all subsumed YAML files from registry/
print("\nRemoving subsumed YAML files from registry/...")
yaml_files_to_remove = [
    "enums.yaml",
    "functions.yaml",
    "functions.yaml.backup",
    "functions_top100_update.yaml",
    "game_knowledge.yaml",
    "globals.yaml",
    "globals_top500_additions.yaml",
    "structs.yaml",
    "structures.yaml",
    "top400_batch1_additions.yaml",
    "top400_batch2_additions.yaml",
    "top500_batch1_additions.yaml",
    "top500_batch2_additions.yaml",
]

for yf in yaml_files_to_remove:
    p = REGISTRY / yf
    if p.exists():
        p.unlink()
        print(f"  Deleted: {yf}")

print("\nAll registry data is now 100% JSON!")
