"""
Add 5 new 8-byte pointer accessor functions discovered from menu controller analysis.
APPENDS to registry/functions.yaml
"""

def add_menu_accessors():
    """Add 5 new 8B accessor functions to registry by appending."""
    
    registry_file = r'c:\Users\ybarnoy\projects\falcon3\registry\functions.yaml'
    
    # Check what's already there
    with open(registry_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # New 8B accessor functions from menu controller call-graph analysis
    # Format: (address, name, size, comparisons, callers, description)
    new_functions = [
        (0x2c3b5, 'menu_selection_ptr_get', 8, 0, 8,
         'Get pointer to menu selection state structure. Simple 8B accessor'),
        
        (0x2c289, 'menu_transition_ptr_get', 8, 0, 3,
         'Get pointer to menu transition state. Simple 8B accessor'),
        
        (0x2c3bf, 'menu_cursor_ptr_get', 8, 0, 3,
         'Get pointer to menu cursor state. Simple 8B accessor'),
        
        (0x2c3c9, 'menu_input_ptr_get', 8, 0, 2,
         'Get pointer to menu input handler state. Simple 8B accessor'),
        
        (0x2c3d3, 'menu_frame_ptr_get', 8, 0, 1,
         'Get pointer to menu frame data. Simple 8B accessor'),
    ]
    
    # Check which are new
    to_add = []
    for addr_int, name, size, comps, callers, desc in new_functions:
        addr = f'0x{addr_int:06x}'
        
        if addr in content:
            print(f"SKIP: {addr} {name:40s} (already in registry)")
            continue
        
        to_add.append((addr, name, size, comps, callers, desc))
        print(f"ADD:  {addr} {name:40s} ({size:4d}B, {comps:2d} cmps, {callers:3d} callers)")
    
    if not to_add:
        print("\n[!] No new functions to add")
        return
    
    # Append to file
    with open(registry_file, 'a', encoding='utf-8') as f:
        for addr, name, size, comps, callers, desc in to_add:
            f.write(f'\n  - address: {addr}\n')
            f.write(f'    name: {name}\n')
            f.write(f'    system: menu\n')
            f.write(f'    size: {size}\n')
            # Escape single quotes
            doc = desc.replace("'", "''")
            f.write(f"    doc: '{doc}'\n")
            source = f'IDA call-graph from menu controller (size={size}B, comparisons={comps}, callers={callers})'
            f.write(f"    source: '{source}'\n")
    
    print(f'\n[+] Added {len(to_add)} new menu accessor functions')
    print(f'[+] Appended to: {registry_file}')

if __name__ == '__main__':
    add_menu_accessors()
