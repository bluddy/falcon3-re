"""
Expand analysis from known menu functions.
Starting points:
- sub_683C5 (0x683C5) - Main menu controller
- sub_66E62 (0x66E62) - Menu panel init
- sub_6A5BD (0x6A5BD) - Menu page setup
- sub_6798C (0x6798C) - Slot record fill
"""
import idaapi
import idc
import idautils
import json

def get_function_info(ea):
    """Get detailed info about a function."""
    func = idaapi.get_func(ea)
    if not func:
        return None
    
    info = {
        'address': ea,
        'name': idc.get_func_name(ea),
        'start': func.start_ea,
        'end': func.end_ea,
        'size': func.end_ea - func.start_ea,
        'callers': [],
        'callees': []
    }
    
    # Get callers
    for xref in idautils.XrefsTo(ea):
        if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:  # Call types
            caller_func = idaapi.get_func(xref.frm)
            if caller_func:
                info['callers'].append({
                    'address': caller_func.start_ea,
                    'name': idc.get_func_name(caller_func.start_ea),
                    'call_site': xref.frm
                })
    
    # Get callees
    for ea_inst in idautils.FuncItems(func.start_ea):
        for xref in idautils.XrefsFrom(ea_inst):
            if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:  # Call types
                callee_func = idaapi.get_func(xref.to)
                if callee_func:
                    info['callees'].append({
                        'address': callee_func.start_ea,
                        'name': idc.get_func_name(callee_func.start_ea),
                        'call_site': ea_inst
                    })
    
    # Deduplicate
    info['callers'] = list({c['address']: c for c in info['callers']}.values())
    info['callees'] = list({c['address']: c for c in info['callees']}.values())
    
    return info

def expand_from_seeds():
    """Expand analysis from known menu functions."""
    
    # Starting points
    seeds = {
        'menu_controller': 0x683C5,
        'menu_panel_init': 0x66E62,
        'menu_page_setup': 0x6A5BD,
        'slot_record_fill': 0x6798C,
        'menu_transition': 0x67BAF,
    }
    
    print("Expanding menu system analysis from known functions")
    print("=" * 80)
    
    results = {}
    
    for name, addr in seeds.items():
        print(f"\nAnalyzing {name} at 0x{addr:X}...")
        info = get_function_info(addr)
        if info:
            print(f"  Name: {info['name']}")
            print(f"  Size: {info['size']} bytes")
            print(f"  Callers: {len(info['callers'])}")
            print(f"  Callees: {len(info['callees'])}")
            results[name] = info
        else:
            print(f"  ERROR: Function not found")
    
    # Find common callees (likely important infrastructure)
    print("\n" + "=" * 80)
    print("COMMON INFRASTRUCTURE (called by multiple menu functions)")
    print("=" * 80)
    
    all_callees = {}
    for name, info in results.items():
        if 'callees' in info:
            for callee in info['callees']:
                callee_addr = callee['address']
                if callee_addr not in all_callees:
                    all_callees[callee_addr] = {
                        'name': callee['name'],
                        'called_by': []
                    }
                all_callees[callee_addr]['called_by'].append(name)
    
    # Show functions called by multiple seeds
    common = [(addr, data) for addr, data in all_callees.items() 
              if len(data['called_by']) > 1]
    common.sort(key=lambda x: len(x[1]['called_by']), reverse=True)
    
    print(f"\nFound {len(common)} functions called by multiple seeds:")
    for addr, data in common[:20]:
        callers = ', '.join(data['called_by'])
        print(f"  0x{addr:05X} {data['name']:40} <- {callers}")
    
    # Look for graphics/file I/O related functions in callees
    print("\n" + "=" * 80)
    print("POTENTIAL GRAPHICS/FILE FUNCTIONS")
    print("=" * 80)
    
    keywords = ['vga', 'graph', 'file', 'load', 'idx', 'dat', 'palette', 
                'blit', 'draw', 'render', 'display']
    
    for name, info in results.items():
        print(f"\n{name}:")
        if 'callees' in info:
            for callee in info['callees']:
                callee_name = callee['name'].lower()
                if any(kw in callee_name for kw in keywords):
                    print(f"  0x{callee['address']:05X} {callee['name']}")
    
    # Save results
    with open('menu_system_expansion.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 80)
    print("Results saved to menu_system_expansion.json")
    
    idc.qexit(0)

if __name__ == '__main__':
    expand_from_seeds()
