"""
Analyze the 7 unknown callees from input_poll_handler:
undoc_130C80, undoc_130CE7, undoc_130E48, undoc_131001, undoc_131235, undoc_1312DF
Plus sub_2BEC9
"""
import idaapi
import idc
import idautils
import json

def analyze_function_quick(func_name_or_addr):
    """Quick analysis of a function"""
    try:
        if isinstance(func_name_or_addr, str):
            target_ea = idc.get_name_ea_simple(func_name_or_addr)
            func_name = func_name_or_addr
        else:
            target_ea = func_name_or_addr
            func_name = idc.get_func_name(target_ea) or f"func_0x{target_ea:X}"
        
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
            'caller_count': 0,
            'interrupts': [],
            'port_io': []
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
            
            # Track port I/O
            if mnem in ['in', 'out']:
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
                            result['callees'].add(callee)
            
            result['instructions'].append(insn_data)
        
        result['callees'] = sorted(list(result['callees']))
        return result
    except Exception as e:
        print(f"[-] Error analyzing {func_name_or_addr}: {e}")
        return None

def main():
    try:
        print("[*] Waiting for auto-analysis...")
        idaapi.auto_wait()
        print("[+] Auto-analysis complete\n")
        
        # Target functions
        targets = [
            'undoc_130C80',
            'undoc_130CE7',
            'undoc_130E48',
            'undoc_131001',
            'undoc_131235',
            'undoc_1312DF',
            'sub_2BEC9'
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
                print(f"    Interrupts: {len(result['interrupts'])}")
                print(f"    Port I/O: {len(result['port_io'])}")
                
                if result['callees']:
                    print(f"    Callees: {', '.join(result['callees'][:5])}")
                
                if result['interrupts']:
                    print(f"    INTs: ", end='')
                    for intr in result['interrupts'][:3]:
                        print(f"0x{intr['int']:02X} ", end='')
                    print()
                
                if result['port_io']:
                    print(f"    Port I/O: ", end='')
                    for pio in result['port_io'][:3]:
                        port_str = f"0x{pio['port']:X}" if isinstance(pio['port'], int) else pio['port']
                        print(f"{pio['operation'].upper()}:{port_str} ", end='')
                    print()
                
                # Print full disassembly if small
                if result['size'] <= 150:
                    print(f"    Full disassembly:")
                    for insn in result['instructions']:
                        print(f"      0x{insn['addr']:X}: {insn['disasm']}")
                
                results[func_name] = result
            else:
                print(f"[-] Could not analyze {func_name}")
            print()
        
        # Save results
        output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\input_callees_analysis.json"
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
                'interrupts': data['interrupts'],
                'port_io': data['port_io'],
                'instruction_count': len(data['instructions']),
                'instructions': data['instructions'] if data['size'] <= 150 else data['instructions'][:50]
            }
        
        with open(output_file, 'w') as f:
            json.dump(json_results, f, indent=2)
        print(f"[+] Saved to {output_file}")
        
        print("\n=== SUMMARY ===")
        for name, data in results.items():
            hw_access = []
            if data['interrupts']:
                hw_access.append(f"INT:{','.join(f'0x{i[\"int\"]:02X}' for i in data['interrupts'][:3])}")
            if data['port_io']:
                hw_access.append(f"PORT:{','.join(str(p[\"port\"]) if isinstance(p[\"port\"], int) else p[\"port\"] for p in data['port_io'][:3])}")
            hw_str = ' | '.join(hw_access) if hw_access else 'no direct hardware'
            
            print(f"{name:20s}: {data['size']:4d} bytes, {len(data['instructions']):4d} insns, {data['caller_count']:3d} callers | {hw_str}")
        
    except Exception as e:
        print(f"[-] ERROR: {e}")
        import traceback
        traceback.print_exc()
        idc.qexit(1)

if __name__ == "__main__":
    main()
    idc.qexit(0)
