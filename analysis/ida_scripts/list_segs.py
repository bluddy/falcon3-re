import idaapi
import idc
import idautils

idaapi.auto_wait()

with open("analysis/ida_scripts/list_segs.txt", "w") as f:
    for seg_ea in idautils.Segments():
        seg = idaapi.getseg(seg_ea)
        name = idc.get_segm_name(seg_ea)
        f.write(f"Seg {name:15s} start=0x{seg.start_ea:08X} end=0x{seg.end_ea:08X}\n")

idc.qexit(0)
