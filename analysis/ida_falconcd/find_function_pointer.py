"""
Find what function pointer is stored at cs:dword_22084
This is an indirect call pattern
"""
import idaapi
import idc
import idautils
import json

def main():
    try:
        print("[*] Waiting for auto-analysis...")
        idaapi.auto_wait()
        print("[+] Auto-analysis complete")
        
        # The address 0x22084 is likely a CS-relative offset
        # Need to find actual address
        ptr_ea = idc.get_name_ea_simple('dword_22084')
        
        if ptr_ea == idc.BADADDR:
            print(f"[-] dword_22084 not found by name, trying literal address")
            ptr_ea = 0x22084
        
        print(f"[+] Checking address 0x{ptr_ea:X}")
        
        # Read the dword (far pointer: offset:segment)
        dword_val = idc.get_wide_dword(ptr_ea)
        offset = dword_val & 0xFFFF
        segment = (dword_val >> 16) & 0xFFFF
        
        print(f"[+] Function pointer at 0x{ptr_ea:X}:")
        print(f"    Raw value: 0x{dword_val:08X}")
        print(f"    Segment: 0x{segment:04X}")
        print(f"    Offset: 0x{offset:04X}")
        
        # Try to find what function this points to
        # Calculate linear address (segment * 16 + offset)
        linear_addr = (segment << 4) + offset
        print(f"    Linear address (approx): 0x{linear_addr:X}")
        
        # Check if there's a function at the offset
        func_name = idc.get_func_name(offset)
        if func_name:
            print(f"[+] Points to function: {func_name}")
        else:
            print(f"[-] No function found at offset 0x{offset:X}")
        
        # Find all cross-references to this pointer
        print("\n[*] Finding cross-references to dword_22084...")
        xrefs = []
        for xref in idautils.XrefsTo(ptr_ea):
            xref_func = idc.get_func_name(xref.frm)
            xrefs.append({
                'from': xref.frm,
                'func': xref_func,
                'type': xref.type
            })
        
        print(f"[+] Found {len(xrefs)} cross-references")
        for i, xref in enumerate(xrefs[:10]):
            print(f"    0x{xref['from']:X}: {xref['func']}")
        
        # Save results
        result = {
            'pointer_address': ptr_ea,
            'raw_value': dword_val,
            'segment': segment,
            'offset': offset,
            'linear_address': linear_addr,
            'target_function': func_name if func_name else None,
            'xrefs': xrefs
        }
        
        output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\function_pointer_22084.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n[+] Saved to {output_file}")
        
        # If we found the target function, analyze it briefly
        if func_name:
            print(f"\n[*] Analyzing target function {func_name}...")
            target_func = idaapi.get_func(offset)
            if target_func:
                print(f"[+] Function size: {target_func.end_ea - target_func.start_ea} bytes")
                print(f"[+] Start: 0x{target_func.start_ea:X}")
                print(f"[+] End: 0x{target_func.end_ea:X}")
        
    except Exception as e:
        print(f"[-] ERROR: {e}")
        import traceback
        traceback.print_exc()
        idc.qexit(1)

if __name__ == "__main__":
    main()
    idc.qexit(0)
