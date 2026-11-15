"""
Verbose dispatch table finder with complete output capture.
"""
import idaapi
import idautils
import idc
import sys

def main():
    idaapi.auto_wait()
    
    dispatch_addr = 0x2257B
    
    output = []
    output.append("=" * 80)
    output.append(f"Analyzing op_dispatch @ 0x{dispatch_addr:X}")
    output.append("=" * 80)
    
    # Get function bounds
    func_start = idc.get_func_attr(dispatch_addr, idc.FUNCATTR_START)
    func_end = idc.get_func_attr(dispatch_addr, idc.FUNCATTR_END)
    func_size = func_end - func_start if func_end != idc.BADADDR else 0
    
    output.append(f"Function start: 0x{func_start:X}")
    output.append(f"Function end: 0x{func_end:X}")
    output.append(f"Function size: {func_size} bytes")
    output.append("")
    
    # Disassemble instruction by instruction
    output.append("Complete disassembly:")
    output.append("-" * 80)
    
    ea = dispatch_addr
    while ea < func_end and ea != idc.BADADDR:
        flags = idc.get_full_flags(ea)
        mnem = idc.print_insn_mnem(ea)
        disasm = idc.generate_disasm_line(ea, 0)
        
        output.append(f"0x{ea:06X}: {disasm}")
        
        # Special handling for CALL instruction
        if mnem == 'call' or mnem == 'lcall':
            output.append(f"  -> CALL instruction found!")
            output.append(f"  -> Mnemonic: {mnem}")
            
            # Get operands
            for i in range(3):
                op = idc.print_operand(ea, i)
                if op:
                    output.append(f"  -> Operand {i}: {op}")
            
            # Get all xrefs
            output.append(f"  -> Cross-references:")
            xref_count = 0
            for xref in idautils.XrefsFrom(ea, 0):
                output.append(f"     Type: {xref.type}, To: 0x{xref.to:08X}")
                xref_count += 1
                
                # Try to get name at target
                target_name = idc.get_name(xref.to, idc.GN_VISIBLE)
                if target_name:
                    output.append(f"     Name: {target_name}")
                
                # If it's a data reference, read it as potential table
                seg_name = idc.get_segm_name(xref.to)
                output.append(f"     Segment: {seg_name}")
                
                # Read as potential table start
                output.append(f"     Reading as word table:")
                for j in range(20):
                    table_offset = xref.to + j * 2
                    word_val = idc.get_wide_word(table_offset)
                    output.append(f"       [{j:2}] @ 0x{table_offset:08X} = 0x{word_val:04X}")
                    
                    # Check if it's a valid code address
                    if word_val != 0 and word_val != 0xFFFF:
                        # Convert to full address (segment:offset)
                        # Try different segment bases
                        for seg_ea in idautils.Segments():
                            seg_start = idc.get_segm_start(seg_ea)
                            seg_end = idc.get_segm_end(seg_ea)
                            
                            # Try as offset within this segment
                            test_addr = seg_start + word_val
                            if seg_start <= test_addr < seg_end:
                                if idc.is_code(idc.get_full_flags(test_addr)):
                                    func_name = idc.get_func_name(test_addr)
                                    if func_name:
                                        output.append(f"                -> In seg 0x{seg_start:08X}: 0x{test_addr:08X} = {func_name}")
                    
                    if word_val == 0 or word_val == 0xFFFF:
                        output.append(f"       -> End of table")
                        break
            
            if xref_count == 0:
                output.append(f"     No xrefs found - trying manual operand parse")
                # Try to extract address from operand string
                operand_str = idc.print_operand(ea, 0)
                output.append(f"     Operand string: '{operand_str}'")
        
        ea = idc.next_head(ea)
    
    result = '\n'.join(output)
    print(result)
    
    # Write to file
    with open('dispatch_table_verbose.txt', 'w') as f:
        f.write(result)
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
