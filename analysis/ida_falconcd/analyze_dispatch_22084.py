"""
Follow the chain: analyze dispatch_22084_near
This should be the actual dispatcher or VGA function
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
        
        target_ea = idc.get_name_ea_simple('dispatch_22084_near')
        
        if target_ea == idc.BADADDR:
            print("[-] Function dispatch_22084_near not found")
            idc.qexit(1)
            return
        
        func = idaapi.get_func(target_ea)
        if not func:
            print(f"[-] No function at 0x{target_ea:X}")
            # Try just reading some bytes
            print("[*] Not a function, might be data or far jump")
            for i in range(20):
                byte_val = idc.get_wide_byte(target_ea + i)
                print(f"  0x{target_ea+i:X}: 0x{byte_val:02X}")
            idc.qexit(0)
            return
        
        func_name = 'dispatch_22084_near'
        print(f"[+] Found {func_name} at 0x{target_ea:X}")
        
        result = {
            'name': func_name,
            'start': target_ea,
            'end': func.end_ea,
            'size': func.end_ea - target_ea,
            'instructions': [],
            'callees': [],
            'far_jumps': [],
            'segments_used': {}
        }
        
        # Analyze instructions (limit to first 100 for safety)
        callees_set = set()
        insn_count = 0
        for head in idautils.Heads(func.start_ea, func.end_ea):
            if insn_count >= 100:
                break
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
            
            # Track far jumps
            if mnem == 'jmp' and 'far ptr' in disasm:
                result['far_jumps'].append({
                    'addr': head,
                    'disasm': disasm
                })
                insn_data['far_jump'] = True
            
            # Track calls
            if mnem in ['call', 'jmp']:
                for xref in idautils.XrefsFrom(head):
                    if xref.type in [idaapi.fl_CF, idaapi.fl_CN, idaapi.fl_JF, idaapi.fl_JN]:
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
        print(f"[+] Far jumps: {len(result['far_jumps'])}")
        
        # Save
        output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\dispatch_22084_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"[+] Saved to {output_file}")
        
        # Print findings
        if result['far_jumps']:
            print("\n=== FAR JUMPS (Overlay Loading) ===")
            for jmp in result['far_jumps']:
                print(f"  0x{jmp['addr']:X}: {jmp['disasm']}")
        
        print("\n=== CALLEES ===")
        for callee in result['callees'][:10]:
            print(f"  {callee}")
        if len(result['callees']) > 10:
            print(f"  ... and {len(result['callees']) - 10} more")
        
        print("\n=== FIRST 20 INSTRUCTIONS ===")
        for insn in result['instructions'][:20]:
            print(f"  0x{insn['addr']:X}: {insn['disasm']}")
        
    except Exception as e:
        print(f"[-] ERROR: {e}")
        import traceback
        traceback.print_exc()
        idc.qexit(1)

if __name__ == "__main__":
    main()
    idc.qexit(0)
