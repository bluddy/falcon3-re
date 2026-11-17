"""
Simple test: Find references to 0x19 (AGM-88 HARM weapon type).
"""

import idc
import idaapi
import idautils
import json

def main():
    print("Starting HARM type search...")
    
    results = {
        'harm_type': '0x19',
        'references': []
    }
    
    # Search for immediate value 0x19 in code segment
    text_seg = idaapi.get_segm_by_name(".text")
    if not text_seg:
        print("ERROR: .text segment not found")
        return results
    
    print(f"Searching .text segment: {text_seg.start_ea:#x} - {text_seg.end_ea:#x}")
    
    ea = text_seg.start_ea
    count = 0
    
    while ea < text_seg.end_ea and count < 100:  # Limit to first 100
        insn = idaapi.insn_t()
        insn_len = idaapi.decode_insn(insn, ea)
        
        if insn_len > 0:
            # Check for cmp with 0x19
            if insn.itype == idaapi.NN_cmp:
                for op in insn.ops:
                    if op.type == idaapi.o_imm and op.value == 0x19:
                        func_name = idc.get_func_name(ea)
                        disasm = idc.generate_disasm_line(ea, 0)
                        
                        results['references'].append({
                            'address': hex(ea),
                            'function': func_name if func_name else 'unknown',
                            'disasm': disasm
                        })
                        count += 1
                        print(f"  Found at {ea:#x} in {func_name}: {disasm}")
                        break
        
        ea = idc.next_head(ea, text_seg.end_ea)
    
    print(f"\nFound {len(results['references'])} references to 0x19")
    
    # Save to JSON in same directory as script
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, "harm_refs.json")
    
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to: {output_file}")
    except Exception as e:
        print(f"ERROR saving file: {e}")
    return results

if __name__ == "__main__":
    idaapi.auto_wait()  # Wait for auto-analysis
    main()
    idc.qexit(0)  # Exit explicitly
