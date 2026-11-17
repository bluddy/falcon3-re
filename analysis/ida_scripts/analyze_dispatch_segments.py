"""
Analyze the dispatch table to understand segment addressing.
The target addresses might be segment:offset pairs or need translation.
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

def main():
    print("Waiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete\n")
    
    # Dispatch table location
    table_addr = 0x26426
    
    print(f"=== Analyzing Dispatch Table Segment Context ===\n")
    
    # Get segment info for the table itself
    seg = idaapi.getseg(table_addr)
    if seg:
        seg_name = idc.get_segm_name(seg.start_ea)
        print(f"Table segment: {seg_name}")
        print(f"Segment range: 0x{seg.start_ea:X} - 0x{seg.end_ea:X}")
        print(f"Table is in code segment: {seg.type == idaapi.SEG_CODE}")
        print()
    
    # Read the table and check what the values reference
    print("=== Checking Table Entry Targets ===\n")
    
    for i in range(10):  # Check first 10 entries
        addr = table_addr + (i * 2)
        value = idc.get_wide_word(addr)
        
        print(f"Entry [{i}] @ 0x{addr:X}: value=0x{value:04X}")
        
        # Try as linear address
        if idaapi.is_mapped(value):
            seg_target = idaapi.getseg(value)
            if seg_target:
                seg_name_target = idc.get_segm_name(seg_target.start_ea)
                func_name = idc.get_func_name(value)
                print(f"  -> Linear address: segment {seg_name_target}, func={func_name}")
            else:
                print(f"  -> Linear address mapped but no segment")
        else:
            print(f"  -> NOT a linear address")
        
        # Try to see what's at that address in different contexts
        # The table might be using near pointers within the same segment
        if seg:
            # Try as offset within table's segment
            linear_in_seg = seg.start_ea + value
            if idaapi.is_mapped(linear_in_seg):
                func_name = idc.get_func_name(linear_in_seg)
                print(f"  -> As offset in table segment: 0x{linear_in_seg:X}, func={func_name}")
        
        print()
    
    # Check if this is CS-relative
    print("=== Checking CS Register Value ===\n")
    
    # Try to find where CS is set before the call
    # Look at farobj_record_step to see segment setup
    record_step_addr = 0x2142E
    func = idaapi.get_func(record_step_addr)
    if func:
        print(f"Checking farobj_record_step at 0x{record_step_addr:X}")
        
        # Look for segment register loads
        ea = func.start_ea
        found_cs = False
        while ea < func.end_ea and ea - func.start_ea < 100:  # First 100 bytes
            disasm = idc.generate_disasm_line(ea, 0)
            if 'cs:' in disasm.lower() or 'push' in disasm.lower() and 'cs' in disasm.lower():
                print(f"  0x{ea:X}: {disasm}")
                found_cs = True
            
            # Also check for mov to segment registers
            mnem = idc.print_insn_mnem(ea)
            if mnem == 'mov':
                op0 = idc.print_operand(ea, 0)
                if 'cs' in op0.lower():
                    print(f"  0x{ea:X}: {disasm} <- SETS CS!")
            
            ea = idc.next_head(ea, func.end_ea)
    
    # The dispatch might be CS-segment relative
    # CS segment in 16-bit code would be the code segment base
    print("\n=== Conclusion ===\n")
    print("The dispatch table contains NEAR pointers (offsets within code segment).")
    print("To convert to linear addresses, need to know CS segment base.")
    print("The 'call cs:off_26426[bx]' uses CS-relative addressing.")
    
    # Try to find actual function addresses by looking at xrefs
    print("\n=== Alternative: Find Functions by Searching for Patterns ===\n")
    
    # Search for functions that might be entity renderers
    # They would likely call text/drawing functions
    candidates = []
    
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        func_name = idc.get_func_name(func_ea)
        
        # Look for functions that call drawing or text rendering
        ea = func.start_ea
        calls_draw = False
        calls_text = False
        
        while ea < func.end_ea:
            if idc.print_insn_mnem(ea) == 'call':
                target = idc.get_operand_value(ea, 0)
                target_name = idc.get_func_name(target) or ""
                
                if 'draw' in target_name.lower() or 'render' in target_name.lower():
                    calls_draw = True
                if 'text' in target_name.lower() or 'font' in target_name.lower():
                    calls_text = True
            
            ea = idc.next_head(ea, func.end_ea)
        
        if calls_draw or calls_text:
            candidates.append({
                'address': hex(func_ea),
                'name': func_name,
                'size': func.end_ea - func.start_ea,
                'calls_draw': calls_draw,
                'calls_text': calls_text
            })
    
    print(f"Found {len(candidates)} candidate drawing functions\n")
    
    # Save results
    results = {
        'table_info': {
            'address': hex(table_addr),
            'segment': seg_name if seg else None,
            'note': 'Dispatch table uses CS-relative NEAR pointers'
        },
        'drawing_function_candidates': candidates[:50]  # First 50
    }
    
    output_json = Path(__file__).parent / "dispatch_segment_analysis.json"
    with open(output_json, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✓ Results saved to: {output_json}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
