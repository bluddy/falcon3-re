"""
Export the damage bit manipulation logic from flight_physics_integration_engine.

This function (0x4113C) accesses entity[0xCA] with multiple bitmasks.
Goal: Extract the complete logic to understand bit-to-subsystem mapping.
"""

import idc
import idaapi
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\damage_bit_logic.txt"
JSON_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\damage_bit_logic.json"

def export_function_with_0xCA_highlights(func_addr):
    """Export function disassembly highlighting 0xCA accesses."""
    func = idaapi.get_func(func_addr)
    if not func:
        return None
    
    func_name = idc.get_func_name(func_addr)
    lines = []
    bit_operations = []
    
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.GetDisasm(ea)
        offset_hex = f"+{ea - func.start_ea:04X}"
        
        # Highlight 0xCA accesses
        if "+0CAh]" in disasm or "+0CA]" in disasm:
            marker = " <-- DAMAGE STATUS BITFIELD"
            
            # Extract bitmask if present
            mnem = idc.print_insn_mnem(ea)
            if mnem in ["test", "and", "or", "xor"]:
                op2 = idc.print_operand(ea, 1)
                
                bit_operations.append({
                    'offset': offset_hex,
                    'address': hex(ea),
                    'operation': mnem.upper(),
                    'instruction': disasm,
                    'bitmask': op2
                })
        else:
            marker = ""
        
        lines.append(f"{ea:08X} {offset_hex}:  {disasm}{marker}")
        ea = idc.next_head(ea, func.end_ea)
    
    return {
        'name': func_name,
        'address': hex(func.start_ea),
        'size': func.end_ea - func.start_ea,
        'disasm_lines': lines,
        'bit_operations': bit_operations
    }

def main():
    try:
        print("Waiting for auto-analysis...")
        idaapi.auto_wait()
        print("Auto-analysis complete")
        
        func_addr = 0x4113C  # flight_physics_integration_engine
        
        print(f"\nExporting function @ {hex(func_addr)}...")
        result = export_function_with_0xCA_highlights(func_addr)
        
        if not result:
            print("ERROR: Function not found")
            idc.qexit(1)
            return
        
        print(f"Function: {result['name']}")
        print(f"Size: {result['size']} bytes")
        print(f"Bit operations found: {len(result['bit_operations'])}")
        
        # Write text output
        with open(OUTPUT_FILE, 'w') as f:
            f.write(f"; {result['name']}\n")
            f.write(f"; Address: {result['address']}\n")
            f.write(f"; Size: {result['size']} bytes\n")
            f.write(f"; Bit operations on entity[0xCA]: {len(result['bit_operations'])}\n")
            f.write("\n")
            
            for line in result['disasm_lines']:
                f.write(line + "\n")
            
            f.write("\n\n")
            f.write("=" * 80 + "\n")
            f.write("DAMAGE BITFIELD OPERATIONS SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            
            for op in result['bit_operations']:
                f.write(f"@ {op['address']} ({op['offset']}):\n")
                f.write(f"  {op['instruction']}\n")
                f.write(f"  Operation: {op['operation']}, Bitmask: {op['bitmask']}\n\n")
        
        # Write JSON output
        with open(JSON_FILE, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\nText output: {OUTPUT_FILE}")
        print(f"JSON output: {JSON_FILE}")
        print("\nDone!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
