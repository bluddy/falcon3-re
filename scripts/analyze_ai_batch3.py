import idaapi
import idc
import idautils

idaapi.auto_wait()

output_path = r"C:\Users\ybarnoy\projects\falcon3\temp\ai_batch3_analysis.txt"

# Batch 3: More AI helper functions
functions_to_analyze = [
    (0x40C0A, "ai_distance_range_check"),
    (0x40C2A, "ai_vector_accumulate"),
    (0x40C54, "ai_vector_accumulate_alt"),
    (0x40C6A, "ai_angle_from_offset"),
    (0x3E8C5, "ai_angle_calculate"),
    (0x3FB5E, "ai_angle_calculate_helper"),
    (0x3F07D, "ai_movement_vector_accumulate"),
    (0x428F6, "ai_index_bounds_check"),
]

try:
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=== AI Function Batch 3 Analysis ===\n\n")
        
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
            
            # Check if it's a leaf function (no calls)
            calls_count = 0
            for ea in idautils.FuncItems(func.start_ea):
                if idc.print_insn_mnem(ea) == 'call':
                    calls_count += 1
            
            if calls_count == 0:
                f.write(f"LEAF FUNCTION (no calls)\n\n")
            else:
                f.write(f"Makes {calls_count} calls\n\n")
            
            # Disassembly - full for small functions, truncated for large
            f.write("Disassembly:\n")
            f.write("-" * 70 + "\n")
            
            max_instructions = 80 if size < 200 else 50
            ea = func.start_ea
            instr_count = 0
            while ea < func.end_ea and instr_count < max_instructions:
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
