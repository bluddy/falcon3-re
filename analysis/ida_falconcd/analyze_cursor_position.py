"""
Analyze menu_cursor_position_set - cursor movement function
Called 6 times by ui_loadout_menu_enter
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
        
        target_ea = idc.get_name_ea_simple('menu_cursor_position_set')
        
        if target_ea == idc.BADADDR:
            print("[-] menu_cursor_position_set not found")
            idc.qexit(1)
            return
        
        func = idaapi.get_func(target_ea)
        if not func:
            print(f"[-] No function at 0x{target_ea:X}")
            idc.qexit(1)
            return
        
        print(f"[+] Found menu_cursor_position_set at 0x{target_ea:X}")
        
        result = {
            'name': 'menu_cursor_position_set',
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
        output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\menu_cursor_position_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"[+] Saved to {output_file}")
        
        # Print summary
        print("\n=== CALLERS ===")
        for caller in result['callers']:
            print(f"  0x{caller['addr']:X}: {caller['name']}")
        
        print("\n=== CALLEES ===")
        for callee in result['callees']:
            print(f"  {callee}")
        
        print("\n=== SEGMENTS ===")
        for seg, refs in result['segments_used'].items():
            unique_refs = set(r['name'] if r['name'] else hex(r['addr']) for r in refs)
            print(f"  {seg}: {len(unique_refs)} unique references")
        
        print("\n=== ALL INSTRUCTIONS ===")
        for insn in result['instructions']:
            print(f"  0x{insn['addr']:X}: {insn['disasm']}")
        
    except Exception as e:
        print(f"[-] ERROR: {e}")
        import traceback
        traceback.print_exc()
        idc.qexit(1)

if __name__ == "__main__":
    main()
    idc.qexit(0)
