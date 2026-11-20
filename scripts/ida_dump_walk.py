import idaapi
import idautils
import idc

idaapi.auto_wait()

out_path = r"C:\Users\yotam\projects\falcon3\analysis\ida_walk_disasm.txt"
with open(out_path, "w") as f:
    for ea_func in [0x272a2, 0x26c4a]:
        func = idaapi.get_func(ea_func)
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
