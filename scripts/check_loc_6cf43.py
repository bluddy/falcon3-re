"""
Check what's at loc_6CF43 - the supposed STT handler target.
"""

import idc
import idaapi
import idautils

def main():
    print("Waiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete")
    
    # Check the target of the jump
    target_ea = 0x6CF43
    
    func = idaapi.get_func(target_ea)
    if func:
        func_name = idc.get_func_name(func.start_ea)
        print(f"Address 0x{target_ea:X} is inside function: {func_name}")
        print(f"Function starts at: 0x{func.start_ea:X}")
        print(f"Function size: {func.end_ea - func.start_ea} bytes")
        
        # Export 50 instructions around the target
        output_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\loc_6cf43_context.txt"
        with open(output_path, 'w') as f:
            f.write(f"Context around loc_6CF43 (target of sub_2C12B jump)\n")
            f.write(f"Function: {func_name} at 0x{func.start_ea:X}\n")
            f.write(f"{'='*70}\n\n")
            
            # Start 20 instructions before target
            ea = target_ea
            for _ in range(20):
                ea = idc.prev_head(ea, func.start_ea)
            
            # Print 50 instructions
            for i in range(50):
                marker = " >>> " if ea == target_ea else "     "
                disasm = idc.generate_disasm_line(ea, 0)
                f.write(f"{marker}0x{ea:X}:  {disasm}\n")
                ea = idc.next_head(ea, func.end_ea)
                if ea >= func.end_ea:
                    break
        
        print(f"Context saved to: {output_path}")
    else:
        print(f"No function found at 0x{target_ea:X}")
    
    # Also check tail_bridge_overlay_load
    print("\nChecking tail_bridge_overlay_load...")
    for func_ea in idautils.Functions():
        name = idc.get_func_name(func_ea)
        if name and 'tail_bridge' in name.lower():
            print(f"Found: {name} at 0x{func_ea:X}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
