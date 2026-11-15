"""
Read the opcode_handler_table correctly.
It's a table of far pointers, indexed by operation code.
"""
import idaapi
import idc

def main():
    idaapi.auto_wait()
    
    # The pointer is at cs:opcode_handler_table
    # From disassembly, that's cs:0x0000C (based on the address 0x0002000C)
    table_addr = 0x0002000C
    
    print("=" * 80)
    print(f"OPCODE HANDLER TABLE @ 0x{table_addr:08X}")
    print("=" * 80)
    print()
    
    # Read table entries (far pointers: offset + segment)
    print(f"{'Op':<4} {'Seg:Off':<12} {'Real Linear':<12} {'IDA Address':<12} {'Function'}")
    print("-" * 80)
    
    for op in range(20):  # Read 20 entries
        entry_addr = table_addr + op * 4  # 4 bytes per far pointer
        
        offset = idc.get_wide_word(entry_addr)
        segment = idc.get_wide_word(entry_addr + 2)
        
        # Real mode linear address
        linear = segment * 16 + offset
        
        # Try to find in IDA
        # Search all segments for this offset
        ida_addr = None
        func_name = "???"
        
        for seg_ea in idautils.Segments():
            seg_start = idc.get_segm_start(seg_ea)
            seg_end = idc.get_segm_end(seg_ea)
            
            # Try: segment base + offset
            test_addr = seg_start + offset
            if seg_start <= test_addr < seg_end:
                if idc.is_code(idc.get_full_flags(test_addr)):
                    fname = idc.get_func_name(test_addr)
                    if fname:
                        ida_addr = test_addr
                        func_name = fname
                        break
        
        # If not found, try linear address directly
        if ida_addr is None:
            if idc.is_code(idc.get_full_flags(linear)):
                fname = idc.get_func_name(linear)
                if fname:
                    ida_addr = linear
                    func_name = fname
        
        marker = " <<<" if op == 0xA else ""
        
        print(f"{op:<4} {segment:04X}:{offset:04X}   0x{linear:08X}   0x{ida_addr:08X if ida_addr else 0}   {func_name}{marker}")
        
        # Save operation 0xA
        if op == 0xA:
            with open('op_0xa_real_handler.txt', 'w') as f:
                f.write(f"Operation: 0xA\n")
                f.write(f"Segment:Offset: {segment:04X}:{offset:04X}\n")
                f.write(f"Real linear: 0x{linear:08X}\n")
                f.write(f"IDA address: 0x{ida_addr:08X}\n")
                f.write(f"Function: {func_name}\n")
    
    print()
    print("Saved operation 0xA handler to op_0xa_real_handler.txt")
    
    idc.qexit(0)

if __name__ == '__main__':
    import idautils
    main()
