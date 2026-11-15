"""
Continue analysis with next high-priority functions:
1. input_poll_handler - the actual input polling
2. input_finalization (undoc_130B39) - called after input ready
3. pit_channel0_latch_read - timer reading for entropy
"""
import idaapi
import idc
import idautils
import json

def analyze_function_quick(func_name):
    """Quick analysis of a function"""
    target_ea = idc.get_name_ea_simple(func_name)
    
    if target_ea == idc.BADADDR:
        print(f"[-] {func_name} not found")
        return None
    
    func = idaapi.get_func(target_ea)
    if not func:
        print(f"[-] No function at 0x{target_ea:X} for {func_name}")
        return None
    
    result = {
        'name': func_name,
        'start': target_ea,
        'end': func.end_ea,
        'size': func.end_ea - target_ea,
        'instructions': [],
        'callees': set(),
        'caller_count': 0
    }
    
    # Count callers
    for xref in idautils.XrefsTo(target_ea):
        if idc.get_func_name(xref.frm):
            result['caller_count'] += 1
    
    # Analyze instructions
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if not idc.is_code(idc.get_full_flags(head)):
            continue
        
        mnem = idc.print_insn_mnem(head)
        disasm = idc.GetDisasm(head)
        
        result['instructions'].append({
            'addr': head,
            'mnem': mnem,
            'disasm': disasm
        })
        
        # Track calls
        if mnem in ['call', 'jmp']:
            for xref in idautils.XrefsFrom(head):
                if xref.type in [idaapi.fl_CF, idaapi.fl_CN]:
                    callee = idc.get_func_name(xref.to)
                    if callee:
                        result['callees'].add(callee)
    
    result['callees'] = sorted(list(result['callees']))
    return result

def main():
    try:
        print("[*] Waiting for auto-analysis...")
        idaapi.auto_wait()
        print("[+] Auto-analysis complete")
        
        # Add comment to farobj_vec3_accum_b_ret
        vec3_ea = idc.get_name_ea_simple('farobj_vec3_accum_b_ret')
        if vec3_ea != idc.BADADDR:
            idc.set_cmt(vec3_ea, "Returns CX from fixed_vec3_accumulate_b. Used for vector math AND timing-based pseudo-RNG.", 0)
            print("[+] Added comment to farobj_vec3_accum_b_ret")
        
        print("\n=== ANALYZING INPUT FUNCTIONS ===\n")
        
        # Analyze input handling functions
        targets = [
            'input_poll_handler',
            'input_finalization',  # undoc_130B39
            'pit_channel0_latch_read'
        ]
        
        results = {}
        
        for func_name in targets:
            print(f"[*] Analyzing {func_name}...")
            result = analyze_function_quick(func_name)
            
            if result:
                print(f"[+] {func_name}:")
                print(f"    Address: 0x{result['start']:X}")
                print(f"    Size: {result['size']} bytes")
                print(f"    Instructions: {len(result['instructions'])}")
                print(f"    Callees: {len(result['callees'])}")
                print(f"    Callers: {result['caller_count']}")
                
                if result['size'] <= 100:  # Print full disasm for small functions
                    print(f"    Full disassembly:")
                    for insn in result['instructions']:
                        print(f"      0x{insn['addr']:X}: {insn['disasm']}")
                
                results[func_name] = result
            else:
                print(f"[-] Could not analyze {func_name}")
            print()
        
        # Save results
        output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\input_functions_analysis.json"
        with open(output_file, 'w') as f:
            # Convert sets to lists for JSON
            json_results = {}
            for name, data in results.items():
                json_results[name] = {
                    'name': data['name'],
                    'start': data['start'],
                    'end': data['end'],
                    'size': data['size'],
                    'caller_count': data['caller_count'],
                    'callees': data['callees'],
                    'instruction_count': len(data['instructions']),
                    'instructions': data['instructions'][:50]  # Limit to first 50
                }
            json.dump(json_results, f, indent=2)
        print(f"[+] Saved to {output_file}")
        
        print("\n=== SUMMARY ===")
        for name, data in results.items():
            print(f"{name}:")
            print(f"  Size: {data['size']} bytes, {len(data['instructions'])} instructions")
            print(f"  Callers: {data['caller_count']}")
            if data['callees']:
                print(f"  Callees: {', '.join(data['callees'][:5])}")
        
    except Exception as e:
        print(f"[-] ERROR: {e}")
        import traceback
        traceback.print_exc()
        idc.qexit(1)

if __name__ == "__main__":
    main()
    idc.qexit(0)
