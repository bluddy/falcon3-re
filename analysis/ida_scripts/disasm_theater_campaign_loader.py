#!/usr/bin/env python3
"""
Disassemble theater_campaign_file_loader function to understand campaign file format.
"""

import idc
import idaapi
import idautils
import json

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("DISASSEMBLE THEATER CAMPAIGN FILE LOADER")
    print("="*80)
    print()
    
    # Find the function
    func_name = "theater_campaign_file_loader"
    func_addr = idc.get_name_ea_simple(func_name)
    
    if func_addr == idc.BADADDR:
        print(f"[!] Function {func_name} not found")
        idc.qexit(1)
    
    func = idaapi.get_func(func_addr)
    if not func:
        print(f"[!] No function at {func_addr:#x}")
        idc.qexit(1)
    
    print(f"[+] Function: {func_name}")
    print(f"    Address: {func.start_ea:#x} - {func.end_ea:#x}")
    print(f"    Size: {func.end_ea - func.start_ea} bytes")
    print()
    
    # Count instructions
    insn_count = 0
    ea = func.start_ea
    while ea < func.end_ea:
        insn_count += 1
        ea = idc.next_head(ea, func.end_ea)
    
    print(f"    Instructions: {insn_count}")
    print()
    
    # Save full disassembly
    disasm_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\theater_campaign_loader_disasm.txt'
    with open(disasm_path, 'w') as f:
        f.write(f"DISASSEMBLY: {func_name}\n")
        f.write(f"Address: {func.start_ea:#x} - {func.end_ea:#x}\n")
        f.write(f"Size: {func.end_ea - func.start_ea} bytes\n")
        f.write(f"Instructions: {insn_count}\n")
        f.write("="*80 + "\n\n")
        
        ea = func.start_ea
        while ea < func.end_ea:
            disasm = idc.generate_disasm_line(ea, 0)
            f.write(f"{ea:#x}  {disasm}\n")
            ea = idc.next_head(ea, func.end_ea)
    
    print(f"[+] Full disassembly saved to {disasm_path}")
    
    # Also disassemble squad_campaign_file_loader
    print()
    print("[*] Also extracting squad_campaign_file_loader...")
    
    squad_func_name = "squad_campaign_file_loader"
    squad_func_addr = idc.get_name_ea_simple(squad_func_name)
    
    if squad_func_addr != idc.BADADDR:
        squad_func = idaapi.get_func(squad_func_addr)
        if squad_func:
            print(f"[+] Function: {squad_func_name}")
            print(f"    Address: {squad_func.start_ea:#x} - {squad_func.end_ea:#x}")
            print(f"    Size: {squad_func.end_ea - squad_func.start_ea} bytes")
            
            squad_insn_count = 0
            ea = squad_func.start_ea
            while ea < squad_func.end_ea:
                squad_insn_count += 1
                ea = idc.next_head(ea, squad_func.end_ea)
            
            print(f"    Instructions: {squad_insn_count}")
            print()
            
            squad_disasm_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\squad_campaign_loader_disasm.txt'
            with open(squad_disasm_path, 'w') as f:
                f.write(f"DISASSEMBLY: {squad_func_name}\n")
                f.write(f"Address: {squad_func.start_ea:#x} - {squad_func.end_ea:#x}\n")
                f.write(f"Size: {squad_func.end_ea - squad_func.start_ea} bytes\n")
                f.write(f"Instructions: {squad_insn_count}\n")
                f.write("="*80 + "\n\n")
                
                ea = squad_func.start_ea
                while ea < squad_func.end_ea:
                    disasm = idc.generate_disasm_line(ea, 0)
                    f.write(f"{ea:#x}  {disasm}\n")
                    ea = idc.next_head(ea, squad_func.end_ea)
            
            print(f"[+] Squad loader disassembly saved to {squad_disasm_path}")
    
    # Save metadata
    result = {
        'theater_campaign_loader': {
            'name': func_name,
            'address': hex(func.start_ea),
            'size': func.end_ea - func.start_ea,
            'instructions': insn_count
        }
    }
    
    if squad_func_addr != idc.BADADDR and squad_func:
        result['squad_campaign_loader'] = {
            'name': squad_func_name,
            'address': hex(squad_func.start_ea),
            'size': squad_func.end_ea - squad_func.start_ea,
            'instructions': squad_insn_count
        }
    
    output_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\campaign_loaders_info.json'
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"[+] Metadata saved to {output_path}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
