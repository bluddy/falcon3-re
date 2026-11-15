"""
Analyze undoc_127FA7 - the coordinate-based drawing function
This should reveal actual VGA operations
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
        
        target_ea = idc.get_name_ea_simple('undoc_127FA7')
        
        if target_ea == idc.BADADDR:
            print("[-] Function undoc_127FA7 not found")
            idc.qexit(1)
            return
        
        func = idaapi.get_func(target_ea)
        if not func:
            print(f"[-] No function at 0x{target_ea:X}")
            idc.qexit(1)
            return
        
        func_name = 'undoc_127FA7'
        print(f"[+] Found {func_name} at 0x{target_ea:X}")
        
        result = {
            'name': func_name,
            'start': target_ea,
            'end': func.end_ea,
            'size': func.end_ea - target_ea,
            'instructions': [],
            'callees': [],
            'callers': [],
            'segments_used': {},
            'port_io': [],  # Track IN/OUT instructions
            'interrupts': []  # Track INT instructions
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
            
            # Track interrupts (BIOS/DOS calls)
            if mnem == 'int':
                int_num = idc.get_operand_value(head, 0)
                result['interrupts'].append({
                    'addr': head,
                    'int': int_num,
                    'disasm': disasm
                })
                insn_data['int_num'] = int_num
            
            # Track port I/O
            if mnem in ['in', 'out', 'ins', 'outs']:
                result['port_io'].append({
                    'addr': head,
                    'operation': mnem,
                    'disasm': disasm
                })
            
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
        print(f"[+] Interrupts: {len(result['interrupts'])}")
        print(f"[+] Port I/O: {len(result['port_io'])}")
        
        # Save
        output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\undoc_127FA7_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"[+] Saved to {output_file}")
        
        # Print interesting findings
        if result['interrupts']:
            print("\n=== INTERRUPTS ===")
            for intr in result['interrupts']:
                print(f"  0x{intr['addr']:X}: INT 0x{intr['int']:X}")
        
        if result['port_io']:
            print("\n=== PORT I/O ===")
            for pio in result['port_io']:
                print(f"  0x{pio['addr']:X}: {pio['operation'].upper()} - {pio['disasm']}")
        
        print("\n=== CALLERS ===")
        for caller in result['callers']:
            print(f"  0x{caller['addr']:X}: {caller['name']}")
        
        print("\n=== CALLEES ===")
        for callee in result['callees']:
            print(f"  {callee}")
        
    except Exception as e:
        print(f"[-] ERROR: {e}")
        import traceback
        traceback.print_exc()
        idc.qexit(1)

if __name__ == "__main__":
    main()
    idc.qexit(0)
