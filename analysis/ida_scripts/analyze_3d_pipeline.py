import idaapi
import idc
import idautils

idaapi.auto_wait()

output_path = "analysis/ida_scripts/3d_pipeline_analysis.txt"

with open(output_path, "w") as f:
    f.write("=== 3D Object Rendering Pipeline Analysis ===\n\n")
    
    # 1. Disassemble object_proj_draw_dispatch (0x26B2E)
    f.write("--- Function: object_proj_draw_dispatch (0x26B2E) ---\n")
    cur = 0x26B2E
    end = 0x26C25
    while cur < end:
        dis = idc.generate_disasm_line(cur, 0)
        cmt = idc.get_cmt(cur, 0) or ''
        f.write(f"0x{cur:08X}: {dis:45s} ; {cmt}\n")
        cur = idc.next_head(cur, end)

    # 2. Disassemble polygon visibility / draw dispatcher at 0x2978E
    f.write("\n--- Function: poly_visibility_and_draw at 0x2978E ---\n")
    cur = 0x2978E
    end = cur + 0x200
    while cur < end:
        dis = idc.generate_disasm_line(cur, 0)
        cmt = idc.get_cmt(cur, 0) or ''
        f.write(f"0x{cur:08X}: {dis:45s} ; {cmt}\n")
        if 'ret' in dis or 'retf' in dis:
            # check if next is start of new function
            flags = idc.get_func_flags(cur)
            f.write(f"--- End of function / block at 0x{cur:08X} ---\n\n")
            break
        cur = idc.next_head(cur, end)

    # 3. Disassemble the jump target loc_298C4 (when not culled / when rendered)
    f.write("\n--- Target loc_298C4 (polygon rasterization setup) ---\n")
    cur = 0x298C4
    end = cur + 0x150
    while cur < end:
        dis = idc.generate_disasm_line(cur, 0)
        cmt = idc.get_cmt(cur, 0) or ''
        f.write(f"0x{cur:08X}: {dis:45s} ; {cmt}\n")
        if 'ret' in dis or 'retf' in dis:
            f.write(f"--- End of block at 0x{cur:08X} ---\n")
            break
        cur = idc.next_head(cur, end)

print("Analysis complete.")
idc.qexit(0)
