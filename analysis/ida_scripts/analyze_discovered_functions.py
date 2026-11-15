"""
Analyze the top discovered UI/menu functions in detail
"""
import idaapi
import idautils
import idc
import json

def analyze_function_detailed(func_ea):
    """Get detailed analysis of a function"""
    func = idaapi.get_func(func_ea)
    if not func:
        return None
    
    func_name = idc.get_func_name(func_ea)
    
    # Get all callees
    callees = []
    callers = []
    
    # Find what this function calls
    ea = func.start_ea
    while ea < func.end_ea:
        for xref in idautils.XrefsFrom(ea, 0):
            if xref.type in [idc.fl_CN, idc.fl_CF]:  # Call
                target_name = idc.get_func_name(xref.to)
                if target_name:
                    callees.append({
                        'addr': xref.to,
                        'hex_addr': f'0x{xref.to:X}',
                        'name': target_name,
                        'call_site': ea,
                        'call_site_hex': f'0x{ea:X}'
                    })
        ea = idc.next_head(ea, func.end_ea)
    
    # Find who calls this function
    for xref in idautils.XrefsTo(func.start_ea, 0):
        if xref.type in [idc.fl_CN, idc.fl_CF]:
            caller_name = idc.get_func_name(xref.frm)
            if caller_name:
                callers.append({
                    'addr': xref.frm,
                    'hex_addr': f'0x{xref.frm:X}',
                    'name': caller_name
                })
    
    # Get strings referenced
    strings_ref = []
    ea = func.start_ea
    while ea < func.end_ea:
        for xref in idautils.XrefsFrom(ea, 0):
            if xref.type == idc.fl_F:  # Data reference
                # Check if it's a string
                str_type = idc.get_str_type(xref.to)
                if str_type >= 0:
                    str_val = idc.get_strlit_contents(xref.to)
                    if str_val:
                        strings_ref.append({
                            'addr': xref.to,
                            'hex_addr': f'0x{xref.to:X}',
                            'string': str_val.decode('ascii', errors='ignore')[:80]
                        })
        ea = idc.next_head(ea, func.end_ea)
    
    # Get first 50 instructions for preview
    disasm_preview = []
    ea = func.start_ea
    count = 0
    while ea < func.end_ea and count < 50:
        disasm = idc.generate_disasm_line(ea, 0)
        disasm_preview.append({
            'addr': ea,
            'hex_addr': f'0x{ea:X}',
            'disasm': disasm
        })
        ea = idc.next_head(ea, func.end_ea)
        count += 1
    
    return {
        'address': func.start_ea,
        'hex_addr': f'0x{func.start_ea:X}',
        'name': func_name,
        'size': func.end_ea - func.start_ea,
        'callees': callees,
        'callers': callers,
        'strings': strings_ref,
        'disasm_preview': disasm_preview
    }

def categorize_function(func_info):
    """Categorize function based on its properties"""
    name = func_info['name'].lower()
    callees = [c['name'].lower() for c in func_info['callees']]
    strings = [s['string'].lower() for s in func_info['strings']]
    
    categories = []
    
    # Check name patterns
    if any(k in name for k in ['menu', 'ui_', 'panel']):
        categories.append('menu_ui')
    if any(k in name for k in ['overlay', 'dispatcher', 'coordinator', 'handler']):
        categories.append('overlay_control')
    if any(k in name for k in ['render', 'draw', 'display', 'paint']):
        categories.append('graphics')
    if any(k in name for k in ['input', 'key', 'mouse', 'joystick']):
        categories.append('input')
    if any(k in name for k in ['loadout', 'weapon', 'mission', 'pilot']):
        categories.append('game_state')
    
    # Check callees
    if any('render' in c or 'draw' in c for c in callees):
        categories.append('graphics')
    if any('menu' in c or 'ui' in c for c in callees):
        categories.append('menu_ui')
    if any('file' in c or 'load' in c or 'read' in c for c in callees):
        categories.append('file_io')
    
    # Check strings
    if any('menu' in s or 'screen' in s for s in strings):
        categories.append('menu_ui')
    
    return list(set(categories)) if categories else ['uncategorized']

def main():
    print("="*60)
    print("DETAILED ANALYSIS OF DISCOVERED FUNCTIONS")
    print("="*60)
    
    # Load the scored functions
    input_path = r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\ui_functions_scored.json'
    with open(input_path, 'r') as f:
        scored_funcs = json.load(f)
    
    print(f"\nAnalyzing top 30 functions in detail...")
    
    results = {}
    
    for i, func_data in enumerate(scored_funcs[:30]):
        func_ea = func_data['address']
        print(f"\n{i+1}. Analyzing {func_data['name']} at 0x{func_ea:X}...")
        
        analysis = analyze_function_detailed(func_ea)
        if analysis:
            analysis['score'] = func_data['score']
            analysis['stats'] = func_data['stats']
            analysis['categories'] = categorize_function(analysis)
            
            results[analysis['name']] = analysis
            
            print(f"   Size: {analysis['size']} bytes")
            print(f"   Callees: {len(analysis['callees'])}")
            print(f"   Callers: {len(analysis['callers'])}")
            print(f"   Strings: {len(analysis['strings'])}")
            print(f"   Categories: {', '.join(analysis['categories'])}")
    
    # Print categorized summary
    print("\n" + "="*60)
    print("CATEGORIZED RESULTS")
    print("="*60)
    
    by_category = {}
    for name, info in results.items():
        for cat in info['categories']:
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append((name, info))
    
    for cat, funcs in sorted(by_category.items()):
        print(f"\n{cat.upper().replace('_', ' ')} ({len(funcs)} functions):")
        for name, info in sorted(funcs, key=lambda x: x[1]['score'], reverse=True)[:5]:
            print(f"  0x{info['address']:06X}: {name:40s} score={info['score']}")
            if info['strings']:
                print(f"    Strings: {info['strings'][0]['string'][:60]}...")
            if info['callees'][:3]:
                print(f"    Calls: {', '.join(c['name'] for c in info['callees'][:3])}")
    
    # Save detailed results
    output_path = r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\functions_detailed_analysis.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n\nDetailed analysis saved to: {output_path}")
    print(f"Total functions analyzed: {len(results)}")

if __name__ == '__main__':
    main()
    idc.qexit(0)
