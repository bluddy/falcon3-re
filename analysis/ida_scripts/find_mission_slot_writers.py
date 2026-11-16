"""
Find all functions that write to the mission slot array (dword_79D3E)
"""

import idaapi
import idc
import idautils
import json

def find_writers_to_pointer(pointer_name, pointer_addr):
    """Find all functions that dereference and write to a pointer"""
    
    writers = []
    
    # Get all cross-references to the pointer
    print(f"Searching for references to {pointer_name} at 0x{pointer_addr:X}...")
    
    for xref in idautils.XrefsTo(pointer_addr):
        ref_ea = xref.frm
        func = idaapi.get_func(ref_ea)
        
        if not func:
            continue
        
        func_name = idc.get_func_name(func.start_ea)
        
        # Scan the function for es:[bx+offset] writes after loading this pointer
        ea = ref_ea
        search_range = min(ea + 200, func.end_ea)  # Look ahead 200 bytes
        
        found_writes = []
        
        while ea < search_range:
            mnem = idc.print_insn_mnem(ea)
            disasm = idc.GetDisasm(ea)
            
            # Look for mov to es:[bx+offset]
            if mnem == 'mov':
                op0 = idc.print_operand(ea, 0)
                op1 = idc.print_operand(ea, 1)
                
                if 'es:[bx' in op0:
                    found_writes.append({
                        'addr': ea,
                        'disasm': disasm,
                        'dest': op0,
                        'src': op1
                    })
            
            ea = idc.next_head(ea, search_range)
        
        if found_writes or True:  # Record all refs for now
            writers.append({
                'function': func_name,
                'func_addr': func.start_ea,
                'ref_addr': ref_ea,
                'ref_offset': ref_ea - func.start_ea,
                'disasm': idc.GetDisasm(ref_ea),
                'writes': found_writes
            })
    
    return writers

def main():
    print("Starting mission slot writer search...")
    idaapi.auto_wait()
    
    pointer_addr = 0x79D3E
    pointer_name = "dword_79D3E"
    
    writers = find_writers_to_pointer(pointer_name, pointer_addr)
    
    print(f"\nFound {len(writers)} functions accessing {pointer_name}")
    
    # Group by function
    by_function = {}
    for w in writers:
        fname = w['function']
        if fname not in by_function:
            by_function[fname] = []
        by_function[fname].append(w)
    
    result = {
        'pointer': pointer_name,
        'pointer_addr': pointer_addr,
        'total_references': len(writers),
        'functions': []
    }
    
    for fname, refs in sorted(by_function.items()):
        func_data = {
            'name': fname,
            'addr': refs[0]['func_addr'],
            'references': [],
            'total_writes': 0
        }
        
        for ref in refs:
            func_data['references'].append({
                'addr': ref['ref_addr'],
                'offset': ref['ref_offset'],
                'disasm': ref['disasm'],
                'writes': ref['writes']
            })
            func_data['total_writes'] += len(ref['writes'])
        
        result['functions'].append(func_data)
        
        print(f"\n{fname} @ 0x{refs[0]['func_addr']:X}")
        print(f"  {len(refs)} ref(s), {func_data['total_writes']} write(s)")
        
        for ref in refs[:3]:  # Show first 3
            print(f"    +0x{ref['ref_offset']:04X}: {ref['disasm']}")
            for write in ref['writes'][:2]:  # Show first 2 writes
                print(f"      -> {write['disasm']}")
    
    output_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\mission_slot_writers.json'
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n\nResults written to {output_path}")
    idc.qexit(0)

if __name__ == '__main__':
    main()
