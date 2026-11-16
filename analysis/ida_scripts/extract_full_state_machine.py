"""
Extract complete disassembly of r57_menu_state_machine function.
Run this in IDA Pro with FALCONCD.EXE loaded.
"""

import idaapi
import idc
import idautils
import json

def get_function_disassembly_full(ea):
    """Get complete disassembly of a function with all instructions."""
    func = idaapi.get_func(ea)
    if not func:
        return None
    
    disasm_lines = []
    insn_count = 0
    
    # Iterate through all addresses in the function
    addr = func.start_ea
    while addr < func.end_ea:
        # Get disassembly line
        disasm = idc.GetDisasm(addr)
        addr_hex = "%08X" % addr
        line = f"{addr_hex}  {disasm}"
        disasm_lines.append(line)
        
        insn_count += 1
        
        # Move to next instruction
        next_addr = idc.next_head(addr, func.end_ea)
        if next_addr == idc.BADADDR or next_addr <= addr:
            break
        addr = next_addr
    
    return {
        'lines': disasm_lines,
        'instruction_count': insn_count,
        'start': func.start_ea,
        'end': func.end_ea,
        'size': func.end_ea - func.start_ea
    }

def find_function_by_name(name):
    """Find function address by name."""
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        if func_name == name:
            return func_ea
    return None

def main():
    print("="*80)
    print("EXTRACTING COMPLETE r57_menu_state_machine DISASSEMBLY")
    print("="*80)
    
    # Find the function
    func_name = "r57_menu_state_machine"
    func_ea = find_function_by_name(func_name)
    
    if not func_ea:
        print(f"ERROR: Could not find function '{func_name}'")
        return
    
    print(f"\nFound {func_name} at 0x{func_ea:08X}")
    
    # Get complete disassembly
    result = get_function_disassembly_full(func_ea)
    
    if not result:
        print("ERROR: Could not get function bounds")
        return
    
    print(f"Function size: {result['size']} bytes")
    print(f"Address range: 0x{result['start']:08X} - 0x{result['end']:08X}")
    print(f"Total instructions: {result['instruction_count']}")
    print(f"Disassembly lines: {len(result['lines'])}")
    
    # Save to file
    output_file = "r57_state_machine_full_disasm.txt"
    with open(output_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write(f"Function: {func_name}\n")
        f.write(f"Address: 0x{func_ea:08X}\n")
        f.write(f"Size: {result['size']} bytes\n")
        f.write(f"Instructions: {result['instruction_count']}\n")
        f.write("="*80 + "\n\n")
        
        for i, line in enumerate(result['lines']):
            f.write(f"{i:4d}: {line}\n")
    
    print(f"\nSaved complete disassembly to: {output_file}")
    
    # Also save as JSON
    json_file = "r57_state_machine_full_disasm.json"
    json_data = {
        'function': func_name,
        'address': hex(func_ea),
        'size': result['size'],
        'start': hex(result['start']),
        'end': hex(result['end']),
        'instruction_count': result['instruction_count'],
        'disassembly': result['lines']
    }
    
    with open(json_file, 'w') as f:
        json.dump(json_data, f, indent=2)
    
    print(f"Saved JSON data to: {json_file}")
    
    # Print first 50 and last 50 lines as verification
    print("\n" + "="*80)
    print("VERIFICATION - First 50 lines:")
    print("="*80)
    for i, line in enumerate(result['lines'][:50]):
        print(f"{i:4d}: {line}")
    
    print("\n" + "="*80)
    print(f"VERIFICATION - Last 50 lines:")
    print("="*80)
    start_idx = max(0, len(result['lines']) - 50)
    for i in range(start_idx, len(result['lines'])):
        print(f"{i:4d}: {result['lines'][i]}")
    
    print("\n" + "="*80)
    print("EXTRACTION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
