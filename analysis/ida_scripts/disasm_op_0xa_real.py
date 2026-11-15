"""
Disassemble operation 0xA handler at 0x2063B and trace through trampolines.
"""
import idaapi
import idautils
import idc

def disasm_function(addr, max_instructions=500):
    """Disassemble function."""
    func_end = idc.get_func_attr(addr, idc.FUNCATTR_END)
    if func_end == idc.BADADDR:
        func_end = addr + 1000
    
    lines = []
    ea = addr
    count = 0
    
    while ea < func_end and ea != idc.BADADDR and count < max_instructions:
        disasm = idc.generate_disasm_line(ea, 0)
        lines.append(f"  0x{ea:08X}: {disasm}")
        ea = idc.next_head(ea)
        count += 1
    
    return lines

def main():
    idaapi.auto_wait()
    
    op_a_addr = 0x2063B
    
    print("=" * 80)
    print(f"OPERATION 0xA HANDLER DISASSEMBLY")
    print("=" * 80)
    print(f"\nStarting at: 0x{op_a_addr:08X} (dispatch_220b0_near)")
    print()
    
    # Disassemble first function
    print("Disassembly:")
    print("-" * 80)
    disasm1 = disasm_function(op_a_addr, max_instructions=100)
    for line in disasm1:
        print(line)
    
    # Look for FAR CALL to cs:220B0
    print()
    print("-" * 80)
    print("Analysis:")
    print("-" * 80)
    
    # Read what's at cs:220B0
    # cs:220B0 means offset 0x220B0 in the code segment
    # With segment base 0x20000, that's 0x20000 + 0x220B0 = 0x420B0
    ptr_addr = 0x20000 + 0x220B0
    
    print(f"\nPointer at cs:220B0 (0x{ptr_addr:08X}):")
    
    # Read as far pointer (segment:offset)
    offset = idc.get_wide_word(ptr_addr)
    segment = idc.get_wide_word(ptr_addr + 2)
    
    print(f"  Offset: 0x{offset:04X}")
    print(f"  Segment: 0x{segment:04X}")
    
    # Convert to linear address
    # In real mode: linear = segment * 16 + offset
    # But in IDA flat model, we need to find the segment
    
    # Try to find which IDA segment this maps to
    target_linear = segment * 16 + offset
    print(f"  Real-mode linear: 0x{target_linear:08X}")
    
    # Search for segments that could contain this
    print(f"\nSearching IDA segments for target...")
    
    for seg_ea in idautils.Segments():
        seg_start = idc.get_segm_start(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        seg_name = idc.get_segm_name(seg_ea)
        
        # Check if offset falls within this segment
        if seg_start <= seg_start + offset < seg_end:
            test_addr = seg_start + offset
            if idc.is_code(idc.get_full_flags(test_addr)):
                func_name = idc.get_func_name(test_addr)
                if func_name:
                    print(f"  Candidate in {seg_name}: 0x{test_addr:08X} = {func_name}")
    
    # Also try common segment bases
    common_bases = [0x10000, 0x20000, 0x30000, segment * 16]
    print(f"\nTrying common segment bases with offset 0x{offset:04X}:")
    
    for base in common_bases:
        test_addr = base + offset
        if idc.is_code(idc.get_full_flags(test_addr)):
            func_name = idc.get_func_name(test_addr)
            if func_name:
                print(f"  Base 0x{base:08X}: 0x{test_addr:08X} = {func_name}")
                
                # If we found it, disassemble it
                print(f"\n{'=' * 80}")
                print(f"DISASSEMBLING ACTUAL HANDLER: {func_name}")
                print("=" * 80)
                disasm2 = disasm_function(test_addr, max_instructions=200)
                for line in disasm2:
                    print(line)
                
                # Save address
                with open('rle_decompressor_address.txt', 'w') as f:
                    f.write(f"0x{test_addr:08X}\n")
                    f.write(f"Function: {func_name}\n")
                
                break
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
