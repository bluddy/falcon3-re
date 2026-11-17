"""
Export disassembly of r06_mode_step_dispatch - the F5/F6/F7 key handler.
Follows IDA_AUTOMATION_GUIDE.md pattern.
"""

import idc
import idaapi
import idautils

def main():
    print("Waiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete")
    
    # Function addresses from xref analysis
    functions = [
        (0x6CDA8, 'r06_mode_step_dispatch'),
        (0x2C12B, 'sub_2C12B_mode5_handler'),
        (0x39D02, 'undoc_39D02_display_update'),
        (0x484C1, 'record_script_coord_entry'),
    ]
    
    output_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\radar_key_handlers.txt"
    
    with open(output_path, 'w') as f:
        for func_addr, expected_name in functions:
            actual_name = idc.get_func_name(func_addr)
            func = idaapi.get_func(func_addr)
            
            if not func:
                f.write(f"\n{'='*70}\n")
                f.write(f"ERROR: No function at 0x{func_addr:X} ({expected_name})\n")
                f.write(f"{'='*70}\n\n")
                continue
            
            f.write(f"\n{'='*70}\n")
            f.write(f"Function: {actual_name} (expected: {expected_name})\n")
            f.write(f"Address: 0x{func.start_ea:X} - 0x{func.end_ea:X}\n")
            f.write(f"Size: {func.end_ea - func.start_ea} bytes\n")
            f.write(f"{'='*70}\n\n")
            
            ea = func.start_ea
            while ea < func.end_ea:
                disasm = idc.generate_disasm_line(ea, 0)
                f.write(f"0x{ea:X}:  {disasm}\n")
                ea = idc.next_head(ea, func.end_ea)
            
            f.write("\n")
            
            print(f"Exported {actual_name}: {func.end_ea - func.start_ea} bytes")
    
    print(f"\nAll disassemblies saved to: {output_path}")
    
    # CRITICAL: Exit explicitly
    idc.qexit(0)

if __name__ == "__main__":
    main()
