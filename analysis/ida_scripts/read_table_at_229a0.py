"""
Read dispatch table at 0x229A0 directly.
"""
import idaapi
import idc

def main():
    idaapi.auto_wait()
    
    table_addr = 0x229A0
    
    print("=" * 80)
    print(f"DISPATCH TABLE at 0x{table_addr:08X}")
    print("=" * 80)
    print()
    
    # Read 17 entries (operations 0-16)
    print(f"{'Op':<4} {'Offset':<8} {'Address':<10} {'Function Name'}")
    print("-" * 70)
    
    for i in range(17):
        entry_addr = table_addr + i * 2
        offset = idc.get_wide_word(entry_addr)
        
        # Calculate full address
        # The offset is relative to the code segment
        # From analysis, segment starts at 0x20000
        seg_base = 0x20000
        full_addr = seg_base + offset
        
        # Get function name
        func_name = idc.get_func_name(full_addr)
        if not func_name:
            func_name = f"sub_{full_addr:X}"
        
        print(f"{i:<4} 0x{offset:04X}   0x{full_addr:08X}  {func_name}")
        
        # Highlight operation 0xA
        if i == 0xA:
            print(f"     ^^^ OPERATION 0xA - FILE READ + RLE DECOMPRESSION ^^^")
    
    # Save operation 0xA address
    op_a_offset = idc.get_wide_word(table_addr + 0xA * 2)
    op_a_addr = seg_base + op_a_offset
    
    print()
    print("=" * 80)
    print(f"Operation 0xA handler: 0x{op_a_addr:08X}")
    print("=" * 80)
    
    with open('op_0xa_address.txt', 'w') as f:
        f.write(f"0x{op_a_addr:08X}\n")
        f.write(f"Offset: 0x{op_a_offset:04X}\n")
        f.write(f"Segment base: 0x{seg_base:08X}\n")
    
    print("\nSaved operation 0xA address to op_0xa_address.txt")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
