"""
Expand from the rendering functions we found to discover more UI/graphics code
"""
import idaapi
import idautils
import idc
import json

def expand_call_graph(seed_addrs, max_depth=3):
    """Expand call graph from seed addresses"""
    visited = set()
    results = {}
    queue = [(addr, 0) for addr in seed_addrs]
    
    while queue:
        addr, depth = queue.pop(0)
        
        if addr in visited or depth > max_depth:
            continue
        
        visited.add(addr)
        func_name = idc.get_func_name(addr)
        
        if not func_name:
            continue
        
        # Get function info
        func = idaapi.get_func(addr)
        if not func:
            continue
        
        callees = []
        callers = []
        
        # Find callees
        for xref in idautils.XrefsFrom(func.start_ea, 0):
            if xref.type in [idc.fl_CN, idc.fl_CF]:  # Calls
                target_name = idc.get_func_name(xref.to)
                if target_name:
                    callees.append({
                        'addr': xref.to,
                        'name': target_name
                    })
                    if depth < max_depth:
                        queue.append((xref.to, depth + 1))
        
        # Find callers
        for xref in idautils.XrefsTo(func.start_ea, 0):
            if xref.type in [idc.fl_CN, idc.fl_CF]:  # Calls
                caller_name = idc.get_func_name(xref.frm)
                if caller_name:
                    callers.append({
                        'addr': xref.frm,
                        'name': caller_name
                    })
        
        results[func_name] = {
            'address': addr,
            'hex_addr': f'0x{addr:X}',
            'depth': depth,
            'callees': callees,
            'callers': callers,
            'size': func.end_ea - func.start_ea
        }
    
    return results

def main():
    print("="*60)
    print("Expanding from rendering and graphics functions...")
    print("="*60)
    
    # Start from the rendering and graphics functions we know
    seed_functions = {
        'ui_menu_panel_renderer': 0x133ADC,
        'menu_panel_background_draw': 0x127ED2,
        'ui_text_render_engine': 0x128598,
        'ui_menu_transition_renderer': 0x12A9F7,
        'madfont_idx_dat_loader': 0x139909,
        'rle_vga_decompressor': 0x88460,
        # Menu system functions
        'sub_683C5': 0x683C5,  # Main menu controller
        'sub_66E62': 0x66E62,  # Menu panel init
        'sub_6A5BD': 0x6A5BD,  # Menu page setup
        'sub_6798C': 0x6798C,  # Slot record fill
        'sub_67BAF': 0x67BAF,  # Menu transition
    }
    
    print(f"\nStarting from {len(seed_functions)} seed functions")
    print("Expanding call graph (depth=3)...")
    
    graph = expand_call_graph(list(seed_functions.values()), max_depth=3)
    
    print(f"\nDiscovered {len(graph)} functions in call graph")
    
    # Categorize functions by their likely purpose based on names
    categories = {
        'ui': [],
        'menu': [],
        'graphics': [],
        'file_io': [],
        'render': [],
        'other': []
    }
    
    for func_name, info in graph.items():
        if any(k in func_name.lower() for k in ['ui_', 'menu', 'panel']):
            categories['menu'].append((func_name, info))
        elif any(k in func_name.lower() for k in ['render', 'draw', 'display', 'paint']):
            categories['render'].append((func_name, info))
        elif any(k in func_name.lower() for k in ['graph', 'vga', 'pixel', 'sprite']):
            categories['graphics'].append((func_name, info))
        elif any(k in func_name.lower() for k in ['file', 'load', 'read', 'idx', 'dat']):
            categories['file_io'].append((func_name, info))
        else:
            categories['other'].append((func_name, info))
    
    # Print categorized summary
    print("\n" + "="*60)
    print("CATEGORIZED FUNCTIONS")
    print("="*60)
    
    for cat_name, funcs in categories.items():
        if funcs:
            print(f"\n{cat_name.upper()} ({len(funcs)} functions):")
            for func_name, info in sorted(funcs, key=lambda x: x[1]['depth'])[:10]:
                print(f"  [d{info['depth']}] 0x{info['address']:06X}: {func_name} "
                      f"({len(info['callees'])} callees, {len(info['callers'])} callers)")
    
    # Save results
    output_path = r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\rendering_call_graph.json'
    with open(output_path, 'w') as f:
        json.dump(graph, f, indent=2)
    
    print(f"\nFull call graph saved to: {output_path}")

if __name__ == '__main__':
    main()
    idc.qexit(0)
