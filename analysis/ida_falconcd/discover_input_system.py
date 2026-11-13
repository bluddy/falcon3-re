"""
Falcon 3.0 Input System Discovery Script
Discovers and categorizes all input-related functions
"""

import idc
import idaapi
import idautils
import json

def find_input_functions():
    """Find all functions related to input handling"""
    
    input_patterns = [
        'joy', 'stick', 'key', 'kbd', 'input', 'button', 'control',
        'mouse', 'axis', 'calibrat', 'poll', 'read', 'scan'
    ]
    
    # Also search for BIOS interrupt handlers
    bios_patterns = ['int_16', 'int_33', 'bios']  # INT 16h keyboard, INT 33h mouse
    
    results = {
        'joystick_functions': [],
        'keyboard_functions': [],
        'mouse_functions': [],
        'control_mapping': [],
        'calibration': [],
        'polling': [],
        'unknown_input': []
    }
    
    print("=" * 80)
    print("FALCON 3.0 INPUT SYSTEM DISCOVERY")
    print("=" * 80)
    
    # Search all functions
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        if not func_name:
            continue
            
        name_lower = func_name.lower()
        
        # Categorize by name patterns
        categorized = False
        
        if any(p in name_lower for p in ['joy', 'stick']):
            results['joystick_functions'].append({
                'address': hex(func_ea),
                'name': func_name,
                'size': idc.get_func_attr(func_ea, idc.FUNCATTR_END) - func_ea
            })
            categorized = True
            
        if any(p in name_lower for p in ['key', 'kbd', 'scan']):
            results['keyboard_functions'].append({
                'address': hex(func_ea),
                'name': func_name,
                'size': idc.get_func_attr(func_ea, idc.FUNCATTR_END) - func_ea
            })
            categorized = True
            
        if 'mouse' in name_lower:
            results['mouse_functions'].append({
                'address': hex(func_ea),
                'name': func_name,
                'size': idc.get_func_attr(func_ea, idc.FUNCATTR_END) - func_ea
            })
            categorized = True
            
        if any(p in name_lower for p in ['calibrat', 'calibr']):
            results['calibration'].append({
                'address': hex(func_ea),
                'name': func_name,
                'size': idc.get_func_attr(func_ea, idc.FUNCATTR_END) - func_ea
            })
            categorized = True
            
        if any(p in name_lower for p in ['poll', 'read', 'input']) and not categorized:
            results['polling'].append({
                'address': hex(func_ea),
                'name': func_name,
                'size': idc.get_func_attr(func_ea, idc.FUNCATTR_END) - func_ea
            })
            categorized = True
            
        if any(p in name_lower for p in ['control', 'map', 'bind']) and not categorized:
            results['control_mapping'].append({
                'address': hex(func_ea),
                'name': func_name,
                'size': idc.get_func_attr(func_ea, idc.FUNCATTR_END) - func_ea
            })
            categorized = True
    
    # Search for interrupt handlers
    print("\nSearching for BIOS interrupt handlers...")
    for seg_ea in idautils.Segments():
        for head in idautils.Heads(seg_ea, idc.get_segm_end(seg_ea)):
            mnem = idc.print_insn_mnem(head)
            if mnem == 'int':
                interrupt_num = idc.get_operand_value(head, 0)
                if interrupt_num == 0x16:  # Keyboard BIOS
                    func_ea = idc.get_func_attr(head, idc.FUNCATTR_START)
                    if func_ea != idc.BADADDR:
                        func_name = idc.get_func_name(func_ea)
                        print(f"  Found INT 16h (keyboard) at {hex(head)} in {func_name}")
                        
                elif interrupt_num == 0x33:  # Mouse BIOS
                    func_ea = idc.get_func_attr(head, idc.FUNCATTR_START)
                    if func_ea != idc.BADADDR:
                        func_name = idc.get_func_name(func_ea)
                        print(f"  Found INT 33h (mouse) at {hex(head)} in {func_name}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY BY CATEGORY")
    print("=" * 80)
    
    total = 0
    for category, functions in results.items():
        count = len(functions)
        total += count
        print(f"\n{category.upper().replace('_', ' ')}: {count} functions")
        for func in sorted(functions, key=lambda x: int(x['address'], 16)):
            print(f"  {func['address']:12s} {func['name']:40s} ({func['size']:4d} bytes)")
    
    print(f"\nTOTAL INPUT FUNCTIONS: {total}")
    
    # Save to JSON
    output_file = 'input_system_discovery.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {output_file}")
    
    return results

def analyze_joystick_ports():
    """Find I/O port access for joystick (typically port 0x201)"""
    print("\n" + "=" * 80)
    print("JOYSTICK PORT I/O ANALYSIS")
    print("=" * 80)
    
    joystick_port = 0x201
    results = []
    
    for seg_ea in idautils.Segments():
        for head in idautils.Heads(seg_ea, idc.get_segm_end(seg_ea)):
            mnem = idc.print_insn_mnem(head)
            
            # Look for IN/OUT instructions
            if mnem in ['in', 'out']:
                port = idc.get_operand_value(head, 1)
                if port == joystick_port:
                    func_ea = idc.get_func_attr(head, idc.FUNCATTR_START)
                    func_name = idc.get_func_name(func_ea) if func_ea != idc.BADADDR else "unknown"
                    disasm = idc.GetDisasm(head)
                    
                    results.append({
                        'address': hex(head),
                        'function': func_name,
                        'instruction': disasm
                    })
                    
                    print(f"  {hex(head):12s} {func_name:40s} {disasm}")
    
    print(f"\nFound {len(results)} joystick port accesses")
    return results

def find_input_data_structures():
    """Find global data structures used for input state"""
    print("\n" + "=" * 80)
    print("INPUT DATA STRUCTURES")
    print("=" * 80)
    
    # Look for commonly named data segments
    data_patterns = ['joy', 'key', 'button', 'axis', 'control', 'input']
    
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        if 'data' in seg_name.lower() or 'bss' in seg_name.lower():
            print(f"\nSearching segment: {seg_name}")
            
            for head in idautils.Heads(seg_ea, idc.get_segm_end(seg_ea)):
                name = idc.get_name(head)
                if name and any(p in name.lower() for p in data_patterns):
                    size = idc.get_item_size(head)
                    print(f"  {hex(head):12s} {name:40s} ({size} bytes)")

if __name__ == '__main__':
    idaapi.auto_wait()
    
    results = find_input_functions()
    analyze_joystick_ports()
    find_input_data_structures()
    
    print("\n" + "=" * 80)
    print("INPUT SYSTEM DISCOVERY COMPLETE")
    print("=" * 80)
