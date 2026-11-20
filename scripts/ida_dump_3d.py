import idaapi
import idautils
import idc

idaapi.auto_wait()

funcs_to_dump = [
    0x264c5,
    0x2676d,
    0x268dd,
    0x26b2e,
    0x26c4a,
    0x286ce,
    0x28774,
    0x4aae2,
    0x4aec4
]

out_path = r"C:\Users\yotam\projects\falcon3\analysis\ida_3d_disasm.txt"
with open(out_path, "w") as f:
    # Check references to aObjects (0x2ea40)
    f.write("=== Refs to aObjects (0x2ea40) ===\n")
    for xref in idautils.XrefsTo(0x2ea40):
        f.write(f"  xref from 0x{xref.frm:x}\n")
    for dref in idautils.DataRefsTo(0x2ea40):
        f.write(f"  dref from 0x{dref:x}\n")

    for f_ea in funcs_to_dump:
        func = idaapi.get_func(f_ea)
        if not func:
            f.write(f"\nFunction at 0x{f_ea:x} not found!\n")
            continue
        name = idaapi.get_func_name(func.start_ea)
        f.write(f"\n========================================\n")
        f.write(f"FUNCTION: {name} (0x{func.start_ea:x} - 0x{func.end_ea:x})\n")
        f.write(f"========================================\n")
        
        # Disassemble all instructions
        ea = func.start_ea
        while ea < func.end_ea:
            dis = idc.generate_disasm_line(ea, 0)
            f.write(f"  0x{ea:05x}: {dis}\n")
            ea = idc.next_head(ea, func.end_ea)

idc.qexit(0)
