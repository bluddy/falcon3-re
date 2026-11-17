"""
Analyze radar detection logic - find where entity+0x79 bit 0 is set.
Also look for azimuth/elevation/range checks.
"""

import idc
import idaapi
import idautils

def main():
    print("Waiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete")
    
    # Functions of interest
    functions = [
        (0x4EAF8, 'ems_entity_slot_script'),
        (0x131A33, 'sub_131A33'),
    ]
    
    output_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\detection_logic_disasm.txt"
    
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
            f.write(f"Function: {actual_name}\n")
            f.write(f"Address: 0x{func.start_ea:X} - 0x{func.end_ea:X}\n")
            f.write(f"Size: {func.end_ea - func.start_ea} bytes\n")
            f.write(f"{'='*70}\n\n")
            
            # Export disassembly
            ea = func.start_ea
            line_count = 0
            while ea < func.end_ea and line_count < 200:
                disasm = idc.generate_disasm_line(ea, 0)
                
                marker = ""
                if '+74h]' in disasm or '+79h]' in disasm:
                    marker = " <-- ENTITY FLAG"
                
                f.write(f"0x{ea:X}:  {disasm}{marker}\n")
                ea = idc.next_head(ea, func.end_ea)
                line_count += 1
            
            if line_count >= 200:
                f.write(f"... (truncated)\n")
            
            f.write("\n")
            print(f"Exported {actual_name}")
    
    print(f"Results saved to: {output_path}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
