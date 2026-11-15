"""
Analyze ui_menu_panel_renderer and related rendering functions.
Goal: Find how .DAT/.IDX files are loaded and displayed.
"""
import idaapi
import idc
import idautils
import json

def get_function_details(ea, max_depth=2, current_depth=0):
    """Get detailed function info including disassembly snippets."""
    func = idaapi.get_func(ea)
    if not func or current_depth > max_depth:
        return None
    
    info = {
        'address': ea,
        'name': idc.get_func_name(ea),
        'start': func.start_ea,
        'end': func.end_ea,
        'size': func.end_ea - func.start_ea,
        'callees': [],
        'interesting_ops': [],
        'strings': [],
        'data_refs': []
    }
    
    # Scan through function for interesting operations
    for ea_inst in idautils.FuncItems(func.start_ea):
        disasm = idc.GetDisasm(ea_inst)
        mnem = idc.print_insn_mnem(ea_inst)
        
        # Look for file I/O operations
        if 'int' in disasm.lower() and '21h' in disasm:
            info['interesting_ops'].append({
                'addr': ea_inst,
                'type': 'DOS_INT_21h',
                'disasm': disasm
            })
        
        # Look for call operations
        if mnem in ['call', 'callf']:
            for xref in idautils.XrefsFrom(ea_inst):
                if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
                    callee_func = idaapi.get_func(xref.to)
                    if callee_func:
                        callee_name = idc.get_func_name(callee_func.start_ea)
                        info['callees'].append({
                            'address': callee_func.start_ea,
                            'name': callee_name,
                            'call_site': ea_inst
                        })
                        
                        # Check if callee looks like file/graphics function
                        name_lower = callee_name.lower()
                        if any(kw in name_lower for kw in ['load', 'file', 'idx', 'dat', 
                                                             'vga', 'blit', 'draw', 'palette']):
                            info['interesting_ops'].append({
                                'addr': ea_inst,
                                'type': 'CALL_INTERESTING',
                                'disasm': disasm,
                                'target': callee_name
                            })
        
        # Look for string references
        for xref in idautils.XrefsFrom(ea_inst, 0):
            if xref.type == idaapi.fl_F:  # Flow reference (not code)
                str_val = idc.get_strlit_contents(xref.to)
                if str_val:
                    try:
                        decoded = str_val.decode('ascii', errors='ignore')
                        if '.DAT' in decoded or '.IDX' in decoded or '.dat' in decoded or '.idx' in decoded:
                            info['strings'].append({
                                'addr': xref.to,
                                'value': decoded,
                                'ref_from': ea_inst
                            })
                    except:
                        pass
        
        # Look for data segment accesses
        op1 = idc.print_operand(ea_inst, 0)
        op2 = idc.print_operand(ea_inst, 1)
        for op in [op1, op2]:
            if 'ds:' in op or 'es:' in op or 'cs:' in op:
                info['data_refs'].append({
                    'addr': ea_inst,
                    'operand': op,
                    'disasm': disasm
                })
    
    # Deduplicate callees
    seen_addrs = set()
    unique_callees = []
    for callee in info['callees']:
        if callee['address'] not in seen_addrs:
            unique_callees.append(callee)
            seen_addrs.add(callee['address'])
    info['callees'] = unique_callees
    
    return info

def analyze_rendering_functions():
    """Analyze the key rendering functions."""
    
    targets = {
        'ui_menu_panel_renderer': 0x133ADC,
        'menu_panel_background_draw': 0x127ED2,
        'ui_text_render_engine': 0x128598,
        'ui_menu_transition_renderer': 0x12A9F7,
    }
    
    print("Analyzing Rendering Functions")
    print("=" * 80)
    
    results = {}
    
    for name, addr in targets.items():
        print(f"\n{name} at 0x{addr:X}")
        print("-" * 80)
        
        info = get_function_details(addr)
        if not info:
            print(f"  ERROR: Function not found")
            continue
        
        print(f"  Size: {info['size']} bytes")
        print(f"  Callees: {len(info['callees'])}")
        
        # Show interesting operations
        if info['interesting_ops']:
            print(f"\n  Interesting Operations:")
            for op in info['interesting_ops'][:10]:
                print(f"    0x{op['addr']:05X}: [{op['type']}] {op['disasm']}")
                if 'target' in op:
                    print(f"              -> {op['target']}")
        
        # Show strings
        if info['strings']:
            print(f"\n  String References:")
            for s in info['strings']:
                print(f"    0x{s['addr']:05X}: {s['value']}")
        
        # Show callees with interesting names
        interesting_callees = [c for c in info['callees'] 
                              if any(kw in c['name'].lower() 
                                   for kw in ['load', 'file', 'idx', 'dat', 'read', 
                                             'vga', 'blit', 'draw', 'palette', 'decompress', 'rle'])]
        if interesting_callees:
            print(f"\n  Interesting Callees:")
            for c in interesting_callees[:15]:
                print(f"    0x{c['address']:05X}: {c['name']}")
        
        results[name] = info
    
    # Look for common callees among rendering functions
    print("\n" + "=" * 80)
    print("COMMON CALLEES AMONG RENDERERS")
    print("=" * 80)
    
    from collections import defaultdict
    all_callees = defaultdict(list)
    
    for func_name, info in results.items():
        for callee in info['callees']:
            all_callees[callee['address']].append(func_name)
    
    common = [(addr, funcs) for addr, funcs in all_callees.items() if len(funcs) > 1]
    common.sort(key=lambda x: len(x[1]), reverse=True)
    
    print(f"\nFound {len(common)} functions called by multiple renderers:\n")
    for addr, funcs in common[:20]:
        callee_name = idc.get_func_name(addr)
        print(f"  0x{addr:05X} {callee_name:50} <- {', '.join(funcs)}")
    
    # Save results
    with open('rendering_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 80)
    print("Results saved to rendering_analysis.json")
    
    idc.qexit(0)

if __name__ == '__main__':
    analyze_rendering_functions()
