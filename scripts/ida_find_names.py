import idaapi
import idautils
import idc

idaapi.auto_wait()

out_path = r"C:\Users\yotam\projects\falcon3\analysis\ida_objects_loader.txt"
with open(out_path, "w") as f:
    target = 0x2ea40
    f.write(f"String at 0x{target:x}: {idc.get_strlit_contents(target)}\n")
    for xref in idautils.XrefsTo(target):
        f.write(f"Xref: 0x{xref.frm:x}\n")
    for dref in idautils.DataRefsTo(target):
        f.write(f"DataRef: 0x{dref:x}\n")

    # Search for functions with '3d' or 'render' or 'object' or 'model' in their names
    f.write("\nNamed 3D functions:\n")
    for ea, name in idautils.Names():
        nl = name.lower()
        if any(k in nl for k in ['falcobj', 'object', 'lod', 'draw_object', 'render_object', 'model']):
            f.write(f"  0x{ea:x}: {name}\n")

idc.qexit(0)
