"""
Deep-dive analysis of input_poll_handler
This is the main input processing function (3814 bytes, 56 callers)
Handles keyboard, mouse, and joystick input
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
        
        target_ea = idc.get_name_ea_simple('input_poll_handler')
        
        if target_ea == idc.BADADDR:
            print("[-] input_poll_handler not found")
            idc.qexit(1)
            return
        
        func = idaapi.get_func(target_ea)
        if not func:
            print(f"[-] No function at 0x{target_ea:X}")
            idc.qexit(1)
            return
        
        print(f"[+] Found input_poll_handler at 0x{target_ea:X}")
        print(f"[+] Size: {func.end_ea - target_ea} bytes")
        
        result = {
            'name': 'input_poll_handler',
            'start': target_ea,
            'end': func.end_ea,
            'size': func.end_ea - target_ea,
            'instructions': [],
            'callees': [],
            'callers': [],
            'segments_used': {},
            'interrupts': [],
            'port_io': [],
            'basic_blocks': []
        }
        
        # Get callers
        for xref in idautils.XrefsTo(target_ea):
            caller_name = idc.get_func_name(xref.frm)
            if caller_name:
                result['callers'].append({
                    'addr': xref.frm,
                    'name': caller_name
                })
        
        # Get basic blocks
        try:
            flowchart = idaapi.qflow_chart_t("", func, idaapi.FC_PREDS)
            for bb_idx in range(flowchart.size()):
                bb = flowchart[bb_idx]
                result['basic_blocks'].append({
                    'start': bb.start_ea,
                    'end': bb.end_ea,
                    'size': bb.end_ea - bb.start_ea
                })
        except Exception as e:
            print(f"[!] Could not analyze basic blocks: {e}")
        
        # Analyze instructions
        callees_set = set()
        insn_counts = {}
        
        for head in idautils.Heads(func.start_ea, func.end_ea):
            if not idc.is_code(idc.get_full_flags(head)):
                continue
            
            mnem = idc.print_insn_mnem(head)
            disasm = idc.GetDisasm(head)
            
            # Count instruction types
            insn_counts[mnem] = insn_counts.get(mnem, 0) + 1
            
            insn_data = {
                'addr': head,
                'mnem': mnem,
                'disasm': disasm
            }
            
            # Track interrupts
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
                try:
                    port_val = idc.get_operand_value(head, 1) if 'dx' not in disasm.lower() else 'DX'
                except:
                    port_val = 'unknown'
                result['port_io'].append({
                    'addr': head,
                    'operation': mnem,
                    'port': port_val,
                    'disasm': disasm
                })
            
            # Track calls
            if mnem in ['call', 'jmp']:
                for xref in idautils.XrefsFrom(head):
                    if xref.type in [idaapi.fl_CF, idaapi.fl_CN]:
                        callee = idc.get_func_name(xref.to)
                        if callee:
                            callees_set.add(callee)
                            insn_data['callee'] = callee
            
            # Track data refs to input flags and key segments
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
        result['instruction_counts'] = insn_counts
        
        print(f"[+] Instructions: {len(result['instructions'])}")
        print(f"[+] Basic blocks: {len(result['basic_blocks'])}")
        print(f"[+] Callees: {len(result['callees'])}")
        print(f"[+] Callers: {len(result['callers'])}")
        print(f"[+] Interrupts: {len(result['interrupts'])}")
        print(f"[+] Port I/O: {len(result['port_io'])}")
        
        # Save full analysis
        output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\input_poll_handler_deepdive.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"[+] Saved to {output_file}")
        
        # Print summary
        print("\n=== INSTRUCTION COUNTS (Top 15) ===")
        sorted_insns = sorted(insn_counts.items(), key=lambda x: x[1], reverse=True)
        for mnem, count in sorted_insns[:15]:
            print(f"  {mnem:8s}: {count:4d}")
        
        print("\n=== CALLEES ===")
        for callee in result['callees']:
            print(f"  {callee}")
        
        print("\n=== INTERRUPTS ===")
        for intr in result['interrupts']:
            print(f"  0x{intr['addr']:X}: INT 0x{intr['int']:02X} - {intr['disasm']}")
        
        print("\n=== PORT I/O ===")
        for pio in result['port_io']:
            port_str = f"0x{pio['port']:X}" if isinstance(pio['port'], int) else pio['port']
            print(f"  0x{pio['addr']:X}: {pio['operation'].upper():4s} port {port_str}")
        
        print("\n=== SEGMENTS USED ===")
        for seg_name, refs in sorted(result['segments_used'].items()):
            unique_refs = set(r['name'] if r['name'] else hex(r['addr']) for r in refs)
            print(f"  {seg_name}: {len(refs)} refs, {len(unique_refs)} unique")
            # Show key data items
            named_refs = [r for r in unique_refs if not r.startswith('0x')]
            if named_refs:
                for ref in sorted(named_refs)[:10]:
                    print(f"    - {ref}")
                if len(named_refs) > 10:
                    print(f"    ... and {len(named_refs) - 10} more")
        
        print("\n=== CALLERS (first 20) ===")
        for i, caller in enumerate(result['callers'][:20]):
            print(f"  0x{caller['addr']:X}: {caller['name']}")
        if len(result['callers']) > 20:
            print(f"  ... and {len(result['callers']) - 20} more")
        
        print("\n=== BASIC BLOCK SUMMARY ===")
        total_bb_size = sum(bb['size'] for bb in result['basic_blocks'])
        avg_bb_size = total_bb_size / len(result['basic_blocks']) if result['basic_blocks'] else 0
        print(f"  Total blocks: {len(result['basic_blocks'])}")
        print(f"  Average block size: {avg_bb_size:.1f} bytes")
        print(f"  Largest block: {max((bb['size'] for bb in result['basic_blocks']), default=0)} bytes")
        print(f"  Smallest block: {min((bb['size'] for bb in result['basic_blocks']), default=0)} bytes")
        
    except Exception as e:
        print(f"[-] ERROR: {e}")
        import traceback
        traceback.print_exc()
        idc.qexit(1)

if __name__ == "__main__":
    main()
    idc.qexit(0)
