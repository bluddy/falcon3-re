#!/usr/bin/env python3
"""
Step 3: Apply PilotRecord structure to squad_campaign_file_loader.

Analyzes the function and exports decompilation with structure comments.
"""

import idc
import idaapi
import idautils
import json

def get_function_decompilation(func_addr):
    """Get pseudocode decompilation."""
    try:
        cfunc = idaapi.decompile(func_addr)
        return str(cfunc) if cfunc else None
    except:
        return None

def main():
    idaapi.auto_wait()
    
    print("[*] Step 3: Applying PilotRecord structure")
    
    # Find function
    func_addr = idc.get_name_ea_simple("squad_campaign_file_loader")
    if func_addr == idc.BADADDR:
        func_addr = 0x6A651
    
    func = idaapi.get_func(func_addr)
    if not func:
        print("[!] Function not found")
        idc.qexit(1)
    
    print(f"[+] Found function at 0x{func_addr:X}, size={func.end_ea - func.start_ea} bytes")
    
    # Check PilotRecord exists
    sid = idc.get_struc_id("PilotRecord")
    if sid == idc.BADADDR:
        print("[!] PilotRecord not found")
        idc.qexit(1)
    
    print(f"[+] PilotRecord found, size={idc.get_struc_size(sid)} bytes")
    
    # Get decompilation
    print("[*] Getting decompilation...")
    decompilation = get_function_decompilation(func_addr)
    
    if decompilation:
        print(f"[+] Got decompilation ({len(decompilation)} chars)")
        
        # Save it
        with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\squad_loader_decompile.c', 'w') as f:
            f.write(decompilation)
        
        # Add comment
        func_cmt = """Squad/Campaign file loader
        
.SQU file structure (2703 bytes):
  0x00: SquadronHeader (60 bytes)
  0x3C: PilotRecord[30] (1980 bytes)
  0x7F8: ExtendedPilotRecord[10] (660 bytes)

PilotRecord (66 bytes):
  +0x00: status_flags[2]
  +0x02: rank
  +0x03: callsign[15]
  +0x13: nickname[15]
  +0x22: id_code[4]
  +0x26: skills (dogfighting, bombing, flying, fatigue)
  +0x2A: mission_data[28]
"""
        
        idc.set_func_cmt(func_addr, func_cmt, 1)
        print("[+] Added function comment")
        
        result = {
            'success': True,
            'function_addr': hex(func_addr),
            'decompilation_saved': 'analysis/squad_loader_decompile.c',
            'pilot_record_size': idc.get_struc_size(sid)
        }
    else:
        print("[!] Decompilation failed")
        result = {'success': False, 'error': 'Decompilation failed'}
    
    with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\apply_pilot_structure_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print("[+] Done!")
    idc.qexit(0)

if __name__ == "__main__":
    main()
