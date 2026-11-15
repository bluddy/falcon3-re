"""
Verify renames were applied and continue analysis with farobj_vec3_accum_b_ret
This mystery function is called 4 times for "random" values
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
        
        print("\n=== VERIFYING RENAMES ===\n")
        
        # Verify key renames
        verifications = [
            (0x130A2F, "input_sync_and_wait"),
            (0x128D5A, "ui_render_coordinator"),
            (0x1295A9, "ui_text_render_loop"),
            (0x12841F, "menu_state_init_with_random"),
            (0x79B68, "input_flag_pending_1"),
            (0x79B66, "input_flag_pending_2"),
        ]
        
        for addr, expected_name in verifications:
            actual_name = idc.get_name(addr)
            if actual_name == expected_name:
                print(f"[+] 0x{addr:X}: {actual_name} ✓")
            else:
                print(f"[-] 0x{addr:X}: Expected '{expected_name}', got '{actual_name}'")
        
        print("\n=== ANALYZING farobj_vec3_accum_b_ret ===\n")
        
        # This function is called 4 times for "random" generation
        target_ea = idc.get_name_ea_simple('farobj_vec3_accum_b_ret')
        
        if target_ea == idc.BADADDR:
            print("[-] farobj_vec3_accum_b_ret not found")
            idc.qexit(1)
            return
        
        print(f"[+] Found farobj_vec3_accum_b_ret at 0x{target_ea:X}")
        
        func = idaapi.get_func(target_ea)
        if not func:
            print(f"[-] No function at 0x{target_ea:X}")
            idc.qexit(1)
            return
        
        result = {
            'name': 'farobj_vec3_accum_b_ret',
            'start': target_ea,
            'end': func.end_ea,
            'size': func.end_ea - target_ea,
            'instructions': [],
            'callees': [],
            'callers': [],
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
        
        print(f"[+] Size: {result['size']} bytes")
        print(f"[+] Instructions: {len(result['instructions'])}")
        print(f"[+] Callees: {len(result['callees'])}")
        print(f"[+] Callers: {len(result['callers'])}")
        
        # Save
        output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\farobj_vec3_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"[+] Saved to {output_file}")
        
        # Print key findings
        print("\n=== CALLERS (first 15) ===")
        for i, caller in enumerate(result['callers'][:15]):
            print(f"  0x{caller['addr']:X}: {caller['name']}")
        if len(result['callers']) > 15:
            print(f"  ... and {len(result['callers']) - 15} more")
        
        print("\n=== CALLEES ===")
        for callee in result['callees']:
            print(f"  {callee}")
        
        print("\n=== SEGMENTS USED ===")
        for seg, refs in result['segments_used'].items():
            unique = set(r['name'] if r['name'] else hex(r['addr']) for r in refs)
            print(f"  {seg}: {len(unique)} unique references")
        
        print("\n=== FULL DISASSEMBLY ===")
        for insn in result['instructions']:
            callee_note = f" -> {insn['callee']}" if 'callee' in insn else ""
            print(f"  0x{insn['addr']:X}: {insn['disasm']}{callee_note}")
        
    except Exception as e:
        print(f"[-] ERROR: {e}")
        import traceback
        traceback.print_exc()
        idc.qexit(1)

if __name__ == "__main__":
    main()
    idc.qexit(0)
