#!/usr/bin/env python3
"""
Analyze R53 Mission/Briefing Menu (the largest R5X overlay).

R53 has 32352 bytes and 48 functions - this is the main mission briefing UI.
"""

import idc
import idaapi
import idautils
import json

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("R53 MISSION/BRIEFING MENU ANALYSIS")
    print("="*80)
    print()
    
    # Find R53 segment
    r53_start = None
    r53_end = None
    
    for seg_ea in idautils.Segments():
        name = idc.get_segm_name(seg_ea)
        if "R53" in name:
            r53_start = seg_ea
            r53_end = idc.get_segm_end(seg_ea)
            print(f"[+] Found R53 segment: {name}")
            print(f"    Range: 0x{r53_start:X} - 0x{r53_end:X}")
            print(f"    Size: {r53_end - r53_start} bytes (0x{r53_end - r53_start:X})")
            break
    
    if not r53_start:
        print("[!] R53 segment not found")
        idc.qexit(1)
    
    print()
    
    # Analyze all functions in R53
    print("[*] Analyzing R53 functions...")
    
    r53_functions = []
    for func_ea in idautils.Functions(r53_start, r53_end):
        func = idaapi.get_func(func_ea)
        if func:
            func_name = idc.get_func_name(func_ea)
            func_size = func.end_ea - func.start_ea
            
            # Count instructions
            insn_count = 0
            ea = func.start_ea
            while ea < func.end_ea:
                insn_count += 1
                ea = idc.next_head(ea, func.end_ea)
            
            # Count calls
            call_count = 0
            ea = func.start_ea
            while ea < func.end_ea:
                if idc.print_insn_mnem(ea) == 'call':
                    call_count += 1
                ea = idc.next_head(ea, func.end_ea)
            
            r53_functions.append({
                'name': func_name,
                'addr': hex(func_ea),
                'size': func_size,
                'instructions': insn_count,
                'calls': call_count
            })
    
    print(f"[+] Found {len(r53_functions)} functions")
    print()
    
    # Find largest functions (likely main logic)
    print("[*] Top 10 largest functions:")
    for func in sorted(r53_functions, key=lambda f: f['size'], reverse=True)[:10]:
        print(f"    {func['addr']}: {func['name']:40} {func['size']:5} bytes, {func['instructions']:4} insns, {func['calls']:3} calls")
    print()
    
    # Extract strings referenced from R53
    print("[*] Extracting strings referenced from R53...")
    
    strings_found = {}
    ea = r53_start
    while ea < r53_end:
        for xref in idautils.XrefsFrom(ea, 0):
            target = xref.to
            str_type = idc.get_str_type(target)
            if str_type is not None:
                string_val = idc.get_strlit_contents(target)
                if string_val:
                    string_key = string_val.decode('ascii', errors='ignore')
                    if string_key not in strings_found:
                        strings_found[string_key] = hex(target)
        ea = idc.next_head(ea, r53_end)
    
    print(f"[+] Found {len(strings_found)} unique strings")
    print()
    print("[*] Mission/briefing related strings:")
    for string in sorted(strings_found.keys()):
        if any(kw in string.upper() for kw in ['MISSION', 'FLIGHT', 'TARGET', 'WAYPOINT', 'ALTITUDE', 'SPEED', 'PILOT', 'AIRCRAFT']):
            print(f"    \"{string}\"")
    print()
    
    # Export disassembly of largest function
    largest = max(r53_functions, key=lambda f: f['size'])
    print(f"[*] Exporting largest function: {largest['name']} ({largest['size']} bytes)")
    
    func_ea = int(largest['addr'], 16)
    func = idaapi.get_func(func_ea)
    
    disasm_lines = []
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        disasm_lines.append(f"{ea:08X}  {disasm}")
        ea = idc.next_head(ea, func.end_ea)
    
    with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\r53_main_function.asm', 'w') as f:
        f.write(f"; {largest['name']}\n")
        f.write(f"; Address: {largest['addr']}\n")
        f.write(f"; Size: {largest['size']} bytes\n")
        f.write(f"; Instructions: {largest['instructions']}\n")
        f.write(f"; Calls: {largest['calls']}\n\n")
        for line in disasm_lines:
            f.write(line + "\n")
    
    print(f"[+] Saved to analysis/r53_main_function.asm")
    print()
    
    # Save results
    result = {
        'segment': {
            'name': idc.get_segm_name(r53_start),
            'start': hex(r53_start),
            'end': hex(r53_end),
            'size': r53_end - r53_start
        },
        'function_count': len(r53_functions),
        'functions': r53_functions,
        'largest_function': largest,
        'string_count': len(strings_found),
        'strings': list(strings_found.keys())
    }
    
    with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\r53_analysis_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"[+] Results saved to analysis/r53_analysis_result.json")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
