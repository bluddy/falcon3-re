#!/usr/bin/env python3
"""
Find where input_flag_pending_2 is READ in R15 overlay and used to dispatch view changes.
Focus on R15_5E0Bs and R29_3174s segments.
"""

import idc
import idaapi
import idautils
import json

def main():
    idaapi.auto_wait()
    
    print("[*] Searching for input_flag_pending_2 readers in R15 overlay...")
    print()
    
    # R15 segments
    r15_segments = ['R15_5E0Bs', 'R29_3174s']
    
    # Find the address of input_flag_pending_2
    flag_name = "input_flag_pending_2"
    
    # Search for references in R15 segments
    found = []
    
    for seg_name in r15_segments:
        print(f"[*] Searching segment {seg_name}...")
        
        # Get segment bounds
        for seg_ea in idautils.Segments():
            if idc.get_segm_name(seg_ea) == seg_name:
                seg_start = seg_ea
                seg_end = idc.get_segm_end(seg_ea)
                
                print(f"    Segment: 0x{seg_start:X} - 0x{seg_end:X}")
                
                # Search for the pattern in disassembly
                ea = seg_start
                while ea < seg_end:
                    insn = idc.generate_disasm_line(ea, 0)
                    
                    if 'input_flag_pending_2' in insn:
                        func_name = idc.get_func_name(ea)
                        mnem = idc.print_insn_mnem(ea).lower()
                        
                        # Determine if read or write
                        access_type = "UNKNOWN"
                        if 'mov' in mnem:
                            op0 = idc.print_operand(ea, 0)
                            if 'input_flag_pending_2' in op0:
                                access_type = "WRITE"
                            else:
                                access_type = "READ"
                        elif 'cmp' in mnem:
                            access_type = "READ (cmp)"
                        
                        entry = {
                            'addr': '0x{:X}'.format(ea),
                            'segment': seg_name,
                            'func': func_name,
                            'access': access_type,
                            'insn': insn
                        }
                        
                        found.append(entry)
                        
                        print(f"    [{access_type:10s}] 0x{ea:X} in {func_name}")
                        print(f"                {insn}")
                    
                    ea = idc.next_head(ea, seg_end)
                
                break
    
    print()
    print("="*80)
    print(f"Found {len(found)} references to input_flag_pending_2 in R15")
    print("="*80)
    
    # Now analyze each READ location in detail
    print()
    print("[*] Analyzing READ locations for view dispatch logic...")
    print()
    
    for entry in found:
        if 'READ' in entry['access']:
            addr = int(entry['addr'], 16)
            func_name = entry['func']
            
            print(f"\n{'='*80}")
            print(f"Function: {func_name} @ 0x{addr:X}")
            print(f"{'='*80}")
            
            # Get context around this read
            func_ea = idc.get_func_attr(addr, idc.FUNCATTR_START)
            if func_ea != idc.BADADDR:
                # Print 20 instructions around the read
                print("\nContext (±10 instructions):")
                
                insn_list = []
                func = idaapi.get_func(func_ea)
                if func:
                    temp_ea = func.start_ea
                    while temp_ea < func.end_ea:
                        insn_list.append({
                            'addr': temp_ea,
                            'disasm': idc.generate_disasm_line(temp_ea, 0)
                        })
                        temp_ea = idc.next_head(temp_ea, func.end_ea)
                    
                    # Find our instruction in the list
                    target_idx = None
                    for i, insn in enumerate(insn_list):
                        if insn['addr'] == addr:
                            target_idx = i
                            break
                    
                    if target_idx:
                        start_idx = max(0, target_idx - 10)
                        end_idx = min(len(insn_list), target_idx + 11)
                        
                        for i in range(start_idx, end_idx):
                            marker = " >>> " if i == target_idx else "     "
                            print(f"{marker}0x{insn_list[i]['addr']:X}: {insn_list[i]['disasm']}")
    
    # Save results
    output = {
        'r15_segments': r15_segments,
        'references_found': len(found),
        'references': found
    }
    
    with open(r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\r15_input_flag_refs.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("="*80)
    print(f"[+] Results saved to r15_input_flag_refs.json")
    print(f"[+] Found {len([e for e in found if 'READ' in e['access']])} READ locations in R15")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
