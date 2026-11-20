import idaapi
import idautils
import idc

idaapi.auto_wait()

out_path = r"C:\Users\yotam\projects\falcon3\analysis\ida_objects_loader.txt"
with open(out_path, "w") as f:
    target = 0x2ea40
    f.write(f"Searching for references to 0x{target:x}...\n")
    for xref in idautils.XrefsTo(target):
        f.write(f"Xref: 0x{xref.frm:x}\n")
    for dref in idautils.DataRefsTo(target):
        f.write(f"DataRef: 0x{dref:x}\n")
    
    # Also search entire binary for immediate value 0x2ea40 (or offset)
    # Target in 16:16 or flat?
    # Let's search for bytes: 40 ea 02 00 or similar
    ea = idaapi.cvar.inf.min_ea
    while ea < idaapi.cvar.inf.max_ea:
        # search for 0x2ea40 as dword or word 0xea40
        w = idc.get_wide_word(ea)
        if w == (target & 0xFFFF):
            f.write(f"Found word 0x{w:04x} at 0x{ea:x}\n")
            func = idaapi.get_func(ea)
            if func:
                f.write(f"  in func 0x{func.start_ea:x}: {idaapi.get_func_name(func.start_ea)}\n")
        ea += 1
        if ea > 0x100000:
            break

idc.qexit(0)
