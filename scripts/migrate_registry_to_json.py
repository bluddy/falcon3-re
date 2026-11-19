#!/usr/bin/env python3
"""
Migrate all registry YAML files to JSON.
Single source of truth becomes:
- registry/functions.json
- registry/globals.json
- registry/structs.json
- registry/enums.json
"""
import json
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "registry"

def migrate_functions():
    yaml_path = REGISTRY / "functions.yaml"
    json_path = REGISTRY / "functions.json"
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    funcs = data.get("functions", [])
    print(f"Migrating {len(funcs)} functions to {json_path}...")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(funcs, f, indent=2)

def migrate_globals():
    yaml_path = REGISTRY / "globals.yaml"
    json_path = REGISTRY / "globals.json"
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    globs = data.get("globals", [])
    print(f"Migrating {len(globs)} globals to {json_path}...")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(globs, f, indent=2)

def migrate_structs_and_enums():
    # 1. Read structs.yaml
    with open(REGISTRY / "structs.yaml", "r", encoding="utf-8") as f:
        data_s = yaml.safe_load(f)
    
    structs_list = data_s.get("structs", [])
    enums_from_structs = data_s.get("enums", [])

    # 2. Read enums.yaml
    with open(REGISTRY / "enums.yaml", "r", encoding="utf-8") as f:
        enums_list = yaml.safe_load(f)

    # Merge enums by name
    enums_by_name = {}
    for e in enums_list:
        if isinstance(e, dict) and "name" in e:
            enums_by_name[e["name"]] = e
    for e in enums_from_structs:
        if isinstance(e, dict) and "name" in e:
            # structs.yaml enums are very detailed (WeaponType, etc)
            enums_by_name[e["name"]] = e

    # Also check if existing enums.json has additional entries
    existing_enums_path = REGISTRY / "enums.json"
    if existing_enums_path.exists():
        try:
            with open(existing_enums_path, "r", encoding="utf-8") as f:
                old_enums = json.load(f)
                for e in old_enums:
                    if isinstance(e, dict) and "name" in e and e["name"] not in enums_by_name:
                        enums_by_name[e["name"]] = e
        except Exception as ex:
            print(f"Notice: old enums.json: {ex}")

    merged_enums = list(enums_by_name.values())
    print(f"Total merged enums: {len(merged_enums)}")
    with open(REGISTRY / "enums.json", "w", encoding="utf-8") as f:
        json.dump(merged_enums, f, indent=2)

    # Merge structs
    structs_by_name = {}
    for s in structs_list:
        if isinstance(s, dict) and "name" in s:
            structs_by_name[s["name"]] = s

    # Check existing structs.json
    existing_structs_path = REGISTRY / "structs.json"
    if existing_structs_path.exists():
        try:
            with open(existing_structs_path, "r", encoding="utf-8") as f:
                old_structs = json.load(f)
                for s in old_structs:
                    if isinstance(s, dict) and "name" in s and s["name"] not in structs_by_name:
                        structs_by_name[s["name"]] = s
        except Exception as ex:
            print(f"Notice: old structs.json: {ex}")

    merged_structs = list(structs_by_name.values())
    print(f"Total merged structs: {len(merged_structs)}")
    with open(REGISTRY / "structs.json", "w", encoding="utf-8") as f:
        json.dump(merged_structs, f, indent=2)

if __name__ == "__main__":
    migrate_functions()
    migrate_globals()
    migrate_structs_and_enums()
    print("Migration complete!")
