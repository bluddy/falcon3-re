#!/usr/bin/env python3
"""
Export squad_campaign_file_loader disassembly and analyze structure.
"""

import idc
import idaapi
import idautils
import json

def main():
    idaapi.auto_wait()
    
    print("[*] Exporting squad_campaign_file_loader")
    
    func_addr = 0x6A651
    func = idaapi.get_func(func_addr)
    
    if not func:
        print("[!] Function not found")
        idc.qexit(1)
    
    print(f"[+] Function: 0x{func.start_ea:X} - 0x{func.end_ea:X}")
    print(f"[+] Size: {func.end_ea - func.start_ea} bytes")
    
    # Export disassembly
    disasm_lines = []
    ea = func.start_ea
    
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        disasm_lines.append(f"{ea:08X}  {disasm}")
        ea = idc.next_head(ea, func.end_ea)
    
    print(f"[+] Exported {len(disasm_lines)} instructions")
    
    # Save disassembly
    with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\squad_loader_disassembly.asm', 'w') as f:
        f.write(f"; squad_campaign_file_loader\n")
        f.write(f"; Address: 0x{func.start_ea:X} - 0x{func.end_ea:X}\n")
        f.write(f"; Size: {func.end_ea - func.start_ea} bytes\n")
        f.write("\n")
        for line in disasm_lines:
            f.write(line + "\n")
    
    print("[+] Saved to squad_loader_disassembly.asm")
    
    # Look for pilot-related constants
    print("\n[*] Searching for pilot-related constants...")
    
    pilot_refs = []
    for line in disasm_lines:
        # Look for 0x3C (60, header size), 0x42 (66, pilot size)
        if any(x in line for x in ['3Ch', '42h', '60d', '66d', '1980', '7BCh']):
            pilot_refs.append(line)
    
    print(f"[+] Found {len(pilot_refs)} pilot-related instructions:")
    for ref in pilot_refs[:20]:
        print(f"    {ref}")
    
    # Check for string references
    print("\n[*] Checking for string references...")
    strings_found = []
    
    ea = func.start_ea
    while ea < func.end_ea:
        # Check for data xrefs from this instruction
        for xref in idautils.XrefsFrom(ea, 0):
            # Check if xref points to a string
            str_type = idc.get_str_type(xref.to)
            if str_type is not None:
                string_val = idc.get_strlit_contents(xref.to)
                if string_val:
                    strings_found.append({
                        'addr': hex(ea),
                        'string': string_val.decode('ascii', errors='ignore')
                    })
        
        ea = idc.next_head(ea, func.end_ea)
    
    print(f"[+] Found {len(strings_found)} string references")
    for s in strings_found[:10]:
        print(f"    {s['addr']}: \"{s['string']}\"")
    
    # Save results
    result = {
        'function_addr': hex(func.start_ea),
        'function_size': func.end_ea - func.start_ea,
        'instruction_count': len(disasm_lines),
        'pilot_related_instructions': len(pilot_refs),
        'string_references': len(strings_found),
        'disassembly_file': 'analysis/squad_loader_disassembly.asm'
    }
    
    with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\squad_loader_analysis.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print("\n[+] Analysis complete!")
    idc.qexit(0)

if __name__ == "__main__":
    main()
