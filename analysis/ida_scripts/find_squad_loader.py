#!/usr/bin/env python3
"""
Find the squad/campaign file loader function.
"""

import idc
import idaapi
import idautils
import json

def main():
    idaapi.auto_wait()
    
    print("[*] Searching for squad_campaign_file_loader...")
    
    # Try by name
    func_addr = idc.get_name_ea_simple("squad_campaign_file_loader")
    if func_addr != idc.BADADDR:
        print(f"[+] Found by name: 0x{func_addr:X}")
    else:
        print("[*] Not found by name, trying direct address...")
        func_addr = 0x6A651
    
    # Check if it's a valid function
    func = idaapi.get_func(func_addr)
    if not func:
        print(f"[!] No function at 0x{func_addr:X}")
        
        # Try to create function
        print("[*] Attempting to create function at 0x{func_addr:X}...")
        if idc.create_insn(func_addr):
            if idc.add_func(func_addr):
                print("[+] Function created!")
                func = idaapi.get_func(func_addr)
            else:
                print("[!] Failed to create function")
        else:
            print("[!] No valid instruction at address")
    
    if func:
        print(f"[+] Function found!")
        print(f"    Start: 0x{func.start_ea:X}")
        print(f"    End: 0x{func.end_ea:X}")
        print(f"    Size: {func.end_ea - func.start_ea} bytes")
        
        # Get current name
        current_name = idc.get_func_name(func_addr)
        print(f"    Current name: {current_name}")
        
        # Try to rename if not already named
        if current_name.startswith("sub_"):
            print(f"[*] Renaming to squad_campaign_file_loader...")
            if idc.set_name(func_addr, "squad_campaign_file_loader", idc.SN_NOWARN):
                print("[+] Renamed successfully")
            else:
                print("[!] Rename failed")
        
        result = {
            'found': True,
            'addr': hex(func_addr),
            'start': hex(func.start_ea),
            'end': hex(func.end_ea),
            'size': func.end_ea - func.start_ea,
            'name': idc.get_func_name(func_addr)
        }
    else:
        result = {
            'found': False,
            'addr': hex(func_addr)
        }
    
    with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\find_squad_loader_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print("[+] Results saved")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
