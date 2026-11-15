"""
Extract detailed disassembly of madfont_idx_dat_loader to find RLE decompression.

We'll look for:
1. Loops that process compressed data
2. Buffer write operations
3. Byte-counting patterns
4. Control flow that indicates run vs literal modes

Run in IDA: File > Script file > disasm_font_loader.py
"""

import idaapi
import idc
import idautils

def disassemble_function_detailed(func_ea, output_file):
    """Extract complete disassembly with annotations."""
    
    func = idaapi.get_func(func_ea)
    if not func:
        print(f"ERROR: No function at 0x{func_ea:x}")
        return
    
    name = idc.get_func_name(func_ea)
    size = func.end_ea - func.start_ea
    
    print(f"Disassembling {name} @ 0x{func_ea:x} ({size} bytes)")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Function: {name}\n")
        f.write(f"Address: 0x{func_ea:x}\n")
        f.write(f"Size: {size} bytes\n")
        f.write(f"="*80 + "\n\n")
        
        # Track interesting patterns
        loop_count = 0
        buffer_writes = []
        comparisons = []
        
        for head in idautils.Heads(func.start_ea, func.end_ea):
            # Get instruction
            mnem = idc.print_insn_mnem(head)
            disasm = idc.GetDisasm(head)
            
            # Get operands
            op0 = idc.print_operand(head, 0)
            op1 = idc.print_operand(head, 1)
            
            # Check for interesting operations
            annotation = ""
            
            # Loop detection
            if mnem.lower() in ['loop', 'loopz', 'loopnz', 'loope', 'loopne']:
                loop_count += 1
                annotation = f"  ; LOOP #{loop_count}"
            
            # Buffer write
            if mnem.lower() in ['mov', 'stosb', 'movsb'] and '[' in op0:
                buffer_writes.append(head)
                annotation = f"  ; BUFFER WRITE #{len(buffer_writes)}"
            
            # Comparison (might check control bytes or counts)
            if mnem.lower() in ['cmp', 'test']:
                comparisons.append(head)
                if '0' in op1 or '4' in op1 or '0x80' in op1:
                    annotation = f"  ; COMPARE (possibly control/header)"
            
            # Rep instructions (fast fill/copy)
            if mnem.lower() == 'rep':
                annotation = "  ; REP - FAST OPERATION"
            
            # Write to file
            f.write(f"0x{head:06x}:  {disasm:50s}{annotation}\n")
            
            # Add comments for xrefs
            xrefs = list(idautils.XrefsFrom(head, 0))
            if xrefs:
                for xref in xrefs:
                    if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:  # Call
                        target_name = idc.get_func_name(xref.to)
                        if target_name:
                            f.write(f"          -> calls {target_name} @ 0x{xref.to:x}\n")
        
        # Summary
        f.write(f"\n{'='*80}\n")
        f.write(f"SUMMARY\n")
        f.write(f"{'='*80}\n")
        f.write(f"Loops: {loop_count}\n")
        f.write(f"Buffer writes: {len(buffer_writes)}\n")
        f.write(f"Comparisons: {len(comparisons)}\n")
        
        if buffer_writes:
            f.write(f"\nBuffer write locations:\n")
            for addr in buffer_writes[:10]:
                f.write(f"  0x{addr:06x}: {idc.GetDisasm(addr)}\n")
        
        if loop_count > 0:
            f.write(f"\nFound {loop_count} loops - likely candidates for decompression\n")
    
    print(f"✓ Disassembly saved to: {output_file}")

def find_loops_and_analyze(func_ea):
    """Find all loops and analyze their structure."""
    
    func = idaapi.get_func(func_ea)
    if not func:
        return []
    
    loops = []
    
    for head in idautils.Heads(func.start_ea, func.end_ea):
        mnem = idc.print_insn_mnem(head).lower()
        
        if mnem in ['loop', 'loopz', 'loopnz']:
            # Get loop target (where it jumps back to)
            target = idc.get_operand_value(head, 0)
            
            # Analyze loop body
            loop_size = head - target if target < head else 0
            
            # Count operations in loop
            ops_in_loop = 0
            buffer_writes_in_loop = 0
            
            if target < head:
                for addr in range(target, head):
                    if idc.is_code(idc.get_full_flags(addr)):
                        ops_in_loop += 1
                        op_mnem = idc.print_insn_mnem(addr).lower()
                        op0 = idc.print_operand(addr, 0)
                        if op_mnem in ['mov', 'stosb'] and '[' in op0:
                            buffer_writes_in_loop += 1
            
            loops.append({
                'address': f'0x{head:x}',
                'type': mnem,
                'target': f'0x{target:x}',
                'loop_size': loop_size,
                'ops_in_loop': ops_in_loop,
                'buffer_writes': buffer_writes_in_loop
            })
    
    return loops

def main():
    print("="*80)
    print("DISASSEMBLING FONT LOADER TO FIND RLE ALGORITHM")
    print("="*80)
    
    idaapi.auto_wait()
    
    # Font loaders to analyze
    loaders = [
        (0x1297F0, 'picfont_idx_dat_loader'),
        (0x1397CE, 'madfont_idx_dat_loader')
    ]
    
    for func_ea, func_name in loaders:
        print(f"\n[1] Analyzing {func_name} @ 0x{func_ea:x}")
        print("-"*80)
        
        # Extract full disassembly
        output_file = rf'c:\Users\ybarnoy\projects\falcon3\analysis\disasm_{func_name}.txt'
        disassemble_function_detailed(func_ea, output_file)
        
        # Analyze loops
        print(f"\n[2] Analyzing loops in {func_name}")
        loops = find_loops_and_analyze(func_ea)
        
        if loops:
            print(f"Found {len(loops)} loops:")
            for i, loop in enumerate(loops, 1):
                print(f"\n  Loop {i}:")
                print(f"    Address: {loop['address']}")
                print(f"    Type: {loop['type']}")
                print(f"    Target: {loop['target']}")
                print(f"    Loop size: {loop['loop_size']} bytes")
                print(f"    Operations in loop: {loop['ops_in_loop']}")
                print(f"    Buffer writes in loop: {loop['buffer_writes']}")
                
                if loop['buffer_writes'] > 0:
                    print(f"    >>> LIKELY DECOMPRESSION LOOP <<<")
        else:
            print(f"  No explicit LOOP instructions found")
            print(f"  Decompression may use conditional jumps (JZ/JNZ) instead")
    
    print(f"\n{'='*80}")
    print("Disassembly complete. Check the output files for details.")
    print("="*80)

if __name__ == '__main__':
    main()
