#!/usr/bin/env python3
"""
Analyze what's around the flag address - maybe it's part of a structure
that gets written as a whole, or accessed via base+offset.
"""

import idc
import idaapi
import json

def main():
    idaapi.auto_wait()
    
    flag_addr = 0x107762
    context_size = 32  # Look at 32 bytes before and after
    
    print("[*] Analyzing context around r15_external_view_flag @ 0x{:X}".format(flag_addr))
    print()
    
    # Get bytes around the flag
    start = flag_addr - context_size
    end = flag_addr + context_size
    
    print("Memory dump (0x{:X} - 0x{:X}):".format(start, end))
    for addr in range(start, end + 1):
        byte_val = idc.get_wide_byte(addr)
        name = idc.get_name(addr)
        cmt = idc.get_cmt(addr, 0)
        
        marker = " <-- FLAG" if addr == flag_addr else ""
        name_str = " ({})".format(name) if name else ""
        cmt_str = " ; {}".format(cmt) if cmt else ""
        
        print("  0x{:08X}: {:02X}{}{}{}".format(addr, byte_val, marker, name_str, cmt_str))
    
    print()
    print("="*80)
    print("Checking for structure definitions...")
    print()
    
    # Check what IDA thinks this memory is
    flags = idc.get_full_flags(flag_addr)
    
    if idc.is_byte(flags):
        print("IDA type: BYTE")
    elif idc.is_word(flags):
        print("IDA type: WORD")
    elif idc.is_dword(flags):
        print("IDA type: DWORD")
    else:
        print("IDA type: Unknown")
    
    # Check for any names/labels nearby
    print()
    print("Named locations in context:")
    for addr in range(start, end + 1):
        name = idc.get_name(addr)
        if name:
            print("  0x{:08X}: {}".format(addr, name))
    
    # Check for xrefs to nearby addresses
    print()
    print("Checking xrefs to nearby addresses...")
    for offset in range(-16, 17):
        addr = flag_addr + offset
        xrefs = list(idautils.XrefsTo(addr))
        if xrefs and addr != flag_addr:  # We already know flag xrefs
            print("  0x{:08X} (offset {:+3d}): {} xrefs".format(addr, offset, len(xrefs)))
    
    # Save analysis
    output = {
        'flag_address': '0x{:X}'.format(flag_addr),
        'flag_byte_value': idc.get_wide_byte(flag_addr),
        'memory_context': {}
    }
    
    for addr in range(start, end + 1):
        output['memory_context']['0x{:X}'.format(addr)] = {
            'byte': idc.get_wide_byte(addr),
            'name': idc.get_name(addr) or None,
            'comment': idc.get_cmt(addr, 0) or None
        }
    
    with open(r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\flag_context.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("Results saved to flag_context.json")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
