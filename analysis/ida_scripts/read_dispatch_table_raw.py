"""
Read dispatch table directly by examining op_dispatch code.
Extract the table address from the CALL instruction.
"""
import idaapi
import idautils
import idc

def main():
    idaapi.auto_wait()
    
    output = []
    output.append("=" * 80)
    output.append("DISPATCH TABLE RAW ANALYSIS")
    output.append("=" * 80)
    
    # op_dispatch is at 0x2257B
    # The instruction is: call cs:op_dispatch_table[bx]
    # We need to find the actual table address
    
    dispatch_addr = 0x2257B
    
    # Find the CALL instruction (should be at 0x22581)
    call_addr = 0x22581
    
    output.append(f"\nop_dispatch: 0x{dispatch_addr:X}")
    output.append(f"CALL instruction: 0x{call_addr:X}")
    output.append(f"Instruction bytes: {' '.join(f'{idc.get_wide_byte(call_addr + i):02X}' for i in range(6))}")
    
    # The instruction is a FAR CALL with indirect addressing
    # Format: FF 1E [offset]
    # or: FF 1F [offset] for cs: prefix
    
    # Try to extract the offset from instruction bytes
    byte1 = idc.get_wide_byte(call_addr)
    byte2 = idc.get_wide_byte(call_addr + 1)
    
    output.append(f"\nFirst byte: 0x{byte1:02X}")
    output.append(f"Second byte: 0x{byte2:02X}")
    
    if byte1 == 0xFF:  # CALL indirect
        # The table address follows
        table_offset = idc.get_wide_word(call_addr + 2)
        output.append(f"Table offset from instruction: 0x{table_offset:04X}")
        
        # In 16-bit real mode, cs: prefix means same code segment
        # Try to find what segment op_dispatch is in
        seg_start = idc.get_segm_start(dispatch_addr)
        seg_end = idc.get_segm_end(dispatch_addr)
        seg_name = idc.get_segm_name(dispatch_addr)
        
        output.append(f"\nop_dispatch segment:")
        output.append(f"  Name: {seg_name}")
        output.append(f"  Start: 0x{seg_start:08X}")
        output.append(f"  End: 0x{seg_end:08X}")
        
        # The table should be at: segment_base + table_offset
        # But in IDA's flat addressing, we need to figure out the right address
        
        # Try common patterns:
        # 1. Same segment as op_dispatch
        table_addr_1 = seg_start + table_offset
        
        # 2. Just after op_dispatch function
        dispatch_end = idc.get_func_attr(dispatch_addr, idc.FUNCATTR_END)
        table_addr_2 = dispatch_end
        
        # 3. At a known location nearby
        table_addr_3 = 0x22000 + table_offset
        
        output.append(f"\nPossible table addresses:")
        output.append(f"  1. Segment + offset: 0x{table_addr_1:08X}")
        output.append(f"  2. After dispatch: 0x{dispatch_end:08X}")
        output.append(f"  3. Base + offset: 0x{table_addr_3:08X}")
        
        # Read the table from most likely location
        # Looking at the verbose output, the table seems to be read starting near 0x22586
        # But that's past the function - let me try the actual offset
        
        # Let's try addresses in the range 0x22000 - 0x23000
        candidates = []
        for test_base in range(0x22000, 0x23000, 0x100):
            test_addr = test_base
            
            # Read first entry
            entry0 = idc.get_wide_word(test_addr)
            entry1 = idc.get_wide_word(test_addr + 2)
            entry2 = idc.get_wide_word(test_addr + 4)
            
            # Check if this looks like a function pointer table
            # Function pointers are usually non-zero and in reasonable range
            if 0x100 < entry0 < 0xF000 and 0x100 < entry1 < 0xF000 and 0x100 < entry2 < 0xF000:
                # Check if entries are distinct
                if entry0 != entry1 and entry1 != entry2:
                    candidates.append(test_addr)
        
        output.append(f"\nScanning for table patterns found {len(candidates)} candidates:")
        for addr in candidates[:10]:
            output.append(f"  Candidate at: 0x{addr:08X}")
            
            # Read first 5 entries
            entries = [idc.get_wide_word(addr + i*2) for i in range(5)]
            output.append(f"    First 5 entries: {' '.join(f'0x{e:04X}' for e in entries)}")
        
        # Also try to read what the verbose script found
        # From the verbose output, entry [10] (op 0xA) = 0x1EEC
        # So let's find where that pattern exists
        output.append(f"\nSearching for operation 0xA entry (0x1EEC):")
        
        for addr in range(0x22000, 0x23000, 2):
            word = idc.get_wide_word(addr)
            if word == 0x1EEC:
                # Check if this is in a table (look at surrounding entries)
                before = [idc.get_wide_word(addr - i*2) for i in range(1, 6)]
                after = [idc.get_wide_word(addr + i*2) for i in range(1, 6)]
                
                output.append(f"  Found 0x1EEC at: 0x{addr:08X}")
                output.append(f"    Before: {' '.join(f'0x{e:04X}' for e in reversed(before))}")
                output.append(f"    Entry: 0x{word:04X}")
                output.append(f"    After: {' '.join(f'0x{e:04X}' for e in after)}")
                
                # If this is entry [10], then the table starts 10*2 = 20 bytes before
                table_start = addr - 20
                output.append(f"  If this is entry [10], table starts at: 0x{table_start:08X}")
                
                # Read all 17 entries
                output.append(f"\n  Complete dispatch table (17 entries):")
                for i in range(17):
                    entry = idc.get_wide_word(table_start + i*2)
                    output.append(f"    Op {i:2} (0x{i:02X}): 0x{entry:04X}")
    
    result = '\n'.join(output)
    print(result)
    
    with open('dispatch_table_raw.txt', 'w') as f:
        f.write(result)
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
