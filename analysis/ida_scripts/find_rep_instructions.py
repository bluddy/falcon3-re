"""
Search globally for REP STOSB/MOVSB instructions - typical in decompressors.

REP STOSB = fast fill (repeat STOSB = store AL into [ES:DI], increment DI)
REP MOVSB = fast copy (repeat MOVSB = copy byte from [DS:SI] to [ES:DI])

These are signatures of RLE decompression or similar algorithms.

Run in IDA: File > Script file > find_rep_instructions.py
"""

import idaapi
import idc
import idautils
import json

def find_rep_instructions():
    """Search entire binary for REP STOSB and REP MOVSB."""
    
    print("="*80)
    print("SEARCHING FOR REP STOSB/MOVSB INSTRUCTIONS")
    print("="*80)
    
    idaapi.auto_wait()
    
    rep_stosb = []
    rep_movsb = []
    rep_other = []
    
    # Search all code segments
    for seg_ea in idautils.Segments():
        seg = idaapi.getseg(seg_ea)
        if not seg or seg.type != idaapi.SEG_CODE:
            continue
        
        seg_name = idc.get_segm_name(seg_ea)
        print(f"\nScanning segment: {seg_name} (0x{seg.start_ea:x} - 0x{seg.end_ea:x})")
        
        # Scan all instructions in segment
        for head in idautils.Heads(seg.start_ea, seg.end_ea):
            if not idc.is_code(idc.get_full_flags(head)):
                continue
            
            mnem = idc.print_insn_mnem(head).lower()
            
            if mnem == 'rep' or mnem == 'repe' or mnem == 'repz':
                # Check next instruction
                next_head = idc.next_head(head)
                if next_head == idaapi.BADADDR:
                    continue
                
                next_mnem = idc.print_insn_mnem(next_head).lower()
                
                # Get containing function
                func = idaapi.get_func(head)
                func_name = idc.get_func_name(func.start_ea) if func else "NO_FUNCTION"
                func_addr = func.start_ea if func else 0
                
                entry = {
                    'address': f'0x{head:x}',
                    'function': func_name,
                    'function_addr': f'0x{func_addr:x}' if func_addr else 'N/A',
                    'instruction': idc.GetDisasm(head),
                    'next_instruction': idc.GetDisasm(next_head)
                }
                
                if next_mnem == 'stosb':
                    rep_stosb.append(entry)
                    print(f"  [STOSB] 0x{head:06x}: {func_name:40s} - {entry['instruction']} / {entry['next_instruction']}")
                elif next_mnem == 'movsb':
                    rep_movsb.append(entry)
                    print(f"  [MOVSB] 0x{head:06x}: {func_name:40s} - {entry['instruction']} / {entry['next_instruction']}")
                else:
                    rep_other.append(entry)
                    print(f"  [OTHER] 0x{head:06x}: {func_name:40s} - {entry['instruction']} / {entry['next_instruction']}")
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SEARCH RESULTS")
    print(f"{'='*80}")
    print(f"REP STOSB found: {len(rep_stosb)}")
    print(f"REP MOVSB found: {len(rep_movsb)}")
    print(f"REP other found: {len(rep_other)}")
    print(f"Total REP instructions: {len(rep_stosb) + len(rep_movsb) + len(rep_other)}")
    
    # Show unique functions with REP STOSB
    if rep_stosb:
        print(f"\n{'='*80}")
        print(f"FUNCTIONS WITH REP STOSB (likely decompressors/fill operations):")
        print(f"{'='*80}")
        
        funcs = {}
        for entry in rep_stosb:
            func_name = entry['function']
            if func_name not in funcs:
                funcs[func_name] = []
            funcs[func_name].append(entry['address'])
        
        for func_name, addrs in sorted(funcs.items()):
            print(f"\n  {func_name} ({len(addrs)} occurrences)")
            for addr in addrs[:5]:  # Show first 5
                print(f"    {addr}")
    
    # Show unique functions with REP MOVSB
    if rep_movsb:
        print(f"\n{'='*80}")
        print(f"FUNCTIONS WITH REP MOVSB (likely copy operations):")
        print(f"{'='*80}")
        
        funcs = {}
        for entry in rep_movsb:
            func_name = entry['function']
            if func_name not in funcs:
                funcs[func_name] = []
            funcs[func_name].append(entry['address'])
        
        for func_name, addrs in sorted(funcs.items()):
            print(f"\n  {func_name} ({len(addrs)} occurrences)")
            for addr in addrs[:5]:
                print(f"    {addr}")
    
    # Save results
    output_file = r'c:\Users\ybarnoy\projects\falcon3\analysis\rep_instructions_found.json'
    result = {
        'rep_stosb': rep_stosb,
        'rep_movsb': rep_movsb,
        'rep_other': rep_other,
        'summary': {
            'total_stosb': len(rep_stosb),
            'total_movsb': len(rep_movsb),
            'total_other': len(rep_other)
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*80}")
    
    if rep_stosb or rep_movsb:
        print(f"\n[RECOMMENDATION]")
        print(f"Examine the functions listed above - they likely contain")
        print(f"decompression or data manipulation code.")
        print(f"RLE decompressors typically use REP STOSB for filling runs.")
    else:
        print(f"\n[NO REP INSTRUCTIONS FOUND]")
        print(f"The decompression may:")
        print(f"  1. Use manual loops instead of REP")
        print(f"  2. Be implemented in a dispatch table")
        print(f"  3. Use a different instruction pattern")

if __name__ == '__main__':
    find_rep_instructions()
