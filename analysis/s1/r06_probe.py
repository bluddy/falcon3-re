"""Read-only (DBFL_KILL): 5CD9 arena variants - segment bounds, selector bases, code at offsets 0 and 0xF,
and every far xref into selector 0x6CD9. Output: analysis/s1/r06_probe.json"""
import json, traceback
import idaapi, idc, idautils, ida_segment, ida_bytes, ida_funcs
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\r06_probe.json"
R = {"segs": [], "sel_6CD9": None}
try:
    for s in idautils.Segments():
        sg = ida_segment.getseg(s)
        nm = ida_segment.get_segm_name(sg)
        if "5CD9" in nm or "569F" in nm and sg.start_ea < 0x70000:
            base = ida_segment.get_segm_base(sg)
            ent = {"name": nm, "lo": sg.start_ea, "hi": sg.end_ea, "sel": sg.sel, "base": base}
            for off in (0, 0xF, 0x10, 0x18):
                ea = base + off
                ent["o%X" % off] = [ea, idc.generate_disasm_line(ea, 0), idc.get_func_name(ea) or "",
                                    idc.get_bytes(ea, 8).hex() if idc.get_bytes(ea, 8) else ""]
            R["segs"].append(ent)
    sel = ida_segment.find_selector(0x6CD9)
    R["sel_6CD9"] = [sel, ida_segment.sel2para(sel)]
    # ida_overlay_dump knowledge: any segment whose base para is 0x6CD9
    R["base_6CD9"] = [ida_segment.get_segm_name(ida_segment.getseg(s)) for s in idautils.Segments()
                      if ida_segment.get_segm_base(ida_segment.getseg(s)) == 0x6CD90]
    R["xrefs_6CD90"] = [[x.frm, x.type, idc.get_func_name(x.frm)] for x in idautils.XrefsTo(0x6CD90, 0)]
    R["xrefs_6CD9F"] = [[x.frm, x.type, idc.get_func_name(x.frm)] for x in idautils.XrefsTo(0x6CD9F, 0)]
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
