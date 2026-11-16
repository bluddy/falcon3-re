"""
Examine the code immediately after each input_flag_pending_2 read.
Look for dispatch patterns: switch tables, cmp chains, etc.
"""

import idaapi
import idautils
import idc
import json

def analyze_dispatch_pattern(read_addr):
    """Analyze 50 instructions after a read to find dispatch pattern."""
    
    func_name = idc.get_func_name(read_addr)
    seg_name = idc.get_segm_name(read_addr)
    
    result = {
        'read_addr': f'0x{read_addr:X}',
        'func': func_name,
        'segment': seg_name,
        'instructions': [],
        'pattern_found': None,
        'interesting_findings': []
    }
    
    print(f"\n{'='*80}")
    print(f"Analyzing 0x{read_addr:X} in {func_name} ({seg_name})")
    print('='*80)
    
    # Get the read instruction
    read_insn = idc.GetDisasm(read_addr)
    print(f"  READ: {read_insn}")
    
    # Analyze next 50 instructions
    ea = read_addr
    for i in range(50):
        ea = idc.next_head(ea)
        if ea == idc.BADADDR:
            break
        
        insn = idc.GetDisasm(ea)
        mnem = idc.print_insn_mnem(ea)
        
        result['instructions'].append({
            'addr': f'0x{ea:X}',
            'insn': insn,
            'mnem': mnem
        })
        
        # Look for dispatch patterns
        
        # Pattern 1: Subtract to normalize (sub ax, 2 would normalize 0x02-0x0B to 0x00-0x09)
        if mnem == 'sub' and 'ax' in insn:
            op_val = idc.get_operand_value(ea, 1)
            if op_val == 2:
                print(f"  >>> NORMALIZE: {insn} [Converts scan 0x02-0x0B to index 0x00-0x09]")
                result['interesting_findings'].append({
                    'type': 'normalize',
                    'addr': f'0x{ea:X}',
                    'insn': insn
                })
        
        # Pattern 2: Comparison with view key scan codes
        if mnem == 'cmp':
            op_val = idc.get_operand_value(ea, 1)
            # View keys: 0x02-0x0B (1,2,3,4,5,6,7,8,9,0)
            if 0x02 <= op_val <= 0x0B or op_val in [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]:
                print(f"  >>> VIEW KEY CMP: {insn} [Scan code {op_val:#x}]")
                result['interesting_findings'].append({
                    'type': 'view_key_compare',
                    'addr': f'0x{ea:X}',
                    'insn': insn,
                    'scan_code': op_val
                })
        
        # Pattern 3: Bounds check (cmp ax, <count>)
        if mnem == 'cmp' and 'ax' in insn:
            op_val = idc.get_operand_value(ea, 1)
            if 8 <= op_val <= 12:  # Reasonable range for view key count
                print(f"  >>> BOUNDS CHECK: {insn} [Max value {op_val}]")
                result['interesting_findings'].append({
                    'type': 'bounds_check',
                    'addr': f'0x{ea:X}',
                    'insn': insn,
                    'max_val': op_val
                })
        
        # Pattern 4: Indexed jump (jmp [table+ax*2])
        if mnem in ['jmp', 'call']:
            if idc.get_operand_type(ea, 0) in [idc.o_phrase, idc.o_displ]:
                print(f"  >>> JUMP TABLE: {insn} [Indirect jump/call - likely switch]")
                result['pattern_found'] = 'jump_table'
                result['interesting_findings'].append({
                    'type': 'jump_table',
                    'addr': f'0x{ea:X}',
                    'insn': insn
                })
        
        # Pattern 5: Multiple sequential compares (if/else chain)
        if mnem == 'cmp' and i < 49:
            # Count sequential cmp/jz pairs
            next_ea = idc.next_head(ea)
            next_mnem = idc.print_insn_mnem(next_ea)
            if next_mnem in ['jz', 'jnz', 'je', 'jne']:
                # This is a cmp/branch pair - part of if/else chain
                pass
        
        # Pattern 6: Call with scan code as parameter
        if mnem == 'push' and 'ax' in insn:
            # Might be pushing scan code as function parameter
            next_ea = idc.next_head(ea)
            next_mnem = idc.print_insn_mnem(next_ea)
            if next_mnem == 'call':
                next_insn = idc.GetDisasm(next_ea)
                print(f"  >>> PARAM CALL: push ax ; {next_insn}")
                result['interesting_findings'].append({
                    'type': 'parameterized_call',
                    'addr': f'0x{ea:X}',
                    'insn': f"{insn} ; {next_insn}"
                })
        
        # Show first 10 instructions for context
        if i < 10:
            print(f"    {insn}")
    
    return result

def main():
    idaapi.auto_wait()
    
    print("=" * 80)
    print("EXAMINING INPUT DISPATCH CONTEXT")
    print("=" * 80)
    
    # Target addresses where input_flag_pending_2 is read
    targets = [
        # r29_tactical_screen_coordinator (3 reads)
        0x12DFD6,
        0x12EEDC,
        0x12F512,
        # game_mode_r53_main_coordinator (5 reads)
        0x182476,
        0x183834,
        0x183FA6,
        0x184B10,
        0x185068,
    ]
    
    results = []
    
    for addr in targets:
        result = analyze_dispatch_pattern(addr)
        results.append(result)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    for result in results:
        if result['interesting_findings']:
            print(f"\n{result['func']} at {result['read_addr']}:")
            for finding in result['interesting_findings']:
                print(f"  [{finding['type']}] {finding['addr']}: {finding['insn']}")
    
    # Save results
    output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\dgroup\input_dispatch_patterns.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n\nResults saved to: {output_file}")
    print("\nNext: Open IDA and navigate to interesting addresses to examine manually.")

if __name__ == "__main__":
    main()
    idc.qexit(0)
