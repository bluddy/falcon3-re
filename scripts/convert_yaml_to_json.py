"""
Convert YAML registry files to JSON for use in IDA (which doesn't have PyYAML).
"""
import yaml
import json
from pathlib import Path

base_path = Path(r"C:\Users\ybarnoy\projects\falcon3")

# Convert enums.yaml
try:
    print("Loading enums.yaml...")
    with open(base_path / "registry" / "enums.yaml", 'r') as f:
        enums = yaml.safe_load(f)
    
    print(f"Loaded {len(enums)} enums")
    
    with open(base_path / "registry" / "enums.json", 'w') as f:
        json.dump(enums, f, indent=2)
    
    print("Created enums.json")
except Exception as e:
    print(f"Error with enums.yaml: {e}")

# Convert structures.yaml
try:
    print("\nLoading structures.yaml...")
    with open(base_path / "registry" / "structures.yaml", 'r') as f:
        structures = yaml.safe_load(f)
    
    print(f"Loaded {len(structures)} structures")
    
    with open(base_path / "registry" / "structures.json", 'w') as f:
        json.dump(structures, f, indent=2)
    
    print("Created structures.json")
except Exception as e:
    print(f"Error with structures.yaml: {e}")

print("\nDone!")
