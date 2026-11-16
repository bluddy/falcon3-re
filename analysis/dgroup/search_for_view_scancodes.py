"""
Search for comparisons with view key scan codes (0x02-0x0B) throughout the codebase.

Maybe the view key dispatch is not in the functions we examined.
Let's do a brute-force search for all places that compare with these scan codes.
"""

import idc
import idaapi
import idautils
import json

def main():
    idaapi.auto_wait()
    
    # View key scan codes
    VIEW_KEYS = list(range(0x02, 0x0C))  # 0x02-0x0B
    
    print("=" * 80)
    print("SEARCHING FOR VIEW KEY SCAN CODE COMPARISONS")
    print("=" * 80)
    print(f"Looking for: {[hex(x) for x in VIEW_KEYS]}")
    print()
    
    findings = []
    
    for scan_code in VIEW_KEYS:
        print(f"\n[*] Searching for scan code 0x{scan_code:02X}...")
        
        # Search for this immediate value
        ea = 0
        count = 0
        while True:
            ea = idc.find_imm(ea, idc.SEARCH_DOWN | idc.SEARCH_NEXT, scan_code)
            if ea == idc.BADADDR:
                break
            
            # Get context
            insn = idc.GetDisasm(ea)
            mnem = idc.print_insn_mnem(ea)
            func = idc.get_func_name(ea)
            seg = idc.get_segm_name(ea)
            
            # Only interested in cmp/test instructions
            if mnem in ['cmp', 'test', 'sub']:
                print(f"  [CMP] 0x{ea:X} in {seg}/{func}: {insn}")
                
                findings.append({
                    'scan_code': f'0x{scan_code:02X}',
                    'addr': f'0x{ea:X}',
                    'segment': seg,
                    'function': func,
                    'mnem': mnem,
                    'insn': insn
                })
                
                count += 1
                if count >= 5:  # Limit per scan code
                    print(f"  ... (limiting to 5 per scan code)")
                    break
    
    print(f"\n\nFound {len(findings)} total comparisons")
    
    # Save
    output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\dgroup\view_scancode_comparisons.json"
    with open(output_file, 'w') as f:
        json.dump(findings, f, indent=2)
    
    print(f"Results saved to: {output_file}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
