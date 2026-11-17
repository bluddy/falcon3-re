"""
Disassemble the radar detection functions that set entity+0x79 bit 0.
"""

import idc
import idaapi

def main():
    print("Waiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete")
    
    # Functions that SET the RADAR_VISIBLE flag (OR operations)
    functions = [
        (0x3A9B7, 'farobj_floor_match_dispatch'),  # Has OR at 0x3AA10
        (0x3AA7E, 'bound_range_check_4aad'),       # Has OR at 0x3AB15
    ]
    
    output_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\radar_detection_functions.txt"
    
    with open(output_path, 'w') as f:
        for func_addr, expected_name in functions:
            actual_name = idc.get_func_name(func_addr)
            func = idaapi.get_func(func_addr)
            
            if not func:
                f.write(f"\n{'='*70}\n")
                f.write(f"ERROR: No function at 0x{func_addr:X}\n")
                f.write(f"{'='*70}\n\n")
                continue
            
            f.write(f"\n{'='*70}\n")
            f.write(f"Function: {actual_name}\n")
            f.write(f"Address: 0x{func.start_ea:X} - 0x{func.end_ea:X}\n")
            f.write(f"Size: {func.end_ea - func.start_ea} bytes\n")
            f.write(f"{'='*70}\n\n")
            
            # Full disassembly
            ea = func.start_ea
            while ea < func.end_ea:
                disasm = idc.generate_disasm_line(ea, 0)
                
                # Highlight interesting lines
                marker = ""
                if '+79h]' in disasm:
                    marker = " <-- RADAR_VISIBLE FLAG"
                elif '+74h]' in disasm:
                    marker = " <-- STATUS FLAGS"
                elif 'rand' in disasm.lower() or 'rng' in disasm.lower():
                    marker = " <-- RANDOM"
                elif 'cmp' in disasm and ('range' in disasm.lower() or 'distance' in disasm.lower()):
                    marker = " <-- RANGE CHECK"
                
                f.write(f"0x{ea:X}:  {disasm}{marker}\n")
                ea = idc.next_head(ea, func.end_ea)
            
            f.write("\n")
            print(f"Exported {actual_name}: {func.end_ea - func.start_ea} bytes")
    
    print(f"\nResults saved to: {output_path}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
