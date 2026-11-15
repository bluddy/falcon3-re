"""
Rename undoc_12841F to menu_state_init_with_random
Then analyze undoc_1295A9 (the post-processor)
"""
import idaapi
import idc
import idautils
import json

def main():
    try:
        print("[*] Waiting for auto-analysis...")
        idaapi.auto_wait()
        print("[+] Auto-analysis complete")
        
        # Rename undoc_12841F
        old_addr = 0x12841F
        new_name = "menu_state_init_with_random"
        if idc.set_name(old_addr, new_name, idc.SN_NOWARN):
            print(f"[+] Renamed 0x{old_addr:X} to {new_name}")
        else:
            print(f"[-] Failed to rename 0x{old_addr:X}")
        
        # Now analyze undoc_1295A9 (called with params 0x1F, 0x0A, far_ptr)
        target_ea = 0x1295A9
        
        print(f"\n[*] Analyzing function at 0x{target_ea:X}")
        
        func = idaapi.get_func(target_ea)
        if not func:
            print(f"[-] No function at 0x{target_ea:X}")
            idc.qexit(1)
            return
        
        func_name = idc.get_func_name(target_ea)
        print(f"[+] Found function: {func_name}")
        
        result = {
            'name': func_name,
            'start': target_ea,
            'end': func.end_ea,
            'size': func.end_ea - target_ea,
            'instructions': [],
            'callees': [],
            'callers': [],
            'data_refs': [],
            'segments_used': {}
        }
        
        # Get callers
        for xref in idautils.XrefsTo(target_ea):
            caller_name = idc.get_func_name(xref.frm)
            if caller_name:
                result['callers'].append({
                    'addr': xref.frm,
                    'name': caller_name
                })
        
        print(f"[+] Found {len(result['callers'])} callers")
        
        # Analyze instructions
        callees_set = set()
        insn_count = 0
        for head in idautils.Heads(func.start_ea, func.end_ea):
            if not idc.is_code(idc.get_full_flags(head)):
                continue
            
            insn_count += 1
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
        
        print(f"[+] Size: {result['size']} bytes")
        print(f"[+] Instructions: {len(result['instructions'])}")
        print(f"[+] Callees: {len(result['callees'])}")
        
        # Save
        output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\undoc_1295A9_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"[+] Saved to {output_file}")
        
        # Print summary
        print("\n=== CALLERS ===")
        for caller in result['callers'][:10]:
            print(f"  0x{caller['addr']:X}: {caller['name']}")
        if len(result['callers']) > 10:
            print(f"  ... and {len(result['callers']) - 10} more")
        
        print("\n=== CALLEES ===")
        for callee in result['callees'][:10]:
            print(f"  {callee}")
        if len(result['callees']) > 10:
            print(f"  ... and {len(result['callees']) - 10} more")
        
        print("\n=== SEGMENTS USED ===")
        for seg_name, refs in sorted(result['segments_used'].items()):
            unique_refs = set(r['name'] if r['name'] else hex(r['addr']) for r in refs)
            print(f"  {seg_name}: {len(refs)} references, {len(unique_refs)} unique")
        
    except Exception as e:
        print(f"[-] ERROR: {e}")
        import traceback
        traceback.print_exc()
        idc.qexit(1)

if __name__ == "__main__":
    main()
    idc.qexit(0)
