"""
Find where entity detection flags are set/cleared.
Looking for writes to entity+0x74 bit 6 and entity+0x79 bit 0.
"""

import idc
import idaapi
import idautils
import json

def main():
    print("Waiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete")
    
    # We need to find where entity flags are modified
    # Entity array is at DS:0x386F in segment 0x54AF (1472 bytes, 16 slots of 92 bytes)
    # But we need to find code that accesses [si+74h] or [di+74h] or [bx+74h] patterns
    
    results = {
        'flag_setters': [],
        'flag_clearers': [],
        'test_operations': []
    }
    
    # Search through code segment for entity field accesses
    # Look for patterns like:
    # - test byte ptr es:[di+74h], 40h  (entity+0x74 bit 6)
    # - test byte ptr es:[di+79h], 1    (entity+0x79 bit 0)
    # - or/and operations on these fields
    
    print("Scanning for entity flag operations...")
    
    func_count = 0
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
            
        func_name = idc.get_func_name(func_ea)
        found_in_func = []
        
        ea = func.start_ea
        while ea < func.end_ea:
            disasm = idc.generate_disasm_line(ea, 0)
            mnem = idc.print_insn_mnem(ea)
            
            # Look for operations on [reg+74h] or [reg+79h]
            if ('+74h]' in disasm or '+79h]' in disasm) and 'es:' in disasm:
                # Check instruction type
                op_type = None
                if mnem in ['or', 'and', 'xor', 'test']:
                    op_type = 'test_or_modify'
                elif mnem == 'mov' and 'es:[' in idc.print_operand(ea, 0):
                    op_type = 'write'
                elif mnem == 'mov' and 'es:[' in idc.print_operand(ea, 1):
                    op_type = 'read'
                
                found_in_func.append({
                    'addr': hex(ea),
                    'mnem': mnem,
                    'disasm': disasm,
                    'type': op_type
                })
            
            ea = idc.next_head(ea, func.end_ea)
        
        if found_in_func:
            func_count += 1
            results['flag_setters'].append({
                'func': func_name,
                'addr': hex(func_ea),
                'operations': found_in_func
            })
            
            if func_count <= 20:  # Print first 20
                print(f"\nFunction: {func_name} at {hex(func_ea)}")
                for op in found_in_func[:3]:  # First 3 ops per func
                    print(f"  {op['addr']}: {op['disasm']}")
    
    print(f"\n\nTotal functions with entity flag access: {func_count}")
    
    # Save results
    output_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\entity_flag_operations.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to: {output_path}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
