"""
Find code that copies from file buffer to mission slot array
Look for references to buffer 0x602E:0x068F and dword_79D3E
"""

import idaapi
import idc
import idautils
import json

def find_buffer_and_slot_refs():
    """Find code that accesses both file buffer and mission slot array"""
    
    # Key addresses
    buffer_seg = 0x602E
    mission_slot_ptr = 0x79D3E
    
    print("Searching for file buffer copy operations...")
    print("-" * 80)
    
    # Find all references to mission slot pointer in squadron_mission_file_loader
    func_addr = 0x17B437
    func = idaapi.get_func(func_addr)
    
    if not func:
        print(f"ERROR: Function not found at 0x{func_addr:X}")
        return None
    
    func_name = idc.get_func_name(func_addr)
    print(f"Analyzing function: {func_name} @ 0x{func_addr:X}")
    print(f"Size: {func.end_ea - func.start_ea} bytes")
    print()
    
    # Scan for segment register loads
    segment_loads = []
    buffer_refs = []
    slot_refs = []
    
    ea = func.start_ea
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        disasm = idc.GetDisasm(ea)
        
        # Look for segment loads (mov es, ...)
        if 'mov' in mnem and 'es' in disasm:
            segment_loads.append({
                'addr': ea,
                'offset': ea - func.start_ea,
                'disasm': disasm
            })
        
        # Look for 602Eh references (buffer segment)
        if '602Eh' in disasm or '602E' in disasm:
            buffer_refs.append({
                'addr': ea,
                'offset': ea - func.start_ea,
                'disasm': disasm
            })
        
        # Look for dword_79D3E references
        if 'dword_79D3E' in disasm or '79D3E' in disasm:
            slot_refs.append({
                'addr': ea,
                'offset': ea - func.start_ea,
                'disasm': disasm
            })
        
        ea = idc.next_head(ea, func.end_ea)
    
    print(f"Found {len(segment_loads)} segment loads")
    print(f"Found {len(buffer_refs)} buffer references")
    print(f"Found {len(slot_refs)} mission slot references")
    print()
    
    # Show buffer references
    print("FILE BUFFER REFERENCES (0x602E segment):")
    print("-" * 80)
    for ref in buffer_refs[:20]:  # Show first 20
        print(f"  +0x{ref['offset']:04X} @ 0x{ref['addr']:06X}: {ref['disasm']}")
    print()
    
    # Show mission slot references
    print("MISSION SLOT ARRAY REFERENCES (dword_79D3E):")
    print("-" * 80)
    for ref in slot_refs[:20]:
        print(f"  +0x{ref['offset']:04X} @ 0x{ref['addr']:06X}: {ref['disasm']}")
    print()
    
    # Look for loops that might be copying data
    print("POTENTIAL COPY LOOPS (has both references nearby):")
    print("-" * 80)
    
    for buf_ref in buffer_refs:
        # Look for slot ref within 100 bytes
        for slot_ref in slot_refs:
            if abs(buf_ref['offset'] - slot_ref['offset']) < 100:
                print(f"Buffer @ +0x{buf_ref['offset']:04X}:")
                print(f"  {buf_ref['disasm']}")
                print(f"Slot @ +0x{slot_ref['offset']:04X}:")
                print(f"  {slot_ref['disasm']}")
                print(f"Distance: {abs(buf_ref['offset'] - slot_ref['offset'])} bytes")
                print()
    
    return {
        'segment_loads': segment_loads,
        'buffer_refs': buffer_refs,
        'slot_refs': slot_refs
    }

def main():
    print("Starting file buffer copy analysis...")
    idaapi.auto_wait()
    
    result = find_buffer_and_slot_refs()
    
    if result:
        output_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\file_buffer_copy.json'
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nResults written to {output_path}")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
