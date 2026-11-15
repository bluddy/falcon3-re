"""
Analyze the drawing primitive functions called by ui_text_render_engine
Starting with undoc_12B07D, undoc_12BE93, undoc_12BED1
"""
import idaapi
import idc
import idautils
import json

def analyze_function(func_name):
    """Analyze a single function and return results"""
    target_ea = idc.get_name_ea_simple(func_name)
    
    if target_ea == idc.BADADDR:
        return None
    
    func = idaapi.get_func(target_ea)
    if not func:
        return None
    
    result = {
        'name': func_name,
        'start': target_ea,
        'end': func.end_ea,
        'size': func.end_ea - target_ea,
        'instructions': [],
        'callees': [],
        'callers': [],
        'segments_used': {}
    }
    
    # Get callers (limit to 15)
    caller_count = 0
    for xref in idautils.XrefsTo(target_ea):
        caller_name = idc.get_func_name(xref.frm)
        if caller_name:
            if caller_count < 15:
                result['callers'].append({
                    'addr': xref.frm,
                    'name': caller_name
                })
            caller_count += 1
    
    result['total_callers'] = caller_count
    
    # Analyze instructions
    callees_set = set()
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if not idc.is_code(idc.get_full_flags(head)):
            continue
        
        mnem = idc.print_insn_mnem(head)
        disasm = idc.GetDisasm(head)
        
        insn_data = {
            'addr': head,
            'mnem': mnem,
            'disasm': disasm
        }
        
        # Track calls
        if mnem in ['call', 'jmp']:
            for xref in idautils.XrefsFrom(head):
                if xref.type in [idaapi.fl_CF, idaapi.fl_CN]:
                    callee = idc.get_func_name(xref.to)
                    if callee:
                        callees_set.add(callee)
                        insn_data['callee'] = callee
        
        # Track data refs
        for op_idx in range(2):
            op_type = idc.get_operand_type(head, op_idx)
            if op_type in [idc.o_mem, idc.o_displ]:
                ref_ea = idc.get_operand_value(head, op_idx)
                seg = idaapi.getseg(ref_ea)
                if seg:
                    seg_name = idaapi.get_segm_name(seg)
                    ref_name = idc.get_name(ref_ea)
                    
                    if seg_name not in result['segments_used']:
                        result['segments_used'][seg_name] = []
                    result['segments_used'][seg_name].append({
                        'addr': ref_ea,
                        'name': ref_name if ref_name else None
                    })
        
        result['instructions'].append(insn_data)
    
    result['callees'] = sorted(list(callees_set))
    
    return result

def main():
    try:
        print("[*] Waiting for auto-analysis...")
        idaapi.auto_wait()
        print("[+] Auto-analysis complete")
        
        # Analyze the three drawing primitives
        targets = [
            'undoc_12B07D',
            'undoc_12BE93',
            'undoc_12BED1'
        ]
        
        results = {}
        
        for func_name in targets:
            print(f"\n[*] Analyzing {func_name}...")
            result = analyze_function(func_name)
            
            if result:
                print(f"[+] {func_name}:")
                print(f"    Address: 0x{result['start']:X}")
                print(f"    Size: {result['size']} bytes")
                print(f"    Instructions: {len(result['instructions'])}")
                print(f"    Callees: {len(result['callees'])}")
                print(f"    Callers: {result['total_callers']}")
                
                results[func_name] = result
            else:
                print(f"[-] Could not analyze {func_name}")
        
        # Also analyze utility_900 (called first by ui_text_render_engine)
        print(f"\n[*] Analyzing utility_900...")
        result = analyze_function('utility_900')
        if result:
            print(f"[+] utility_900:")
            print(f"    Address: 0x{result['start']:X}")
            print(f"    Size: {result['size']} bytes")
            print(f"    Instructions: {len(result['instructions'])}")
            print(f"    Callees: {len(result['callees'])}")
            print(f"    Callers: {result['total_callers']}")
            results['utility_900'] = result
        
        # Save all results
        output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\drawing_primitives_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n[+] Saved all results to {output_file}")
        
        # Print summary
        print("\n=== SUMMARY ===")
        for func_name, data in results.items():
            print(f"\n{func_name}:")
            print(f"  Size: {data['size']} bytes")
            print(f"  Callers: {data['total_callers']}")
            if data['callees']:
                print(f"  Callees: {', '.join(data['callees'][:5])}")
                if len(data['callees']) > 5:
                    print(f"           ... and {len(data['callees']) - 5} more")
            if data['segments_used']:
                print(f"  Segments: {', '.join(data['segments_used'].keys())}")
        
    except Exception as e:
        print(f"[-] ERROR: {e}")
        import traceback
        traceback.print_exc()
        idc.qexit(1)

if __name__ == "__main__":
    main()
    idc.qexit(0)
