#!/usr/bin/env python3
"""
Look at HOW the readers access the flag. Maybe writers use same pattern
but IDA doesn't see the xref.
"""

import idc
import idaapi
import idautils
import json

def get_function_disasm(start_ea, end_ea):
    """Get all instructions in a range."""
    insns = []
    ea = start_ea
    while ea < end_ea:
        insns.append({
            'addr': '0x{:X}'.format(ea),
            'mnem': idc.print_insn_mnem(ea),
            'disasm': idc.generate_disasm_line(ea, 0),
            'bytes': ' '.join(['{:02X}'.format(idc.get_wide_byte(ea + i)) for i in range(idc.get_item_size(ea))])
        })
        ea = idc.next_head(ea, end_ea)
    return insns

def main():
    idaapi.auto_wait()
    
    flag_addr = 0x107762
    
    # Get the one known writer
    writer_func = 0x1086EC  # view_mode_set
    writer_insn = 0x1087B2  # the mov instruction
    
    print("[*] Analyzing HOW the flag is accessed...")
    print()
    print("="*80)
    print("KNOWN WRITER: view_mode_set @ 0x{:X}".format(writer_func))
    print("="*80)
    
    # Get context around the write
    writer_context = []
    for offset in range(-10, 11):
        addr = writer_insn + offset * 2  # rough estimate
        if idc.is_code(idc.get_full_flags(addr)):
            insn = idc.generate_disasm_line(addr, 0)
            marker = " <-- WRITE" if addr == writer_insn else ""
            writer_context.append({
                'addr': '0x{:X}'.format(addr),
                'insn': insn
            })
            print("{} 0x{:X}: {}".format(">>>" if marker else "   ", addr, insn))
    
    # Get the exact bytes of the write instruction
    print()
    print("Write instruction bytes:")
    write_size = idc.get_item_size(writer_insn)
    write_bytes = [idc.get_wide_byte(writer_insn + i) for i in range(write_size)]
    print("  0x{:X}: {}".format(writer_insn, ' '.join(['{:02X}'.format(b) for b in write_bytes])))
    print("  Pattern: MOV CS:[offset], AL")
    
    # Now search for similar patterns
    print()
    print("="*80)
    print("SEARCHING FOR SIMILAR WRITE PATTERNS")
    print("="*80)
    
    # The write is: 2E 88 06 62 77  (mov cs:[7762h], al)
    # Search for: 2E 88 or 2E 89 (CS: prefix + MOV to memory)
    
    similar = []
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        if 'R15' not in seg_name:
            continue  # Only R15 segment
        
        ea = seg_ea
        seg_end = idc.get_segm_end(seg_ea)
        
        while ea < seg_end:
            if idc.get_wide_byte(ea) == 0x2E:  # CS: prefix
                next_byte = idc.get_wide_byte(ea + 1)
                if next_byte in [0x88, 0x89, 0xC6, 0xC7]:  # MOV variants
                    insn = idc.generate_disasm_line(ea, 0)
                    if 'cs:' in insn.lower():
                        func_name = idc.get_func_name(ea)
                        similar.append({
                            'addr': '0x{:X}'.format(ea),
                            'func': func_name,
                            'insn': insn,
                            'bytes': ' '.join(['{:02X}'.format(idc.get_wide_byte(ea + i)) for i in range(4)])
                        })
                        print("[CS:WRITE] 0x{:X} in {}: {}".format(ea, func_name, insn))
            
            ea = ea + 1  # Byte-by-byte scan
    
    print()
    print("Found {} CS: write instructions in R15".format(len(similar)))
    
    # Save
    output = {
        'flag_address': '0x{:X}'.format(flag_addr),
        'writer_instruction': {
            'addr': '0x{:X}'.format(writer_insn),
            'bytes': ' '.join(['{:02X}'.format(b) for b in write_bytes]),
            'context': writer_context
        },
        'similar_patterns': similar
    }
    
    with open(r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\access_patterns.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("Results saved to access_patterns.json")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
