"""
Direct approach: examine op_dispatch instruction by instruction to find table reference.
"""
import idaapi
import idautils
import idc

def main():
    idaapi.auto_wait()
    
    dispatch_addr = 0x2257B
    
    print("=" * 80)
    print(f"Analyzing op_dispatch @ 0x{dispatch_addr:X}")
    print("=" * 80)
    
    # Disassemble each instruction and look for the CALL instruction
    ea = dispatch_addr
    func_end = idc.get_func_attr(dispatch_addr, idc.FUNCATTR_END)
    
    print("\nDisassembly:")
    while ea < func_end and ea != idc.BADADDR:
        mnem = idc.print_insn_mnem(ea)
        op0 = idc.print_operand(ea, 0)
        
        disasm = idc.generate_disasm_line(ea, 0)
        print(f"  0x{ea:X}: {disasm}")
        
        # Look for: call cs:op_dispatch_table[bx]
        if mnem == 'call':
            print(f"\n    -> Found CALL instruction")
            print(f"    -> Operand: {op0}")
            
            # Get all xrefs from this instruction
            print(f"    -> Cross-references from this call:")
            for xref in idautils.XrefsFrom(ea, 0):
                print(f"       Type: {xref.type}, To: 0x{xref.to:X}")
                
                # If it's a data reference, that's our table!
                if xref.type == idc.fl_F or xref.type == idc.dr_O:
                    table_addr = xref.to
                    print(f"\n    -> DISPATCH TABLE FOUND at 0x{table_addr:X}!")
                    
                    # Read table entries
                    print(f"\n    -> Reading table entries:")
                    for i in range(25):
                        entry_addr = table_addr + i * 2
                        ptr = idc.get_wide_word(entry_addr)
                        
                        if ptr == 0 or ptr == 0xFFFF:
                            print(f"       Entry {i}: END (0x{ptr:04X})")
                            break
                        
                        func_name = idc.get_func_name(ptr)
                        if not func_name:
                            func_name = f"sub_{ptr:X}"
                        
                        print(f"       Entry {i} (op 0x{i:X}): 0x{ptr:X} -> {func_name}")
                        
                        # Mark operation 0xA specially
                        if i == 0xA:
                            print(f"       *** OPERATION 0xA (FILE READ + RLE DECOMPRESSION) ***")
                    
                    # Save the op 0xA address for next script
                    with open('op_0xa_handler.txt', 'w') as f:
                        op_a_addr = idc.get_wide_word(table_addr + 0xA * 2)
                        f.write(f"0x{op_a_addr:X}\n")
                    
                    break
        
        ea = idc.next_head(ea)
    
    print("\n" + "=" * 80)
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
