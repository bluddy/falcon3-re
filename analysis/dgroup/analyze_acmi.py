"""
Analyze ACMI system and its relationship to view_pipeline_mode.

Found:
- Menu option "K4.`ACMI" at case 8 in menu dispatcher (0x1909A0)
- ACMI handler function at 0x11CC39
- ACMI data files: acmi.idx, acmi.dat
"""

import idc
import idaapi
import idautils
import json

def analyze_acmi_handler():
    """Analyze the ACMI menu handler function."""
    
    handler_addr = 0x11CC39
    
    print(f"[*] Analyzing ACMI handler at 0x{handler_addr:X}")
    
    func = idaapi.get_func(handler_addr)
    if not func:
        print(f"  [!] No function at 0x{handler_addr:X}")
        return None
    
    func_name = idc.get_func_name(handler_addr)
    print(f"  Function: {func_name}")
    print(f"  Size: {func.end_ea - func.start_ea} bytes")
    print(f"\n  First 50 instructions:")
    
    ea = func.start_ea
    instructions = []
    
    for i in range(min(50, func.end_ea - func.start_ea)):
        insn = idc.GetDisasm(ea)
        print(f"    0x{ea:X}: {insn}")
        
        # Look for calls to view_mode_set or writes to view_pipeline_mode
        if 'view_mode_set' in insn or '107762' in insn or 'view_pipeline_mode' in insn:
            print(f"      ^^^ INTERESTING: Possible mode setting!")
        
        instructions.append({
            'addr': f'0x{ea:X}',
            'insn': insn
        })
        
        ea = idc.next_head(ea, func.end_ea)
        if ea >= func.end_ea:
            break
    
    return {
        'addr': f'0x{handler_addr:X}',
        'name': func_name,
        'size': func.end_ea - func.start_ea,
        'instructions': instructions
    }

def find_acmi_file_operations():
    """Find operations on ACMI files (acmi.idx, acmi.dat)."""
    
    print("\n[*] Finding ACMI file operations...")
    
    # Search for "acmi" string references
    acmi_strings = []
    
    for s in idautils.Strings():
        if 'acmi' in str(s).lower() or 'ACMI' in str(s):
            str_addr = s.ea
            str_content = str(s)
            
            print(f"\n  String at 0x{str_addr:X}: \"{str_content}\"")
            
            # Find xrefs
            refs = []
            for xref in idautils.XrefsTo(str_addr):
                func = idc.get_func_name(xref.frm)
                print(f"    → Used in {func} at 0x{xref.frm:X}")
                refs.append({
                    'addr': f'0x{xref.frm:X}',
                    'func': func
                })
            
            acmi_strings.append({
                'addr': f'0x{str_addr:X}',
                'content': str_content,
                'refs': refs
            })
    
    return acmi_strings

def trace_from_menu_to_mode():
    """Trace execution from ACMI menu selection to mode setting."""
    
    print("\n[*] Tracing ACMI menu → mode setting...")
    
    # Menu dispatcher at 0x1909A0, case 8 calls 0x11CC39
    menu_case_addr = 0x190A8B
    
    print(f"  Menu case 8 (ACMI) at 0x{menu_case_addr:X}")
    print(f"  Calls sub_11CC39")
    print(f"  Need to trace: sub_11CC39 → ... → view_mode_set(1)?")
    
    # Look for path from 0x11CC39 to view_mode_set
    acmi_handler = 0x11CC39
    view_mode_set_start = 0x1086EC  # view_mode_set function start
    
    # Get callees of ACMI handler
    func = idaapi.get_func(acmi_handler)
    if func:
        print(f"\n  Calls from ACMI handler:")
        ea = func.start_ea
        calls = []
        
        while ea < func.end_ea:
            mnem = idc.print_insn_mnem(ea)
            if mnem == 'call':
                target = idc.get_operand_value(ea, 0)
                target_name = idc.get_name(target)
                
                if target_name:
                    calls.append({
                        'addr': f'0x{ea:X}',
                        'target': f'0x{target:X}',
                        'name': target_name
                    })
                    
                    # Check if this is view_mode_set!
                    if target == view_mode_set_start or 'view_mode' in target_name.lower():
                        print(f"    >>> 0x{ea:X}: call {target_name} [FOUND MODE SETTER!]")
                    else:
                        print(f"    0x{ea:X}: call {target_name}")
            
            ea = idc.next_head(ea, func.end_ea)
        
        return calls
    
    return []

def check_all_mode_set_callers():
    """Find all callers of view_mode_set to see context."""
    
    print("\n[*] Finding all callers of view_mode_set...")
    
    view_mode_set = 0x1086EC
    
    callers = []
    for xref in idautils.XrefsTo(view_mode_set):
        if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
            caller_addr = xref.frm
            func = idc.get_func_name(caller_addr)
            
            # Show context
            print(f"\n  Called from {func} at 0x{caller_addr:X}")
            print(f"    Context:")
            
            # Show 5 instructions before and after
            context_ea = caller_addr - 10  # Rough guess
            for i in range(10):
                insn = idc.GetDisasm(context_ea)
                marker = ">>>" if context_ea == caller_addr else "   "
                print(f"    {marker} 0x{context_ea:X}: {insn}")
                context_ea = idc.next_head(context_ea)
            
            callers.append({
                'addr': f'0x{caller_addr:X}',
                'func': func
            })
    
    return callers

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("ACMI SYSTEM ANALYSIS")
    print("="*80)
    
    results = {}
    
    # 1. Analyze ACMI handler
    print("\n[1/4] ACMI HANDLER")
    print("-"*80)
    results['acmi_handler'] = analyze_acmi_handler()
    
    # 2. Find ACMI file operations
    print("\n[2/4] ACMI FILE OPERATIONS")
    print("-"*80)
    results['acmi_files'] = find_acmi_file_operations()
    
    # 3. Trace menu to mode
    print("\n[3/4] MENU TO MODE TRACE")
    print("-"*80)
    results['menu_to_mode'] = trace_from_menu_to_mode()
    
    # 4. All mode set callers
    print("\n[4/4] ALL MODE SET CALLERS")
    print("-"*80)
    results['mode_set_callers'] = check_all_mode_set_callers()
    
    # Save
    output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\dgroup\acmi_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n\nResults saved to: {output_file}")
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
