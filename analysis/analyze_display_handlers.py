import json
from collections import Counter

data = json.load(open('r57_loadout_menu_complete.json'))

# Look at the display handlers
handlers = ['menu_r57_flight_display_handler', 'menu_r57_loadout_flight_display', 'r57_loadout_display_handler']

for name in handlers:
    if name in data:
        func = data[name]
        print(f'\n{name}:')
        print(f'  Address: {func["address"]}')
        print(f'  Size: {func["size"]} bytes')
        print(f'  Calls: {len(func["calls"])} functions')
        print(f'\n  Top function calls:')
        
        # Count call frequencies
        call_counts = Counter(c['name'] for c in func['calls'])
        for fname, count in call_counts.most_common(20):
            print(f'    {count:3d}x {fname}')
        
        # Look for graphics-related calls
        print(f'\n  Graphics-related calls:')
        graphics_keywords = ['draw', 'render', 'blit', 'sprite', 'image', 'graphic', 'pic', 'bitmap', 'vga', 'pixel']
        for call in func['calls']:
            call_name = call['name'].lower()
            if any(kw in call_name for kw in graphics_keywords):
                print(f'    {call["name"]} at {call["address"]}')
