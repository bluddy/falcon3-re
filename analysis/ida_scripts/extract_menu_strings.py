"""
Extract string references and file I/O operations from FALCONCD.EXE IDA database.
Specifically looking for:
1. Strings like "ARMS", "MENU", ".IDX", ".DAT"
2. Functions that call DOS INT 21h (file operations)
3. Complete disassembly of menu-related functions
"""

import idc
import idaapi
import idautils
import json

def find_string_references(search_strings):
    """Find all references to specific strings in the binary."""
    results = {}
    
    # Get all strings in the database
    strings = idautils.Strings()
    
    for s in strings:
        str_val = str(s)
        str_addr = s.ea
        
        for search in search_strings:
            if search.upper() in str_val.upper():
                # Find all code references to this string
                refs = []
                for xref in idautils.XrefsTo(str_addr):
                    refs.append({
                        'from': hex(xref.frm),
                        'type': xref.type,
                        'func': idc.get_func_name(xref.frm)
                    })
                
                if refs:
                    results[hex(str_addr)] = {
                        'string': str_val,
                        'address': hex(str_addr),
                        'refs': refs
                    }
    
    return results

def find_dos_int21_calls():
    """Find all INT 21h calls (DOS file operations)."""
    results = []
    
    # Search for all INT 21h instructions
    ea = idc.get_inf_attr(idc.INF_MIN_EA)
    end = idc.get_inf_attr(idc.INF_MAX_EA)
    
    while ea < end:
        # Check if this is an INT instruction
        mnem = idc.print_insn_mnem(ea)
        if mnem == "int":
            # Check if it's INT 21h
            op = idc.get_operand_value(ea, 0)
            if op == 0x21:
                func_name = idc.get_func_name(ea)
                func_start = idc.get_func_attr(ea, idc.FUNCATTR_START)
                
                # Try to find the AH value (DOS function number)
                # Look backwards for MOV AH, XX
                check_ea = ea - 20
                ah_value = None
                while check_ea < ea:
                    if idc.print_insn_mnem(check_ea) == "mov":
                        op0 = idc.print_operand(check_ea, 0)
                        if op0 == "ah":
                            ah_value = hex(idc.get_operand_value(check_ea, 1))
                            break
                    check_ea = idc.next_head(check_ea)
                
                results.append({
                    'address': hex(ea),
                    'function': func_name,
                    'func_addr': hex(func_start) if func_start != idc.BADADDR else None,
                    'ah_value': ah_value,
                    'context': idc.GetDisasm(ea)
                })
        
        ea = idc.next_head(ea)
    
    return results

def get_function_disasm(func_addr):
    """Get complete disassembly of a function."""
    if isinstance(func_addr, str):
        func_addr = int(func_addr, 16)
    
    func_start = idc.get_func_attr(func_addr, idc.FUNCATTR_START)
    func_end = idc.get_func_attr(func_addr, idc.FUNCATTR_END)
    
    if func_start == idc.BADADDR:
        return None
    
    disasm = []
    ea = func_start
    while ea < func_end:
        disasm.append({
            'addr': hex(ea),
            'disasm': idc.GetDisasm(ea),
            'bytes': idc.get_bytes(ea, idc.get_item_size(ea)).hex()
        })
        ea = idc.next_head(ea)
    
    return {
        'name': idc.get_func_name(func_start),
        'start': hex(func_start),
        'end': hex(func_end),
        'size': func_end - func_start,
        'disasm': disasm
    }

def main():
    """Main extraction function."""
    print("[*] Extracting data from IDA database...")
    
    # Wait for auto-analysis to complete
    idaapi.auto_wait()
    
    results = {}
    
    # 1. Find string references
    print("[*] Searching for string references...")
    search_strings = ["ARMS", "MENU", ".IDX", ".DAT", "COMM", "SYS", "DIFF", "SQUAD"]
    results['strings'] = find_string_references(search_strings)
    print(f"    Found {len(results['strings'])} relevant strings")
    
    # 2. Find DOS INT 21h calls
    print("[*] Searching for INT 21h calls...")
    results['int21_calls'] = find_dos_int21_calls()
    print(f"    Found {len(results['int21_calls'])} INT 21h calls")
    
    # 3. Get specific function disassemblies
    print("[*] Extracting function disassemblies...")
    funcs_to_extract = {
        'sub_683C5': 0x683C5,  # Menu controller
        'sub_66E62': 0x66E62,  # UI menu panel init
        'sub_6798C': 0x6798C,  # UI slot record fill
        'sub_6A5BD': 0x6A5BD,  # UI menu page setup
    }
    
    results['functions'] = {}
    for func_name, func_addr in funcs_to_extract.items():
        print(f"    Extracting {func_name}...")
        results['functions'][func_name] = get_function_disasm(func_addr)
    
    # 4. Save results
    output_file = idc.get_idb_path().replace('.i64', '_extracted.json')
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"[+] Results saved to: {output_file}")
    print("[+] Extraction complete!")
    
    # Also create a summary report
    summary_file = output_file.replace('.json', '_summary.txt')
    with open(summary_file, 'w') as f:
        f.write("FALCONCD.EXE String and File I/O Analysis\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"String References Found: {len(results['strings'])}\n")
        for addr, data in results['strings'].items():
            f.write(f"\n{addr}: \"{data['string']}\"\n")
            for ref in data['refs']:
                f.write(f"  Referenced by: {ref['func']} at {ref['from']}\n")
        
        f.write("\n" + "=" * 60 + "\n\n")
        f.write(f"DOS INT 21h Calls Found: {len(results['int21_calls'])}\n")
        
        # Group by DOS function
        by_function = {}
        for call in results['int21_calls']:
            ah = call['ah_value'] or 'unknown'
            if ah not in by_function:
                by_function[ah] = []
            by_function[ah].append(call)
        
        for ah, calls in sorted(by_function.items()):
            dos_func = {
                '0x3d': 'Open File',
                '0x3e': 'Close File',
                '0x3f': 'Read File',
                '0x40': 'Write File',
                '0x42': 'Seek File',
            }.get(ah, 'Unknown')
            
            f.write(f"\nAH={ah} ({dos_func}): {len(calls)} calls\n")
            for call in calls[:10]:  # Limit to first 10
                f.write(f"  {call['address']}: {call['function']} - {call['context']}\n")
    
    print(f"[+] Summary saved to: {summary_file}")

if __name__ == "__main__":
    main()
