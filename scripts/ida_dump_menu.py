import idaapi
import idautils
import idc

idaapi.auto_wait()

out_path = r"C:\Users\yotam\projects\falcon3\analysis\ida_menu_model.txt"
with open(out_path, "w") as f:
    # Function menu_3d_model_frame_step (0x4aae2)
    # and farobj_3d_model_rotate_step (0x4aec4)
    # These are the routines that draw the 3D model in the model viewer!
    for f_ea in [0x4aae2, 0x4aec4]:
        func = idaapi.get_func(f_ea)
        name = idaapi.get_func_name(func.start_ea)
        f.write(f"\n========================================\n")
        f.write(f"FUNCTION: {name} (0x{func.start_ea:x} - 0x{func.end_ea:x})\n")
        f.write(f"========================================\n")
        ea = func.start_ea
        while ea < func.end_ea:
            dis = idc.generate_disasm_line(ea, 0)
            f.write(f"  0x{ea:05x}: {dis}\n")
            ea = idc.next_head(ea, func.end_ea)

idc.qexit(0)
