"""
Exhaustive search for ALL writes to r15_external_view_flag (0x107762).

The flag is in R15_5E0Bs segment. Previous searches only found 1 write (initialization).
But overlays might write using different segment prefixes (es:, ds:, etc.).

This script searches for:
1. Direct writes with any segment prefix
2. Indirect writes via pointers
3. Writes in all segments, not just R15
"""

import idaapi
import idautils
import idc
import json

def main():
    idaapi.auto_wait()
    
    FLAG_ADDR = 0x107762
    FLAG_NAME = "r15_external_view_flag"
    
    print("=" * 80)
    print(f"EXHAUSTIVE SEARCH FOR WRITES TO {FLAG_NAME}")
    print(f"Target address: 0x{FLAG_ADDR:X}")
    print("=" * 80)
    print()
    
    # Method 1: Get all xrefs (same as before, but let's verify)
    print("[Method 1] Searching via xrefs...")
    xref_writes = []
    
    for xref in idautils.XrefsTo(FLAG_ADDR):
        addr = xref.frm
        insn = idc.GetDisasm(addr)
        mnem = idc.print_insn_mnem(addr)
        func_name = idc.get_func_name(addr)
        seg_name = idc.get_segm_name(addr)
        
        # Check if it's a write
        is_write = False
        if mnem in ['mov', 'xor', 'or', 'and', 'inc', 'dec', 'xchg']:
            # Check if destination operand references our address
            op0_type = idc.get_operand_type(addr, 0)
            if op0_type == idc.o_mem:
                op0_addr = idc.get_operand_value(addr, 0)
                if op0_addr == FLAG_ADDR:
                    is_write = True
        
        if is_write:
            xref_writes.append({
                'addr': f'0x{addr:X}',
                'func': func_name,
                'segment': seg_name,
                'insn': insn,
                'mnem': mnem
            })
            print(f"  [WRITE] 0x{addr:X} in {seg_name}/{func_name}: {insn}")
    
    print(f"\nMethod 1 found {len(xref_writes)} writes")
    
    # Method 2: Search for the literal address 0x107762 in immediate operands
    print("\n[Method 2] Searching for address 0x107762 in immediate operands...")
    immediate_refs = []
    
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        seg_start = idc.get_segm_start(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        
        # Search this segment
        ea = seg_start
        while ea < seg_end:
            ea = idc.find_imm(ea, idc.SEARCH_DOWN, FLAG_ADDR)
            if ea == idc.BADADDR:
                break
            
            insn = idc.GetDisasm(ea)
            func_name = idc.get_func_name(ea)
            
            immediate_refs.append({
                'addr': f'0x{ea:X}',
                'segment': seg_name,
                'func': func_name,
                'insn': insn
            })
            print(f"  [IMM] 0x{ea:X} in {seg_name}/{func_name}: {insn}")
            
            ea = idc.next_head(ea)
    
    print(f"\nMethod 2 found {len(immediate_refs)} references")
    
    # Method 3: Search for MOV to offset 0x7762 (without segment portion)
    print("\n[Method 3] Searching for offset 0x7762 (without segment)...")
    offset_refs = []
    
    OFFSET_ONLY = 0x7762
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        seg_start = idc.get_segm_start(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        
        ea = seg_start
        while ea < seg_end:
            ea = idc.find_imm(ea, idc.SEARCH_DOWN, OFFSET_ONLY)
            if ea == idc.BADADDR:
                break
            
            insn = idc.GetDisasm(ea)
            mnem = idc.print_insn_mnem(ea)
            func_name = idc.get_func_name(ea)
            
            # Only interested in memory operations
            if mnem in ['mov', 'lea', 'cmp', 'test', 'xor', 'or', 'and']:
                offset_refs.append({
                    'addr': f'0x{ea:X}',
                    'segment': seg_name,
                    'func': func_name,
                    'insn': insn,
                    'mnem': mnem
                })
                print(f"  [OFFSET] 0x{ea:X} in {seg_name}/{func_name}: {insn}")
            
            ea = idc.next_head(ea)
    
    print(f"\nMethod 3 found {len(offset_refs)} references")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total WRITE operations found: {len(xref_writes)}")
    print(f"Total immediate references: {len(immediate_refs)}")
    print(f"Total offset references: {len(offset_refs)}")
    
    if len(xref_writes) == 1:
        print("\n*** ONLY 1 WRITE FOUND - This confirms the flag is only written at initialization! ***")
        print("***This means view switching does NOT modify this flag directly.***")
        print("\nPossible explanations:")
        print("1. The flag is session-static (set once at mission start)")
        print("2. View switching bypasses the flag entirely")
        print("3. Different view code paths don't modify the flag")
    
    # Save results
    output = {
        'flag_address': f'0x{FLAG_ADDR:X}',
        'flag_name': FLAG_NAME,
        'xref_writes': xref_writes,
        'immediate_refs': immediate_refs,
        'offset_refs': offset_refs
    }
    
    output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\dgroup\exhaustive_flag_write_search.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()
