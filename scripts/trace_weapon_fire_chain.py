import idc
import idautils
import idaapi
import json

def find_callers_recursive(target_ea, depth=0, max_depth=5, visited=None):
    """Recursively find callers up the call chain"""
    if visited is None:
        visited = set()
    
    if depth >= max_depth or target_ea in visited:
        return []
    
    visited.add(target_ea)
    
    callers = []
    for xref in idautils.XrefsTo(target_ea, idaapi.XREF_ALL):
        func = idaapi.get_func(xref.frm)
        if func:
            func_name = idc.get_func_name(func.start_ea)
            if func_name:
                caller_info = {
                    'function': func_name,
                    'address': hex(func.start_ea),
                    'call_site': hex(xref.frm),
                    'depth': depth,
                    'callers': []
                }
                
                # Recursively find callers of this function
                if depth < max_depth - 1:
                    caller_info['callers'] = find_callers_recursive(
                        func.start_ea, depth + 1, max_depth, visited
                    )
                
                callers.append(caller_info)
    
    return callers

def search_for_keyboard_handlers(call_chain):
    """Search for keyboard-related functions in the call chain"""
    keyboard_functions = []
    
    def search_recursive(node):
        func_name = node.get('function', '').lower()
        if any(kw in func_name for kw in ['key', 'input', 'scan', 'kbd', 'button']):
            keyboard_functions.append({
                'function': node['function'],
                'address': node['address'],
                'depth': node['depth']
            })
        
        for caller in node.get('callers', []):
            search_recursive(caller)
    
    for node in call_chain:
        search_recursive(node)
    
    return keyboard_functions

print("Tracing weapon fire call chain...")

# Start from weapon_spawn_gate_validate
weapon_spawn = 0x3DC55

# Build call chain
call_chain = find_callers_recursive(weapon_spawn, depth=0, max_depth=6)

# Search for keyboard handlers
keyboard_funcs = search_for_keyboard_handlers(call_chain)

results = {
    'root_function': {
        'name': 'weapon_spawn_gate_validate',
        'address': hex(weapon_spawn)
    },
    'call_chain': call_chain,
    'keyboard_handlers': keyboard_funcs
}

with open('weapon_fire_call_chain.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nBuilt call chain with {len(call_chain)} immediate callers")
print(f"Found {len(keyboard_funcs)} potential keyboard handlers")

for kh in keyboard_funcs:
    print(f"  {kh['function']} at {kh['address']} (depth {kh['depth']})")

idc.qexit(0)
