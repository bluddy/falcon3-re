"""
Extract full disassembly of squadron_mission_file_loader with annotations
"""

import idaapi
import idc
import idautils

def get_full_disassembly():
    """Get complete disassembly with annotations"""
    
    func_addr = 0x17B437
    func = idaapi.get_func(func_addr)
    
    if not func:
        print(f"ERROR: Function not found at 0x{func_addr:X}")
        return
    
    func_name = idc.get_func_name(func_addr)
    print(f"Extracting {func_name} at 0x{func_addr:X}")
    
    output_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\disassembly\squadron_mission_file_loader_full.txt'
    
    with open(output_path, 'w') as f:
        f.write(f"Function: {func_name}\n")
        f.write(f"Address: 0x{func_addr:X}\n")
        f.write(f"Size: {func.end_ea - func.start_ea} bytes\n")
        f.write("=" * 80 + "\n\n")
        
        ea = func.start_ea
        line_num = 0
        
        while ea < func.end_ea:
            line_num += 1
            
            # Get disassembly
            disasm = idc.GetDisasm(ea)
            
            # Get operands
            mnem = idc.print_insn_mnem(ea)
            op0 = idc.print_operand(ea, 0)
            op1 = idc.print_operand(ea, 1)
            
            # Get any comment
            comment = idc.get_cmt(ea, 0) or idc.get_cmt(ea, 1)
            
            # Format output
            offset = ea - func.start_ea
            f.write(f"{line_num:4d} | +0x{offset:04X} | 0x{ea:06X} | {disasm}")
            
            if comment:
                f.write(f"  ; {comment}")
            
            f.write("\n")
            
            # Add annotations for key operations
            if 'dword_79D3E' in disasm:
                f.write(f"      *** MISSION SLOT ARRAY POINTER ACCESS ***\n")
            
            if mnem in ['mov', 'lea'] and '[' in op0 and 'es:[bx' in op0:
                f.write(f"      *** POTENTIAL MISSION SLOT FIELD WRITE: {op0} = {op1} ***\n")
            
            ea = idc.next_head(ea, func.end_ea)
        
        f.write(f"\n\nTotal instructions: {line_num}\n")
    
    print(f"Disassembly written to {output_path}")
    print(f"Total instructions: {line_num}")

def main():
    print("Starting full disassembly extraction...")
    idaapi.auto_wait()
    get_full_disassembly()
    idc.qexit(0)

if __name__ == '__main__':
    main()
