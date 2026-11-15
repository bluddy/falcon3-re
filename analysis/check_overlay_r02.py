"""
The graphics_record_processor jumps to overlay r02_farptr_pair_call_entry
Let's see if we have any info about overlay r02
"""
import json
from pathlib import Path

# Check overlay loads
overlay_file = Path('archive/traces/overlay_load_map.json')

if overlay_file.exists():
    with open(overlay_file) as f:
        overlays = json.load(f)
    
    print("Checking for r02 overlay...")
    for key, info in overlays.items():
        if 'r02' in key.lower() or '0x100D01' in str(info):
            print(f"\nFound: {key}")
            print(json.dumps(info, indent=2))
else:
    print("No overlay map found")

# Check if there are any DOSBox/game files with overlay data
game_dir = Path('../game')
for f in game_dir.glob('*.OVL'):
    print(f"\nFound overlay file: {f.name} ({f.stat().st_size} bytes)")
