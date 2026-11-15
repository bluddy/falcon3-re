"""
Find all functions that reference menu/UI data structures
Instead of following calls, find functions by what data they access
"""
import idaapi
import idautils
import idc
import json

def find_functions_referencing_data(data_addrs):
    """Find all functions that reference specific data addresses"""
    func_refs = {}
    
    for data_addr in data_addrs:
        for xref in idautils.XrefsTo(data_addr, 0):
            func = idaapi.get_func(xref.frm)
            if func:
                func_name = idc.get_func_name(func.start_ea)
                if func_name not in func_refs:
                    func_refs[func_name] = {
                        'address': func.start_ea,
                        'hex_addr': f'0x{func.start_ea:X}',
                        'size': func.end_ea - func.start_ea,
                        'data_refs': []
                    }
                
                data_name = idc.get_name(data_addr)
                func_refs[func_name]['data_refs'].append({
                    'addr': data_addr,
                    'name': data_name if data_name else f'data_{data_addr:X}'
                })
    
    return func_refs

def find_string_patterns():
    """Find menu-related strings and functions that use them"""
    menu_strings = []
    
    print("Searching for menu-related strings...")
    
    keywords = [
        'MENU', 'PANEL', 'BUTTON', 'SCREEN', 'SETUP', 'CONFIG',
        'PILOT', 'MISSION', 'LOADOUT', 'WEAPON', 'OPTION',
        'VIDEO', 'SOUND', 'CONTROL', 'DIFFICULTY'
    ]
    
    for s in idautils.Strings():
        str_val = str(s).upper()
        if any(kw in str_val for kw in keywords):
            menu_strings.append({
                'addr': s.ea,
                'hex_addr': f'0x{s.ea:X}',
                'string': str(s),
                'length': s.length
            })
    
    return menu_strings

def find_functions_by_instruction_pattern():
    """Find functions with patterns typical of menu/UI code"""
    candidates = []
    
    print("Searching for UI-pattern functions...")
    
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        func_name = idc.get_func_name(func_ea)
        func_size = func.end_ea - func.start_ea
        
        # Skip tiny functions
        if func_size < 30:
            continue
        
        # Count UI-related patterns
        call_count = 0
        data_ref_count = 0
        loop_count = 0
        conditional_count = 0
        
        ea = func.start_ea
        while ea < func.end_ea:
            mnem = idc.print_insn_mnem(ea)
            
            if mnem in ['call', 'callf']:
                call_count += 1
            elif mnem in ['loop', 'loope', 'loopne']:
                loop_count += 1
            elif mnem in ['jz', 'jnz', 'je', 'jne', 'jg', 'jl', 'jge', 'jle']:
                conditional_count += 1
            
            # Check for data references
            for i in range(2):
                op_type = idc.get_operand_type(ea, i)
                if op_type in [idc.o_mem, idc.o_displ]:
                    data_ref_count += 1
            
            ea = idc.next_head(ea, func.end_ea)
        
        # Score based on patterns
        # UI functions typically have many calls, conditionals, and data refs
        score = 0
        if call_count >= 5:
            score += call_count
        if data_ref_count >= 10:
            score += data_ref_count // 2
        if conditional_count >= 5:
            score += conditional_count // 2
        
        if score >= 15:
            candidates.append({
                'address': func_ea,
                'hex_addr': f'0x{func_ea:X}',
                'name': func_name,
                'size': func_size,
                'calls': call_count,
                'data_refs': data_ref_count,
                'conditionals': conditional_count,
                'score': score
            })
    
    return sorted(candidates, key=lambda x: x['score'], reverse=True)

def analyze_known_menu_data():
    """Analyze data accessed by known menu functions"""
    known_menu_funcs = [
        0x683C5,   # sub_683C5 - Main menu controller
        0x66E62,   # sub_66E62 - Menu panel init
        0x6A5BD,   # sub_6A5BD - Menu page setup
        0x133ADC,  # ui_menu_panel_renderer
        0x127ED2,  # menu_panel_background_draw
    ]
    
    print("Analyzing data accessed by known menu functions...")
    
    data_addrs = set()
    
    for func_ea in known_menu_funcs:
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        ea = func.start_ea
        while ea < func.end_ea:
            for i in range(2):
                op_type = idc.get_operand_type(ea, i)
                if op_type in [idc.o_mem, idc.o_displ]:
                    data_addr = idc.get_operand_value(ea, i)
                    if data_addr != idc.BADADDR:
                        data_addrs.add(data_addr)
            
            ea = idc.next_head(ea, func.end_ea)
    
    return list(data_addrs)

def main():
    print("="*60)
    print("FINDING MENU FUNCTIONS BY DATA REFERENCES")
    print("="*60)
    
    # 1. Find data accessed by known menu functions
    print("\n1. Analyzing known menu function data access...")
    menu_data_addrs = analyze_known_menu_data()
    print(f"   Found {len(menu_data_addrs)} unique data addresses")
    
    # 2. Find all functions that access this menu data
    print("\n2. Finding functions that reference menu data...")
    data_ref_funcs = find_functions_referencing_data(menu_data_addrs[:100])  # Limit to avoid too many
    print(f"   Found {len(data_ref_funcs)} functions")
    
    # 3. Find menu-related strings
    print("\n3. Searching for menu-related strings...")
    menu_strings = find_string_patterns()
    print(f"   Found {len(menu_strings)} menu strings")
    
    # 4. Find functions by UI patterns
    print("\n4. Finding functions by UI code patterns...")
    pattern_funcs = find_functions_by_instruction_pattern()
    print(f"   Found {len(pattern_funcs)} candidates")
    
    # Combine results
    all_funcs = {}
    
    # Add pattern-based functions
    for func in pattern_funcs[:50]:  # Top 50
        all_funcs[func['name']] = func
        all_funcs[func['name']]['source'] = 'pattern'
    
    # Add data-reference functions
    for name, func in data_ref_funcs.items():
        if name not in all_funcs:
            all_funcs[name] = func
            all_funcs[name]['source'] = 'data_ref'
        else:
            all_funcs[name]['source'] = 'both'
    
    # Print summary
    print(f"\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"Total unique functions found: {len(all_funcs)}")
    print(f"\nTop 30 by score/relevance:")
    
    # Sort by source and score
    sorted_funcs = sorted(all_funcs.items(), 
                         key=lambda x: (x[1].get('score', 0), len(x[1].get('data_refs', []))),
                         reverse=True)
    
    for i, (name, info) in enumerate(sorted_funcs[:30]):
        score = info.get('score', 0)
        source = info.get('source', 'unknown')
        print(f"{i+1:2d}. 0x{info['address']:06X} {name:40s} [{source}] score={score}")
    
    # Save results
    results = {
        'functions': all_funcs,
        'menu_strings': menu_strings[:50],
        'menu_data_addrs': [f'0x{addr:X}' for addr in menu_data_addrs[:50]]
    }
    
    output_path = r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\menu_data_analysis.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")

if __name__ == '__main__':
    main()
    idc.qexit(0)
