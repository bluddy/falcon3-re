"""
Search for ACMI-related strings and their references.

ACMI = Air Combat Maneuvering Instrumentation
Should find menu options, file handling, mode initialization.
"""

import idc
import idaapi
import idautils
import json

def find_strings_containing(search_terms):
    """Find all strings containing any of the search terms."""
    
    results = []
    
    for s in idautils.Strings():
        str_content = str(s)
        str_addr = s.ea
        
        # Check if any search term matches
        for term in search_terms:
            if term.upper() in str_content.upper():
                # Find references to this string
                refs = []
                for xref in idautils.XrefsTo(str_addr):
                    func = idc.get_func_name(xref.frm)
                    seg = idc.get_segm_name(xref.frm)
                    refs.append({
                        'addr': f'0x{xref.frm:X}',
                        'func': func,
                        'segment': seg
                    })
                
                results.append({
                    'addr': f'0x{str_addr:X}',
                    'string': str_content,
                    'matched_term': term,
                    'length': len(str_content),
                    'refs': refs
                })
                
                print(f"\n[FOUND] 0x{str_addr:X}: \"{str_content}\"")
                print(f"  Matched: {term}")
                print(f"  References: {len(refs)}")
                for ref in refs[:5]:  # Show first 5
                    print(f"    → 0x{ref['addr']} in {ref['segment']}/{ref['func']}")
                if len(refs) > 5:
                    print(f"    ... and {len(refs)-5} more")
                
                break  # Don't match multiple terms for same string
    
    return results

def analyze_view_mode_set():
    """Analyze the view_mode_set function to see what values it sets."""
    
    print("\n" + "="*80)
    print("ANALYZING view_mode_set FUNCTION")
    print("="*80)
    
    # The function that sets view_pipeline_mode
    # We know it writes to 0x107762
    
    # Find the function containing the write
    write_addr = 0x1087B2  # Known write location
    
    func = idaapi.get_func(write_addr)
    if not func:
        print(f"No function found at write location 0x{write_addr:X}")
        return None
    
    func_start = func.start_ea
    func_name = idc.get_func_name(func_start)
    
    print(f"\nFunction: {func_name} at 0x{func_start:X}")
    print(f"Size: {func.end_ea - func_start} bytes")
    print(f"\nDisassembly:")
    
    # Show full function
    ea = func.start_ea
    instructions = []
    
    while ea < func.end_ea:
        insn = idc.GetDisasm(ea)
        addr_str = f'0x{ea:X}'
        
        # Highlight the actual write
        if ea == write_addr:
            print(f"  >>> {addr_str}: {insn}  [WRITES view_pipeline_mode]")
        else:
            print(f"      {addr_str}: {insn}")
        
        instructions.append({
            'addr': addr_str,
            'insn': insn
        })
        
        ea = idc.next_head(ea, func.end_ea)
    
    # Find who calls this function
    print(f"\n[*] Finding callers of {func_name}...")
    callers = []
    
    for xref in idautils.XrefsTo(func_start):
        if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
            caller_addr = xref.frm
            caller_func = idc.get_func_name(caller_addr)
            caller_seg = idc.get_segm_name(caller_addr)
            
            callers.append({
                'addr': f'0x{caller_addr:X}',
                'func': caller_func,
                'segment': caller_seg
            })
            
            print(f"    Called from 0x{caller_addr:X} in {caller_seg}/{caller_func}")
    
    return {
        'func_name': func_name,
        'func_addr': f'0x{func_start:X}',
        'write_addr': f'0x{write_addr:X}',
        'instructions': instructions,
        'callers': callers
    }

def search_for_mode_checks():
    """Find all places that check view_pipeline_mode value."""
    
    print("\n" + "="*80)
    print("FINDING view_pipeline_mode CHECKS")
    print("="*80)
    
    flag_addr = 0x107762
    
    checks = []
    
    for xref in idautils.XrefsTo(flag_addr):
        addr = xref.frm
        insn = idc.GetDisasm(addr)
        mnem = idc.print_insn_mnem(addr)
        
        # Look for comparisons
        if mnem in ['cmp', 'test']:
            func = idc.get_func_name(addr)
            seg = idc.get_segm_name(addr)
            
            # Show context (5 instructions)
            print(f"\n[CHECK] 0x{addr:X} in {seg}/{func}")
            context_start = addr
            for i in range(5):
                context_insn = idc.GetDisasm(context_start)
                marker = ">>>" if context_start == addr else "   "
                print(f"  {marker} 0x{context_start:X}: {context_insn}")
                context_start = idc.next_head(context_start)
            
            checks.append({
                'addr': f'0x{addr:X}',
                'func': func,
                'segment': seg,
                'insn': insn
            })
    
    print(f"\n[*] Found {len(checks)} checks of view_pipeline_mode")
    
    return checks

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("ACMI INVESTIGATION")
    print("="*80)
    
    # Search for ACMI-related strings
    print("\n[1/3] SEARCHING FOR ACMI STRINGS")
    print("-"*80)
    
    search_terms = [
        'ACMI',
        'Air Combat',
        'Maneuvering',
        'Instrumentation',
        'Replay',
        'Playback',
        'Recording',
        'Record',
        'Tape',  # ACMI recordings sometimes called "tapes"
        '.VCR',  # Possible file extension
        '.ACM',  # Possible file extension
        '.TRK',  # Track file?
    ]
    
    string_results = find_strings_containing(search_terms)
    
    # Analyze view_mode_set
    print("\n[2/3] ANALYZING view_mode_set")
    print("-"*80)
    
    view_mode_info = analyze_view_mode_set()
    
    # Find all mode checks
    print("\n[3/3] FINDING MODE CHECKS")
    print("-"*80)
    
    mode_checks = search_for_mode_checks()
    
    # Save results
    output = {
        'strings_found': string_results,
        'view_mode_set_analysis': view_mode_info,
        'mode_checks': mode_checks
    }
    
    output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\dgroup\acmi_investigation.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"ACMI strings found: {len(string_results)}")
    print(f"view_mode_set callers: {len(view_mode_info['callers']) if view_mode_info else 0}")
    print(f"Mode checks found: {len(mode_checks)}")
    print(f"\nResults saved to: {output_file}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
