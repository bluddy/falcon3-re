"""
Extract disassembly after file read operation to find parsing code
Focus on offset +0x713 and beyond in squadron_mission_file_loader
"""

import idaapi
import idc
import idautils

def extract_post_read_code():
    """Extract code after file read to find mission data parsing"""
    
    func_addr = 0x17B437
    func = idaapi.get_func(func_addr)
    
    if not func:
        print(f"ERROR: Function not found at 0x{func_addr:X}")
        return
    
    # File read happens at offset +0x713 (address 0x17BB4A)
    read_addr = func_addr + 0x713
    
    # Extract 500 instructions after the read
    output_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\disassembly\post_file_read_code.txt'
    
    with open(output_path, 'w') as f:
        f.write(f"POST FILE READ CODE ANALYSIS\n")
        f.write(f"Function: {idc.get_func_name(func_addr)} @ 0x{func_addr:X}\n")
        f.write(f"File read at: 0x{read_addr:X} (offset +0x713)\n")
        f.write("=" * 80 + "\n\n")
        
        ea = read_addr
        count = 0
        max_instructions = 500
        
        while ea < func.end_ea and count < max_instructions:
            offset = ea - func_addr
            mnem = idc.print_insn_mnem(ea)
            disasm = idc.GetDisasm(ea)
            comment = idc.get_cmt(ea, 0) or idc.get_cmt(ea, 1) or ""
            
            # Format output
            f.write(f"+0x{offset:04X} | 0x{ea:06X} | {disasm}")
            if comment:
                f.write(f"  ; {comment}")
            f.write("\n")
            
            # Annotate key operations
            if 'dword_79D3E' in disasm:
                f.write("      *** MISSION SLOT ARRAY ACCESS ***\n")
            
            if 'loop' in mnem or 'jmp' in mnem:
                # Calculate jump target
                if idc.get_operand_type(ea, 0) == idc.o_near:
                    target = idc.get_operand_value(ea, 0)
                    target_offset = target - func_addr
                    f.write(f"      --> Jump to +0x{target_offset:04X}\n")
            
            if mnem in ['mov', 'lea'] and '602E' in disasm:
                f.write("      *** FILE BUFFER ACCESS ***\n")
            
            if mnem == 'call':
                target = idc.get_operand_value(ea, 0)
                target_name = idc.get_func_name(target)
                if target_name:
                    f.write(f"      --> Calls {target_name} @ 0x{target:X}\n")
            
            ea = idc.next_head(ea, func.end_ea)
            count += 1
        
        f.write(f"\n\nExtracted {count} instructions\n")
    
    print(f"Extracted {count} instructions to {output_path}")

def main():
    print("Starting post-file-read code extraction...")
    idaapi.auto_wait()
    extract_post_read_code()
    idc.qexit(0)

if __name__ == '__main__':
    main()
