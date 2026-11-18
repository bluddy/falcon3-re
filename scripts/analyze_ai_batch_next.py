import idaapi
import idc
import idautils

idaapi.auto_wait()

output_path = r"C:\Users\ybarnoy\projects\falcon3\temp\ai_batch_analysis.txt"

# Next batch of unanalyzed AI functions from catalog
functions_to_analyze = [
    (0x3EBA5, "ai_behavior_decision_tree"),
    (0x40768, "ai_state_range_check"),
    (0x407AA, "ai_state_value_dispatcher"),
    (0x40C0A, "ai_distance_range_check"),
    (0x40C9E, "ai_rect_ratio_check"),
    (0x40CC5, "ai_rect_ratio_update"),
    (0x428B8, "ai_field_check_flag"),
    (0x428E1, "ai_field_pair_compare"),
]

try:
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=== AI Function Batch Analysis ===\n\n")
        
        for addr, expected_name in functions_to_analyze:
            f.write(f"\n{'='*70}\n")
            f.write(f"Function: {expected_name} @ {addr:#x}\n")
            f.write(f"{'='*70}\n\n")
            
            func = idaapi.get_func(addr)
            if not func:
                f.write(f"ERROR: No function at {addr:#x}\n")
                continue
            
            actual_name = idc.get_func_name(addr)
            size = func.end_ea - func.start_ea
            
            f.write(f"Actual name: {actual_name}\n")
            f.write(f"Size: {size} bytes\n")
            f.write(f"Range: {func.start_ea:#x} - {func.end_ea:#x}\n\n")
            
            # Count xrefs
            xrefs_to = list(idautils.XrefsTo(func.start_ea))
            f.write(f"Called by: {len(xrefs_to)} locations\n")
            
            # Count calls inside
            calls_count = 0
            for ea in idautils.FuncItems(func.start_ea):
                if idc.print_insn_mnem(ea) == 'call':
                    calls_count += 1
            f.write(f"Makes {calls_count} calls\n\n")
            
            # Disassembly
            f.write("Disassembly:\n")
            f.write("-" * 70 + "\n")
            
            ea = func.start_ea
            instr_count = 0
            while ea < func.end_ea and instr_count < 100:  # Limit to 100 instructions
                disasm = idc.generate_disasm_line(ea, 0)
                comment = idc.get_cmt(ea, 0) or idc.get_cmt(ea, 1)
                
                if comment:
                    f.write(f"{ea:#x}: {disasm:50s} ; {comment}\n")
                else:
                    f.write(f"{ea:#x}: {disasm}\n")
                
                ea = idc.next_head(ea)
                instr_count += 1
                if ea == idc.BADADDR:
                    break
            
            if ea < func.end_ea:
                f.write(f"\n... (truncated, {size} bytes total)\n")
            
            f.write("\n")
        
        f.write("\n=== Success ===\n")
        
except Exception as e:
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"ERROR: {str(e)}\n")
        import traceback
        f.write(traceback.format_exc())

idc.qexit(0)
