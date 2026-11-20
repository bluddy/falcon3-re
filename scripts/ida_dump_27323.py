import idaapi
import idautils
import idc

idaapi.auto_wait()

out_path = r"C:\Users\yotam\projects\falcon3\analysis\ida_sub27323.txt"
with open(out_path, "w") as f:
    func = idaapi.get_func(0x27323)
    name = idaapi.get_func_name(func.start_ea)
    f.write(f"FUNCTION: {name} (0x{func.start_ea:x} - 0x{func.end_ea:x})\n")
    ea = func.start_ea
    while ea < func.end_ea:
        dis = idc.generate_disasm_line(ea, 0)
        f.write(f"  0x{ea:05x}: {dis}\n")
        ea = idc.next_head(ea, func.end_ea)

idc.qexit(0)
