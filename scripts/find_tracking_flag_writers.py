"""
Find all functions that WRITE to entity+0x79 (tracking_flags / RADAR_VISIBLE).
This should reveal the detection probability logic.
"""

import idc
import idaapi
import idautils
import json

def main():
    print("Waiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete")
    
    results = {
        'writers': [],
        'or_operations': [],
        'and_operations': [],
        'mov_operations': []
    }
    
    print("Scanning for entity+0x79 WRITE operations...")
    
    func_count = 0
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
            
        func_name = idc.get_func_name(func_ea)
        writes = []
        
        ea = func.start_ea
        while ea < func.end_ea:
            disasm = idc.generate_disasm_line(ea, 0)
            mnem = idc.print_insn_mnem(ea)
            
            # Look for writes to [reg+79h]
            if '+79h]' in disasm and 'es:' in disasm:
                # Check if destination (op0) is the memory location
                op0 = idc.print_operand(ea, 0)
                op1 = idc.print_operand(ea, 1)
                
                # Write operations: destination is memory
                if '[' in op0 and '+79h' in op0:
                    operation_type = None
                    if mnem == 'mov':
                        operation_type = 'mov'
                    elif mnem == 'or':
                        operation_type = 'or'  # Sets bits
                    elif mnem == 'and':
                        operation_type = 'and'  # Clears bits
                    elif mnem == 'xor':
                        operation_type = 'xor'
                    
                    if operation_type:
                        writes.append({
                            'addr': hex(ea),
                            'mnem': mnem,
                            'operation': operation_type,
                            'disasm': disasm,
                            'operand': op1  # What's being written
                        })
            
            ea = idc.next_head(ea, func.end_ea)
        
        if writes:
            func_count += 1
            entry = {
                'func_name': func_name,
                'func_addr': hex(func_ea),
                'operations': writes
            }
            
            results['writers'].append(entry)
            
            # Categorize by operation type
            for w in writes:
                if w['operation'] == 'or':
                    results['or_operations'].append(entry)
                elif w['operation'] == 'and':
                    results['and_operations'].append(entry)
                elif w['operation'] == 'mov':
                    results['mov_operations'].append(entry)
            
            # Print first 30 functions
            if func_count <= 30:
                print(f"\n{func_count}. {func_name} at {hex(func_ea)}")
                for w in writes:
                    print(f"   {w['addr']}: {w['mnem']:6s} {w['disasm']}")
    
    print(f"\n\nTotal functions writing to entity+0x79: {func_count}")
    print(f"  OR operations (set bits): {len(results['or_operations'])}")
    print(f"  AND operations (clear bits): {len(results['and_operations'])}")
    print(f"  MOV operations (direct write): {len(results['mov_operations'])}")
    
    # Save results
    output_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\tracking_flag_writers.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
