"""
Directly trace operation 0xA from the dispatch table.
This operation is used by the font loaders and likely contains the RLE decompressor.
"""
import idaapi
import idc
import idautils
import json

def follow_address(ea, depth=0, max_depth=5, visited=None):
    """Recursively follow an address through trampolines."""
    if visited is None:
        visited = set()
    
    if depth >= max_depth or ea in visited:
        return []
    
    visited.add(ea)
    
    result = {
        'depth': depth,
        'address': f"0x{ea:08X}",
        'name': idc.get_func_name(ea),
        'type': 'function' if idc.get_func_attr(ea, idc.FUNCATTR_START) else 'data',
        'next': []
    }
    
    # If it's not a function, return
    if not idc.get_func_attr(ea, idc.FUNCATTR_START):
        result['type'] = 'invalid'
        return [result]
    
    func = idaapi.get_func(ea)
    result['size'] = func.end_ea - func.start_ea
    
    # Get disassembly of first 20 instructions
    disasm = []
    count = 0
    curr_ea = ea
    while curr_ea < func.end_ea and count < 20:
        line = idc.generate_disasm_line(curr_ea, 0)
        disasm.append(line)
        curr_ea = idc.next_head(curr_ea)
        count += 1
    result['disasm'] = disasm
    
    # Look for jumps and calls in first 20 instructions
    curr_ea = ea
    count = 0
    while curr_ea < func.end_ea and count < 20:
        insn = idaapi.insn_t()
        if idaapi.decode_insn(insn, curr_ea):
            mnem = idc.print_insn_mnem(curr_ea).lower()
            
            # Direct jump/call
            if mnem in ['jmp', 'jmpf', 'call', 'callf']:
                target = idc.get_operand_value(curr_ea, 0)
                if target and target != idc.BADADDR:
                    result['next'].extend(follow_address(target, depth + 1, max_depth, visited))
            
            # Indirect jump through register/memory
            elif mnem in ['jmp', 'call']:
                op0 = idc.print_operand(curr_ea, 0)
                # Try to resolve indirect jumps through tables
                if '[' in op0:  # Memory reference
                    # This is complex, just note it
                    result['indirect_jump'] = op0
        
        curr_ea = idc.next_head(curr_ea)
        count += 1
    
    return [result]

def main():
    idaapi.auto_wait()
    
    print("=" * 80)
    print("TRACING OPERATION 0xA FROM DISPATCH TABLE")
    print("=" * 80)
    
    # Dispatch table is at cs:0x29A0, absolute address 0x229A0
    # Entry [10] (0xA) is at offset 10 * 2 = 20 bytes = 0x14
    dispatch_table_addr = 0x229A0
    entry_0xA_addr = dispatch_table_addr + 0x14
    
    print(f"\nDispatch table: 0x{dispatch_table_addr:06X}")
    print(f"Entry [0xA]: 0x{entry_0xA_addr:06X}")
    
    # Read the pointer at this address
    ptr = idc.get_wide_word(entry_0xA_addr)
    
    print(f"Pointer value: 0x{ptr:04X}")
    
    # This is a near pointer in the code segment
    # We need to add the segment base
    # Try multiple possibilities
    possible_addresses = [
        ptr,  # Direct
        0x20000 + ptr,  # Common code segment base
        0x10000 + ptr,  # Alternative
        ptr + 0x10,  # Paragraph aligned
    ]
    
    results = []
    
    for addr in possible_addresses:
        print(f"\n--- Trying address: 0x{addr:06X} ---")
        
        # Check if this is a valid function
        func_start = idc.get_func_attr(addr, idc.FUNCATTR_START)
        if func_start:
            print(f"  Valid function: {idc.get_func_name(addr)}")
            
            # Follow this address
            trace = follow_address(addr, max_depth=8)
            results.append({
                'base_address': f"0x{addr:06X}",
                'trace': trace
            })
        else:
            print(f"  Not a function")
    
    # Also manually check known dispatch addresses
    known_dispatch = [
        0x220B0,  # dispatch_220b0_near
        0x22128,  # dispatch_22128_invoke_1arg
        0x1EEC,   # From table entry
        0x063B,   # Alternative reading
    ]
    
    print("\n" + "=" * 80)
    print("CHECKING KNOWN DISPATCH ADDRESSES")
    print("=" * 80)
    
    for addr in known_dispatch:
        print(f"\n--- Address: 0x{addr:06X} ---")
        func_start = idc.get_func_attr(addr, idc.FUNCATTR_START)
        if func_start:
            print(f"  Function: {idc.get_func_name(addr)}")
            trace = follow_address(addr, max_depth=8)
            results.append({
                'base_address': f"0x{addr:06X}",
                'trace': trace
            })
        else:
            print(f"  Not a function")
    
    # Save results
    import os
    output_path = os.path.join(os.path.dirname(__file__), '..', 'ida_falconcd', 'operation_0xA_trace.json')
    output = {
        'dispatch_table': f"0x{dispatch_table_addr:06X}",
        'entry_0xA_offset': f"0x{entry_0xA_addr:06X}",
        'pointer_value': f"0x{ptr:04X}",
        'traces': results
    }
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Found {len(results)} valid traces")
    print(f"Results saved to operation_0xA_trace.json")
    
    # Print the first trace in detail
    if results:
        print("\n" + "=" * 80)
        print("FIRST TRACE DETAIL")
        print("=" * 80)
        
        first = results[0]
        print(f"\nBase address: {first['base_address']}")
        
        def print_trace(trace, indent=0):
            for item in trace:
                prefix = "  " * indent
                print(f"{prefix}Depth {item['depth']}: {item['address']} {item['name']} ({item['type']})")
                if 'size' in item:
                    print(f"{prefix}  Size: {item['size']} bytes")
                if 'disasm' in item and indent < 2:  # Only print disasm for first 2 levels
                    print(f"{prefix}  First 10 instructions:")
                    for line in item['disasm'][:10]:
                        print(f"{prefix}    {line}")
                if item['next']:
                    print_trace(item['next'], indent + 1)
        
        print_trace(first['trace'])
    
    print("\nDone!")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
