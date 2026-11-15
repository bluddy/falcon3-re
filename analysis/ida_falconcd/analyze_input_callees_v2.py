"""
Analyze the 7 unknown callees from input_poll_handler
More robust version with better error handling
"""
import idaapi
import idc
import idautils
import json

def main():
    try:
        print("[*] Waiting for auto-analysis...")
        idaapi.auto_wait()
        print("[+] Auto-analysis complete\n")
        
        # Target functions with their hex addresses as backup
        targets = [
            ('undoc_130C80', 0x130C80),
            ('undoc_130CE7', 0x130CE7),
            ('undoc_130E48', 0x130E48),
            ('undoc_131001', 0x131001),
            ('undoc_131235', 0x131235),
            ('undoc_1312DF', 0x1312DF),
            ('sub_2BEC9', 0x2BEC9)
        ]
        
        results = {}
        
        for func_name, addr_hint in targets:
            print(f"[*] Analyzing {func_name} (0x{addr_hint:X})...")
            
            # Try by name first, then by address
            target_ea = idc.get_name_ea_simple(func_name)
            if target_ea == idc.BADADDR:
                target_ea = addr_hint
                print(f"    Name not found, using address 0x{addr_hint:X}")
            
            func = idaapi.get_func(target_ea)
            if not func:
                print(f"[-] No function at 0x{target_ea:X}")
                continue
            
            actual_name = idc.get_func_name(target_ea)
            print(f"[+] Found: {actual_name} at 0x{target_ea:X}")
            
            result = {
                'name': actual_name,
                'start': target_ea,
                'end': func.end_ea,
                'size': func.end_ea - target_ea,
                'instructions': [],
                'callees': [],
                'callers': [],
                'interrupts': [],
                'port_io': []
            }
            
            # Count callers
            for xref in idautils.XrefsTo(target_ea):
                caller_name = idc.get_func_name(xref.frm)
                if caller_name:
                    result['callers'].append(caller_name)
            
            # Analyze instructions
            callees_set = set()
            for head in idautils.Heads(func.start_ea, func.end_ea):
                if not idc.is_code(idc.get_full_flags(head)):
                    continue
                
                mnem = idc.print_insn_mnem(head)
                disasm = idc.GetDisasm(head)
                
                insn = {'addr': head, 'mnem': mnem, 'disasm': disasm}
                
                # Track interrupts
                if mnem == 'int':
                    int_num = idc.get_operand_value(head, 0)
                    result['interrupts'].append({
                        'addr': head,
                        'int': int_num,
                        'disasm': disasm
                    })
                
                # Track port I/O
                if mnem in ['in', 'out']:
                    port_str = 'DX' if 'dx' in disasm.lower() else 'IMM'
                    result['port_io'].append({
                        'addr': head,
                        'op': mnem,
                        'port': port_str,
                        'disasm': disasm
                    })
                
                # Track calls
                if mnem in ['call', 'jmp']:
                    for xref in idautils.XrefsFrom(head):
                        if xref.type in [idaapi.fl_CF, idaapi.fl_CN]:
                            callee = idc.get_func_name(xref.to)
                            if callee:
                                callees_set.add(callee)
                
                result['instructions'].append(insn)
            
            result['callees'] = sorted(list(callees_set))
            
            print(f"    Size: {result['size']} bytes")
            print(f"    Instructions: {len(result['instructions'])}")
            print(f"    Callees: {len(result['callees'])}")
            print(f"    Callers: {len(result['callers'])}")
            print(f"    Interrupts: {len(result['interrupts'])}")
            print(f"    Port I/O: {len(result['port_io'])}")
            
            if result['interrupts']:
                ints = ', '.join(f"0x{i['int']:02X}" for i in result['interrupts'][:3])
                print(f"    INT: {ints}")
            
            if result['port_io']:
                ports = ', '.join(f"{p['op'].upper()}" for p in result['port_io'][:3])
                print(f"    I/O: {ports}")
            
            if result['callees']:
                callees = ', '.join(result['callees'][:3])
                print(f"    Calls: {callees}")
                if len(result['callees']) > 3:
                    print(f"           ... and {len(result['callees']) - 3} more")
            
            # Print full disasm if small enough
            if result['size'] <= 200:
                print(f"    Full disassembly:")
                for insn in result['instructions']:
                    print(f"      0x{insn['addr']:X}: {insn['disasm']}")
            
            results[actual_name] = result
            print()
        
        # Save results
        output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\input_callees_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"[+] Saved to {output_file}")
        
        # Summary table
        print("\n=== SUMMARY TABLE ===")
        print(f"{'Function':<25} {'Size':>6} {'Insns':>6} {'Calls':>6} {'Callers':>6} {'Hardware':<20}")
        print("-" * 80)
        for name, data in results.items():
            hw = []
            if data['interrupts']:
                hw.append(f"INT:{','.join(f'0x{i['int']:02X}' for i in data['interrupts'][:2])}")
            if data['port_io']:
                hw.append(f"I/O:{len(data['port_io'])}")
            hw_str = ' '.join(hw) if hw else '-'
            
            print(f"{name:<25} {data['size']:>6} {len(data['instructions']):>6} "
                  f"{len(data['callees']):>6} {len(data['callers']):>6} {hw_str:<20}")
        
        print(f"\n[+] Analyzed {len(results)} functions")
        
    except Exception as e:
        print(f"[-] ERROR: {e}")
        import traceback
        traceback.print_exc()
        idc.qexit(1)

if __name__ == "__main__":
    main()
    idc.qexit(0)
