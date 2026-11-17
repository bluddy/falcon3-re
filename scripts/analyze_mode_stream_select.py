"""
Analyze mode_stream_select_step function (0x39E62 or nearby) - F6 key handler
This should help understand radar mode switching logic
"""

import idaapi
import idc
import idautils

# Initialize IDA if needed
idaapi.auto_wait()

def analyze_mode_stream_function():
    # The function address from F6 handler search
    # Try both the reported address and nearby
    candidates = [0x39E62, 0x39E13, 0x39E00]
    
    func_ea = None
    for addr in candidates:
        if idc.get_func_name(addr):
            func_ea = addr
            print(f"Found function at 0x{addr:X}: {idc.get_func_name(addr)}")
            break
    
    if not func_ea:
        print("Function not found, searching for 'mode_stream' in function names...")
        for func_ea in idautils.Functions():
            name = idc.get_func_name(func_ea)
            if name and 'mode' in name.lower() and 'stream' in name.lower():
                print(f"Found: 0x{func_ea:X} - {name}")
        return
    
    print(f"\n=== Analyzing {idc.get_func_name(func_ea)} at 0x{func_ea:X} ===\n")
    
    func = idaapi.get_func(func_ea)
    if not func:
        print("Could not get function bounds")
        return
    
    print(f"Function size: {func.end_ea - func.start_ea} bytes")
    print(f"Range: 0x{func.start_ea:X} - 0x{func.end_ea:X}\n")
    
    # Save full disassembly
    output_file = r"C:\Users\ybarnoy\projects\falcon3\analysis\mode_stream_select_disasm.txt"
    with open(output_file, 'w') as f:
        f.write(f"=== {idc.get_func_name(func_ea)} at 0x{func_ea:X} ===\n")
        f.write(f"Size: {func.end_ea - func.start_ea} bytes\n\n")
        
        ea = func.start_ea
        while ea < func.end_ea:
            disasm = idc.generate_disasm_line(ea, 0)
            f.write(f"0x{ea:X}: {disasm}\n")
            ea = idc.next_head(ea)
    
    print(f"Full disassembly saved to: {output_file}\n")
    
    # Analyze data references
    print("=== Data References ===")
    data_refs = set()
    ea = func.start_ea
    while ea < func.end_ea:
        # Check for data references
        for ref in idautils.DataRefsFrom(ea):
            if ref not in data_refs:
                data_refs.add(ref)
                name = idc.get_name(ref)
                if not name:
                    name = f"data_{ref:X}"
                
                # Try to get type/value
                val = idc.get_wide_byte(ref)
                size = idc.get_item_size(ref)
                
                print(f"  0x{ref:X}: {name} (size={size}, byte_val=0x{val:02X})")
        
        ea = idc.next_head(ea)
    
    # Analyze mode checks
    print("\n=== Mode Value Checks ===")
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        mnem = idc.print_insn_mnem(ea)
        
        # Look for comparisons
        if mnem == 'cmp':
            op1 = idc.print_operand(ea, 0)
            op2 = idc.print_operand(ea, 1)
            print(f"  0x{ea:X}: {disasm}")
            
            # Check what happens after the comparison
            next_ea = idc.next_head(ea)
            next_disasm = idc.generate_disasm_line(next_ea, 0)
            print(f"           -> {next_disasm}")
        
        ea = idc.next_head(ea)
    
    # Analyze entity field accesses
    print("\n=== Entity Field Accesses ===")
    ea = func.start_ea
    entity_fields = {}
    
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        
        # Look for [di+offset] or [edi+offset] patterns
        if '[di+' in disasm.lower() or '[edi+' in disasm.lower():
            # Extract offset
            import re
            match = re.search(r'\[e?di\+([0-9A-Fa-f]+)h?\]', disasm)
            if match:
                offset = int(match.group(1), 16)
                if offset not in entity_fields:
                    entity_fields[offset] = []
                entity_fields[offset].append((ea, disasm))
    
    if entity_fields:
        for offset in sorted(entity_fields.keys()):
            print(f"\n  Offset +0x{offset:X}:")
            for ea, disasm in entity_fields[offset]:
                print(f"    0x{ea:X}: {disasm}")
    
    # Analyze loops
    print("\n=== Loop Analysis ===")
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        mnem = idc.print_insn_mnem(ea)
        
        # Look for loop instructions or backward jumps
        if mnem in ['loop', 'jmp', 'jnz', 'jz', 'jl', 'jg', 'jle', 'jge', 'jb', 'ja', 'jbe', 'jae']:
            target = idc.get_operand_value(ea, 0)
            if target < ea:  # Backward jump = loop
                print(f"  0x{ea:X}: {disasm} (backward jump - loop?)")
        
        ea = idc.next_head(ea)
    
    print("\n=== Analysis Complete ===")

if __name__ == '__main__':
    analyze_mode_stream_function()
