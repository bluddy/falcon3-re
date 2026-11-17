import idaapi
import idc
import idautils

def disassemble_function(func_addr, func_name, output_file):
    """
    Disassemble a function and save to file with detailed annotations.
    """
    print(f"[*] Disassembling {func_name} @ 0x{func_addr:X}...")
    
    func_end = idc.get_func_attr(func_addr, idc.FUNCATTR_END)
    if func_end == idc.BADADDR:
        print(f"[-] Function not found at 0x{func_addr:X}")
        return False
    
    func_size = func_end - func_addr
    
    with open(output_file, 'w') as f:
        # Header
        f.write("="*80 + "\n")
        f.write(f"{func_name} Disassembly\n")
        f.write("="*80 + "\n")
        f.write(f"Address: 0x{func_addr:X}\n")
        f.write(f"Size: {func_size} bytes (0x{func_size:X})\n")
        f.write(f"Segment: {idc.get_segm_name(func_addr)}\n")
        f.write("="*80 + "\n\n")
        
        # Disassembly with line numbers
        line_num = 0
        for head in idautils.Heads(func_addr, func_end):
            # Get offset from function start
            offset = head - func_addr
            
            # Get disassembly
            disasm = idc.generate_disasm_line(head, 0)
            
            # Get any comments
            comment = idc.get_cmt(head, 0)  # Regular comment
            if not comment:
                comment = idc.get_cmt(head, 1)  # Repeatable comment
            
            # Format line
            line = f"{line_num:4d} | +0x{offset:04X} | 0x{head:06X} | {disasm}"
            
            if comment:
                line += f"  ; {comment}"
            
            f.write(line + "\n")
            line_num += 1
        
        # Summary
        f.write("\n" + "="*80 + "\n")
        f.write(f"Total instructions: {line_num}\n")
        f.write("="*80 + "\n")
    
    print(f"[+] Saved {line_num} instructions to {output_file}")
    return True

def find_graphics_calls(func_addr):
    """
    Find calls to graphics functions within a function.
    """
    results = {
        "function_calls": [],
        "far_calls": [],
        "indirect_calls": []
    }
    
    func_end = idc.get_func_attr(func_addr, idc.FUNCATTR_END)
    if func_end == idc.BADADDR:
        return results
    
    for head in idautils.Heads(func_addr, func_end):
        disasm = idc.generate_disasm_line(head, 0)
        
        # Look for call instructions
        if "call" in disasm.lower():
            # Get target
            target = None
            if "far" in disasm.lower():
                results["far_calls"].append({
                    "addr": hex(head),
                    "disasm": disasm
                })
            elif "[" in disasm or "ptr" in disasm.lower():
                results["indirect_calls"].append({
                    "addr": hex(head),
                    "disasm": disasm
                })
            else:
                # Direct call - try to get target name
                target_addr = idc.get_operand_value(head, 0)
                target_name = idc.get_func_name(target_addr)
                
                results["function_calls"].append({
                    "addr": hex(head),
                    "offset": hex(head - func_addr),
                    "target": hex(target_addr) if target_addr else "unknown",
                    "target_name": target_name if target_name else "sub_" + hex(target_addr)[2:].upper(),
                    "disasm": disasm
                })
    
    return results

def main():
    print("="*80)
    print("Map Display Functions Disassembly")
    print("="*80)
    
    # Functions to disassemble (from mission editor analysis)
    functions = [
        ("waypoint_coordinate_processor", 0x1A2441),
        ("waypoint_display_processor", 0x1A0F10),
        ("waypoint_display_helper", 0x1A163A),
        ("tactical_screen_coordinator", 0x12DB6A)
    ]
    
    output_dir = r"C:\Users\ybarnoy\projects\falcon3\analysis\disassembly"
    
    for func_name, func_addr in functions:
        print(f"\n{'='*80}")
        print(f"Processing {func_name}")
        print(f"{'='*80}")
        
        # Disassemble
        output_file = f"{output_dir}\\{func_name}_disasm.txt"
        success = disassemble_function(func_addr, func_name, output_file)
        
        if success:
            # Find graphics calls
            print(f"\n[*] Analyzing function calls in {func_name}...")
            calls = find_graphics_calls(func_addr)
            
            print(f"    Direct calls: {len(calls['function_calls'])}")
            print(f"    Far calls: {len(calls['far_calls'])}")
            print(f"    Indirect calls: {len(calls['indirect_calls'])}")
            
            if calls['function_calls']:
                print(f"\n[*] Direct function calls:")
                for call in calls['function_calls'][:10]:  # First 10
                    print(f"    {call['offset']}: {call['target_name']}")
    
    print("\n" + "="*80)
    print("[+] Disassembly complete!")
    print(f"[*] Output files in: {output_dir}")
    print("="*80)

if __name__ == "__main__":
    main()
