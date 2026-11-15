"""
Simpler analysis of top functions - just get basic info
"""
import idaapi
import idautils
import idc
import json

def get_function_calls(func_ea):
    """Get all functions called by this function"""
    func = idaapi.get_func(func_ea)
    if not func:
        return []
    
    callees = []
    ea = func.start_ea
    
    while ea < func.end_ea:
        if idc.print_insn_mnem(ea) in ['call', 'callf']:
            for xref in idautils.XrefsFrom(ea, 0):
                if xref.type in [idc.fl_CN, idc.fl_CF]:
                    target_name = idc.get_func_name(xref.to)
                    if target_name and target_name not in [c['name'] for c in callees]:
                        callees.append({
                            'addr': xref.to,
                            'name': target_name
                        })
        
        ea = idc.next_head(ea, func.end_ea)
    
    return callees

def get_function_callers(func_ea):
    """Get all functions that call this function"""
    callers = []
    
    for xref in idautils.XrefsTo(func_ea, 0):
        if xref.type in [idc.fl_CN, idc.fl_CF]:
            caller_name = idc.get_func_name(xref.frm)
            if caller_name and caller_name not in [c['name'] for c in callers]:
                callers.append({
                    'addr': xref.frm,
                    'name': caller_name
                })
    
    return callers

def main():
    print("Analyzing top 30 functions...")
    
    # Load scored functions
    try:
        input_path = r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\ui_functions_scored.json'
        with open(input_path, 'r') as f:
            scored_funcs = json.load(f)
        print(f"Loaded {len(scored_funcs)} scored functions")
    except Exception as e:
        print(f"Error loading: {e}")
        return
    
    results = []
    
    for i, func_data in enumerate(scored_funcs[:30]):
        func_ea = func_data['address']
        func_name = func_data['name']
        
        print(f"{i+1}. {func_name} at 0x{func_ea:X}")
        
        try:
            callees = get_function_calls(func_ea)
            callers = get_function_callers(func_ea)
            
            results.append({
                'address': func_ea,
                'hex_addr': f'0x{func_ea:X}',
                'name': func_name,
                'score': func_data['score'],
                'stats': func_data['stats'],
                'callees': callees,
                'callers': callers
            })
            
            print(f"   Callees: {len(callees)}, Callers: {len(callers)}")
            
        except Exception as e:
            print(f"   Error analyzing: {e}")
    
    # Save
    output_path = r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\top_functions_analysis.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nSaved {len(results)} function analyses to: {output_path}")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
    
    idc.qexit(0)
