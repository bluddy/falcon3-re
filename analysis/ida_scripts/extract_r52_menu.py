#!/usr/bin/env python3
"""
Extract R52 Flight Briefing Menu overlay.

R52 is the flight briefing menu that shows mission details before flight.
Find the overlay loader, extract the function, and analyze structure.
"""

import idc
import idaapi
import idautils
import json

def find_overlay_references(overlay_name):
    """Find all references to an overlay name."""
    refs = []
    
    # Search for the string
    for seg_ea in idautils.Segments():
        ea = seg_ea
        seg_end = idc.get_segm_end(seg_ea)
        
        while ea < seg_end:
            # Check if this is a string
            str_type = idc.get_str_type(ea)
            if str_type is not None:
                string_val = idc.get_strlit_contents(ea)
                if string_val and overlay_name.encode() in string_val:
                    # Found the string, get xrefs to it
                    for xref in idautils.XrefsTo(ea):
                        refs.append({
                            'string_addr': hex(ea),
                            'string': string_val.decode('ascii', errors='ignore'),
                            'xref_from': hex(xref.frm),
                            'xref_func': idc.get_func_name(xref.frm)
                        })
            
            ea = idc.next_head(ea, seg_end)
    
    return refs

def find_segment_by_name(seg_name):
    """Find a segment by name or partial name."""
    for seg_ea in idautils.Segments():
        name = idc.get_segm_name(seg_ea)
        if seg_name in name:
            return {
                'name': name,
                'start': hex(seg_ea),
                'end': hex(idc.get_segm_end(seg_ea)),
                'size': idc.get_segm_end(seg_ea) - seg_ea
            }
    return None

def extract_function_info(func_addr):
    """Extract detailed information about a function."""
    func = idaapi.get_func(func_addr)
    if not func:
        return None
    
    # Get function name
    func_name = idc.get_func_name(func_addr)
    
    # Count instructions
    insn_count = 0
    ea = func.start_ea
    while ea < func.end_ea:
        insn_count += 1
        ea = idc.next_head(ea, func.end_ea)
    
    # Find calls within function
    calls = []
    ea = func.start_ea
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        if mnem == 'call':
            target = idc.get_operand_value(ea, 0)
            target_name = idc.get_func_name(target) if target != idc.BADADDR else None
            calls.append({
                'addr': hex(ea),
                'target': hex(target) if target != idc.BADADDR else None,
                'target_name': target_name
            })
        ea = idc.next_head(ea, func.end_ea)
    
    return {
        'name': func_name,
        'start': hex(func.start_ea),
        'end': hex(func.end_ea),
        'size': func.end_ea - func.start_ea,
        'instruction_count': insn_count,
        'calls': calls
    }

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("R52 FLIGHT BRIEFING MENU EXTRACTION")
    print("="*80)
    print()
    
    # Look for R52 segment
    print("[*] Searching for R52 segment...")
    r52_seg = find_segment_by_name("R52")
    
    if r52_seg:
        print(f"[+] Found R52 segment: {r52_seg['name']}")
        print(f"    Start: {r52_seg['start']}")
        print(f"    End: {r52_seg['end']}")
        print(f"    Size: {r52_seg['size']} bytes (0x{r52_seg['size']:X})")
    else:
        print("[!] R52 segment not found by name")
        r52_seg = None
    print()
    
    # Search for "R52" string references
    print("[*] Searching for 'R52' string references...")
    refs = find_overlay_references("R52")
    
    print(f"[+] Found {len(refs)} references to 'R52'")
    for ref in refs[:10]:
        print(f"    String at {ref['string_addr']}: \"{ref['string']}\"")
        print(f"      Referenced from {ref['xref_from']} in {ref['xref_func']}")
    print()
    
    # Look for known overlay patterns
    print("[*] Searching for R52 overlay loader patterns...")
    
    # Based on R45/R57, look for segment around 0x15xxxx or 0x1Axxxx
    potential_starts = [
        0x158000, 0x159000, 0x15A000, 0x15B000,  # After R45 (0x156945)
        0x1A8000, 0x1A9000, 0x1AA000, 0x1AB000   # After R57 (0x1A57F0)
    ]
    
    found_functions = []
    for addr in potential_starts:
        func = idaapi.get_func(addr)
        if func:
            func_name = idc.get_func_name(addr)
            func_size = func.end_ea - func.start_ea
            
            # Look for medium-large functions (R45=2614, R57=3083)
            if func_size > 1000:
                print(f"[*] Found large function at 0x{addr:X}: {func_name} ({func_size} bytes)")
                found_functions.append({
                    'addr': hex(addr),
                    'name': func_name,
                    'size': func_size
                })
    
    if found_functions:
        print(f"[+] Found {len(found_functions)} potential R52 functions")
    print()
    
    # Try to find R52 by looking at the overlay table
    print("[*] Searching for overlay dispatch table...")
    
    # In Falcon 3.0, overlays are typically loaded via a dispatch table
    # Look for references to "R45", "R52", "R57" strings near each other
    
    # Alternative: scan for functions that load/call overlays
    overlay_loaders = []
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        if 'overlay' in func_name.lower() or 'menu' in func_name.lower():
            overlay_loaders.append({
                'addr': hex(func_ea),
                'name': func_name
            })
    
    if overlay_loaders:
        print(f"[+] Found {len(overlay_loaders)} potential overlay loaders:")
        for loader in overlay_loaders[:10]:
            print(f"    {loader['addr']}: {loader['name']}")
    print()
    
    # If we have R52 segment, analyze it
    if r52_seg:
        print("[*] Analyzing R52 segment functions...")
        seg_start = int(r52_seg['start'], 16)
        seg_end = int(r52_seg['end'], 16)
        
        # Find all functions in segment
        r52_functions = []
        for func_ea in idautils.Functions(seg_start, seg_end):
            func_info = extract_function_info(func_ea)
            if func_info:
                r52_functions.append(func_info)
        
        print(f"[+] Found {len(r52_functions)} functions in R52 segment")
        
        # Find the largest function (likely the main menu logic)
        if r52_functions:
            largest = max(r52_functions, key=lambda f: f['size'])
            print(f"[+] Largest function: {largest['name']} at {largest['start']}")
            print(f"    Size: {largest['size']} bytes")
            print(f"    Instructions: {largest['instruction_count']}")
            print(f"    Calls: {len(largest['calls'])}")
            
            # Export disassembly
            print("\n[*] Exporting disassembly of main R52 function...")
            func_addr = int(largest['start'], 16)
            func = idaapi.get_func(func_addr)
            
            disasm_lines = []
            ea = func.start_ea
            while ea < func.end_ea:
                disasm = idc.generate_disasm_line(ea, 0)
                disasm_lines.append(f"{ea:08X}  {disasm}")
                ea = idc.next_head(ea, func.end_ea)
            
            with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\r52_main_function.asm', 'w') as f:
                f.write(f"; {largest['name']}\n")
                f.write(f"; Address: {largest['start']} - {largest['end']}\n")
                f.write(f"; Size: {largest['size']} bytes\n\n")
                for line in disasm_lines:
                    f.write(line + "\n")
            
            print(f"[+] Saved disassembly to analysis/r52_main_function.asm")
    
    # Save results
    result = {
        'r52_segment': r52_seg,
        'string_references': len(refs),
        'potential_functions': found_functions,
        'overlay_loaders': overlay_loaders[:10] if overlay_loaders else [],
        'r52_functions': r52_functions if r52_seg else []
    }
    
    with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\r52_extraction_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print("\n[+] Results saved to analysis/r52_extraction_result.json")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
