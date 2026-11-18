"""
Extract weapon category hash calculation constants from fixed_vec3_accumulate_a.
Reads the exact scale factors and divisors to calculate weapon categories.
"""

import idaapi
import idc
import idautils

def extract_constants():
    """Extract scale factors and divisors from fixed_vec3_accumulate_a"""
    
    print("=" * 70)
    print("EXTRACTING WEAPON HASH CALCULATION CONSTANTS")
    print("=" * 70)
    print()
    
    # Function address
    func_addr = 0x22C91
    
    print(f"Function: fixed_vec3_accumulate_a @ 0x{func_addr:X}")
    print()
    
    # Scale factor addresses (from MOV AX, cs:xxx then MUL cs:yyy)
    scale_x_addr = None
    scale_y_addr = None
    scale_z_addr = None
    
    div_x_addr = None
    div_y_addr = None
    div_z_addr = None
    
    # Parse the function instruction by instruction
    addr = func_addr
    end_addr = func_addr + 68  # 68 bytes long
    
    print("Parsing function disassembly...")
    print()
    
    component = None
    
    while addr < end_addr:
        mnem = idc.print_insn_mnem(addr)
        op0 = idc.print_operand(addr, 0)
        op1 = idc.print_operand(addr, 1)
        
        # Look for MOV AX, cs:vec3_X_component
        if mnem == "mov" and op0 == "ax" and "vec3_x_component" in op1:
            component = "X"
            print(f"0x{addr:X}: Found X component load")
            
        elif mnem == "mov" and op0 == "ax" and "vec3_y_component" in op1:
            component = "Y"
            print(f"0x{addr:X}: Found Y component load")
            
        elif mnem == "mov" and op0 == "ax" and "vec3_z_component" in op1:
            component = "Z"
            print(f"0x{addr:X}: Found Z component load")
        
        # Look for MUL cs:matrix_scale_X
        elif mnem == "mul" and component:
            # Parse the operand string to extract the address
            # Format is "cs:name" or "cs:offset"
            op_str = idc.print_operand(addr, 0)
            
            # Try to get the referenced address from the operand
            # For memory operands, this gives us the EA (effective address)
            if idc.get_operand_type(addr, 0) == idc.o_mem:
                mem_addr = idc.get_operand_value(addr, 0)
                # For CS segment references, we may need to add segment base
                if mem_addr == 0:
                    # Try parsing from the disassembly
                    disasm = idc.GetDisasm(addr)
                    print(f"0x{addr:X}: {disasm}")
                    # Extract just the multiplier name/addr
                    parts = disasm.split()
                    if len(parts) >= 2:
                        print(f"    Component {component}: {parts[1]}")
            else:
                mem_addr = idc.get_operand_value(addr, 0)
            
            value = idc.get_wide_word(mem_addr) if mem_addr else 0
            
            if component == "X":
                scale_x_addr = mem_addr
                print(f"0x{addr:X}: X scale @ 0x{mem_addr:X} = {value} (0x{value:X})")
            elif component == "Y":
                scale_y_addr = mem_addr
                print(f"0x{addr:X}: Y scale @ 0x{mem_addr:X} = {value} (0x{value:X})")
            elif component == "Z":
                scale_z_addr = mem_addr
                print(f"0x{addr:X}: Z scale @ 0x{mem_addr:X} = {value} (0x{value:X})")
        
        # Look for DIV cs:fixedpoint_divisor_X
        elif mnem == "div" and component:
            # Get the memory address being divided
            if idc.get_operand_type(addr, 0) == idc.o_mem:
                mem_addr = idc.get_operand_value(addr, 0)
                if mem_addr == 0:
                    disasm = idc.GetDisasm(addr)
                    print(f"0x{addr:X}: {disasm}")
                    parts = disasm.split()
                    if len(parts) >= 2:
                        print(f"    Component {component}: {parts[1]}")
            else:
                mem_addr = idc.get_operand_value(addr, 0)
            
            value = idc.get_wide_word(mem_addr) if mem_addr else 0
            
            if component == "X":
                div_x_addr = mem_addr
                print(f"0x{addr:X}: X divisor @ 0x{mem_addr:X} = {value} (0x{value:X})")
            elif component == "Y":
                div_y_addr = mem_addr
                print(f"0x{addr:X}: Y divisor @ 0x{mem_addr:X} = {value} (0x{value:X})")
            elif component == "Z":
                div_z_addr = mem_addr
                print(f"0x{addr:X}: Z divisor @ 0x{mem_addr:X} = {value} (0x{value:X})")
            
            component = None  # Reset for next triplet
        
        addr = idc.next_head(addr)
    
    print()
    print("=" * 70)
    print("CONSTANTS EXTRACTED")
    print("=" * 70)
    print()
    
    # Read the actual values
    if scale_x_addr and scale_y_addr and scale_z_addr:
        scale_x = idc.get_wide_word(scale_x_addr)
        scale_y = idc.get_wide_word(scale_y_addr)
        scale_z = idc.get_wide_word(scale_z_addr)
        
        print(f"Scale factors:")
        print(f"  X: {scale_x:5d} (0x{scale_x:04X}) @ 0x{scale_x_addr:X}")
        print(f"  Y: {scale_y:5d} (0x{scale_y:04X}) @ 0x{scale_y_addr:X}")
        print(f"  Z: {scale_z:5d} (0x{scale_z:04X}) @ 0x{scale_z_addr:X}")
        print()
    
    if div_x_addr and div_y_addr and div_z_addr:
        div_x = idc.get_wide_word(div_x_addr)
        div_y = idc.get_wide_word(div_y_addr)
        div_z = idc.get_wide_word(div_z_addr)
        
        print(f"Divisors:")
        print(f"  X: {div_x:5d} (0x{div_x:04X}) @ 0x{div_x_addr:X}")
        print(f"  Y: {div_y:5d} (0x{div_y:04X}) @ 0x{div_y_addr:X}")
        print(f"  Z: {div_z:5d} (0x{div_z:04X}) @ 0x{div_z_addr:X}")
        print()
    
    print("=" * 70)
    print("HASH FORMULA")
    print("=" * 70)
    print()
    print("category = (field_06 * scale_x / div_x) +")
    print("           (field_08 * scale_y / div_y) +")
    print("           (field_0A * scale_z / div_z)")
    print()
    
    if all([scale_x_addr, scale_y_addr, scale_z_addr, div_x_addr, div_y_addr, div_z_addr]):
        print(f"category = (field_06 * {scale_x} / {div_x}) +")
        print(f"           (field_08 * {scale_y} / {div_y}) +")
        print(f"           (field_0A * {scale_z} / {div_z})")
        print()
    
    return {
        'scale_x': scale_x if scale_x_addr else None,
        'scale_y': scale_y if scale_y_addr else None,
        'scale_z': scale_z if scale_z_addr else None,
        'div_x': div_x if div_x_addr else None,
        'div_y': div_y if div_y_addr else None,
        'div_z': div_z if div_z_addr else None,
    }

def main():
    constants = extract_constants()
    
    # Save to file
    output_path = r"C:\Users\ybarnoy\projects\falcon3\temp\weapon_hash_constants.txt"
    print(f"Saving to: {output_path}")
    
    return constants

if __name__ == "__main__":
    constants = main()
    print()
    print("Done! Constants extracted.")
