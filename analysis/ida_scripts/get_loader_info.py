#!/usr/bin/env python3
"""
Get basic info about loader functions.
"""

import idc
import idaapi
import idautils

def main():
    idaapi.auto_wait()
    
    output_lines = []
    output_lines.append("="*80)
    output_lines.append("GET LOADER FUNCTION INFO")
    output_lines.append("="*80)
    output_lines.append("")
    
    # Check multiple loaders
    func_names = [
        "squadron_mission_file_loader",
        "squad_campaign_file_loader", 
        "theater_campaign_file_loader"
    ]
    
    for func_name in func_names:
        func_addr = idc.get_name_ea_simple(func_name)
        
        output_lines.append(f"[*] Looking for: {func_name}")
        output_lines.append(f"    Address: {func_addr:#x}")
        
        if func_addr == idc.BADADDR or func_addr == 0xFFFFFFFF:
            output_lines.append(f"    Status: NOT FOUND")
        else:
            output_lines.append(f"    Status: FOUND")
            func = idaapi.get_func(func_addr)
            if func:
                output_lines.append(f"    Function start: {func.start_ea:#x}")
                output_lines.append(f"    Function end: {func.end_ea:#x}")
                output_lines.append(f"    Size: {func.end_ea - func.start_ea} bytes")
            else:
                output_lines.append(f"    ERROR: get_func returned None")
        output_lines.append("")
    
    # Write to file
    output_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\loader_info_check.txt'
    with open(output_path, 'w') as f:
        f.write('\n'.join(output_lines))
    
    output_lines.append(f"[+] Output saved to {output_path}")
    print('\n'.join(output_lines))
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
