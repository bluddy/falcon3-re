"""
Find weapon lock and fire control code.
Search for:
- IR lock logic (heat-seeking)
- Radar lock integration
- HARM anti-radar logic
- Fire button handlers
- Lock tone/indication
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
        'fire_functions': [],
        'lock_functions': [],
        'weapon_type_checks': [],
        'target_tracking': []
    }
    
    # Search for functions with relevant names
    keywords = [
        'fire', 'launch', 'weapon', 'missile', 'lock', 'track',
        'aim', 'sidewinder', 'amraam', 'harm', 'gun', 'bullet'
    ]
    
    print("Searching for weapon-related functions...")
    
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        if not func_name:
            continue
        
        name_lower = func_name.lower()
        for keyword in keywords:
            if keyword in name_lower:
                func = idaapi.get_func(func_ea)
                if func:
                    results['fire_functions'].append({
                        'addr': hex(func_ea),
                        'name': func_name,
                        'size': func.end_ea - func.start_ea,
                        'keyword': keyword
                    })
                    print(f"  Found: {func_name} at {hex(func_ea)} (keyword: {keyword})")
                break
    
    # Also search for specific weapon type constants (0x12, 0x13, 0x33-0x37)
    print("\nSearching for weapon type comparisons...")
    
    type_count = 0
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        func_name = idc.get_func_name(func_ea)
        type_checks = []
        
        ea = func.start_ea
        while ea < func.end_ea:
            mnem = idc.print_insn_mnem(ea)
            
            # Look for cmp with weapon type constants
            if mnem == 'cmp':
                op1 = idc.print_operand(ea, 1)
                # Check for weapon type constants
                if op1 in ['12h', '13h', '33h', '34h', '35h', '36h', '37h']:
                    disasm = idc.generate_disasm_line(ea, 0)
                    type_checks.append({
                        'addr': hex(ea),
                        'type': op1,
                        'disasm': disasm
                    })
            
            ea = idc.next_head(ea, func.end_ea)
        
        if type_checks:
            type_count += 1
            results['weapon_type_checks'].append({
                'func': func_name,
                'addr': hex(func_ea),
                'checks': type_checks
            })
            
            if type_count <= 20:
                print(f"  {func_name}: {len(type_checks)} weapon type checks")
    
    print(f"\nTotal functions with weapon keywords: {len(results['fire_functions'])}")
    print(f"Total functions with type checks: {len(results['weapon_type_checks'])}")
    
    # Save results
    output_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\weapon_lock_search.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
