"""
Exhaustive search for ALL writes to view_pipeline_mode (0x107762).

Search strategies:
1. Direct xrefs (already done, found 1)
2. Search for immediate 0x107762 in code
3. Search for offset 0x7762 (segment-relative)
4. Look for MOV to [BX] where BX might contain the address
"""

import idc
import idaapi
import idautils

def main():
    idaapi.auto_wait()
    
    FLAG_ADDR = 0x107762
    FLAG_OFFSET = 0x7762
    
    print("="*80)
    print("EXHAUSTIVE SEARCH FOR ALL WRITES TO view_pipeline_mode")
    print("="*80)
    print(f"Target: 0x{FLAG_ADDR:X}")
    print()
    
    all_writes = []
    
    # Method 1: Direct xrefs (we know this finds 1)
    print("[Method 1] Direct xrefs to 0x107762:")
    print("-"*80)
    
    for xref in idautils.XrefsTo(FLAG_ADDR):
        addr = xref.frm
        insn = idc.GetDisasm(addr)
        mnem = idc.print_insn_mnem(addr)
        func = idc.get_func_name(addr)
        
        # Check if write
        is_write = False
        if mnem in ['mov', 'xor', 'or', 'and', 'inc', 'dec']:
            op0_type = idc.get_operand_type(addr, 0)
            if op0_type == idc.o_mem:
                op0_val = idc.get_operand_value(addr, 0)
                if op0_val == FLAG_ADDR:
                    is_write = True
        
        if is_write:
            print(f"  WRITE: 0x{addr:X} in {func}: {insn}")
            all_writes.append({
                'method': 1,
                'addr': f'0x{addr:X}',
                'func': func,
                'insn': insn
            })
        else:
            print(f"  READ:  0x{addr:X} in {func}: {insn}")
    
    # Method 2: Search for immediate 0x107762
    print(f"\n[Method 2] Searching for immediate 0x{FLAG_ADDR:X}:")
    print("-"*80)
    
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        seg_start = idc.get_segm_start(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        
        ea = seg_start
        while ea < seg_end:
            ea = idc.find_imm(ea, idc.SEARCH_DOWN, FLAG_ADDR)
            if ea == idc.BADADDR:
                break
            
            insn = idc.GetDisasm(ea)
            func = idc.get_func_name(ea)
            mnem = idc.print_insn_mnem(ea)
            
            # Skip if already found via xref
            found_in_xrefs = any(w['addr'] == f'0x{ea:X}' for w in all_writes)
            if not found_in_xrefs and mnem in ['mov', 'lea']:
                print(f"  Found: 0x{ea:X} in {seg_name}/{func}: {insn}")
                all_writes.append({
                    'method': 2,
                    'addr': f'0x{ea:X}',
                    'func': func,
                    'insn': insn,
                    'segment': seg_name
                })
            
            ea = idc.next_head(ea)
    
    # Method 3: Search for offset 0x7762
    print(f"\n[Method 3] Searching for offset 0x{FLAG_OFFSET:X}:")
    print("-"*80)
    
    count = 0
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        seg_start = idc.get_segm_start(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        
        ea = seg_start
        while ea < seg_end:
            ea = idc.find_imm(ea, idc.SEARCH_DOWN, FLAG_OFFSET)
            if ea == idc.BADADDR:
                break
            
            insn = idc.GetDisasm(ea)
            func = idc.get_func_name(ea)
            mnem = idc.print_insn_mnem(ea)
            
            # Only show MOV instructions
            if mnem == 'mov' and count < 20:  # Limit output
                print(f"  Found: 0x{ea:X} in {seg_name}/{func}: {insn}")
                count += 1
            
            ea = idc.next_head(ea)
    
    if count >= 20:
        print(f"  ... (showing first 20, total likely more)")
    
    # Summary
    print(f"\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total writes found: {len(all_writes)}")
    
    for w in all_writes:
        print(f"\n[Method {w['method']}] 0x{w['addr']} in {w['func']}")
        print(f"  {w['insn']}")
    
    if len(all_writes) == 1:
        print("\n*** CONFIRMED: Only 1 direct write to flag! ***")
        print("*** The flag IS session-static (set once at init) ***")
        print("\n[Hypothesis Update]")
        print("Since there's only 1 write, the mode must be:")
        print("  A) Set by a parameter to view_mode_set, OR")
        print("  B) Modified by writing to a different address that aliases to 0x107762, OR")
        print("  C) Our ACMI hypothesis is wrong - the flag controls something else")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
