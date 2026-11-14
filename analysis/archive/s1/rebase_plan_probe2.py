"""Read-only (DBFL_KILL): remaining facts for tools/plan_rebase_fixes.py.
Output: analysis/s1/rebase_plan_probe2.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes, ida_xref
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\rebase_plan_probe2.json"
R = {}


def fn(ea):
    f = ida_funcs.get_func(ea)
    return [f.start_ea, f.end_ea, idc.get_func_name(f.start_ea)] if f else None


try:
    R["byte_161945"] = idc.get_wide_byte(0x161945)
    R["far_2C96C"] = [[x.to, x.type, bool(x.user)] for x in idautils.XrefsFrom(0x2C96C, ida_xref.XREF_FAR) if x.iscode]
    R["fn_6812F"] = fn(0x6812F)
    R["refs_6812F"] = [[x.frm, x.type, bool(x.user), idc.get_func_name(x.frm)] for x in idautils.XrefsTo(0x6812F, 0)]
    R["fn_1AA05F"] = fn(0x1AA05F)
    R["refs_1AA05F"] = [[x.frm, x.type, bool(x.user)] for x in idautils.XrefsTo(0x1AA05F, 0)]
    R["dis_6DF20"] = [[h, idc.generate_disasm_line(h, 0), [[x.frm, x.type] for x in idautils.XrefsTo(h, 0) if x.iscode]]
                      for h in idautils.Heads(0x6DF1C, 0x6DF30)]
    R["dis_15BE0"] = [[h, idc.generate_disasm_line(h, 0)] for h in idautils.Heads(0x15BE0, 0x15BF0)]
    R["dis_15EA0"] = [[h, idc.generate_disasm_line(h, 0)] for h in idautils.Heads(0x15EA0, 0x15EC2)]
    R["bytes_6CD90"] = idc.get_bytes(0x6CD90, 24).hex()
    R["fn_6E7C7"] = [fn(0x6E7C6), fn(0x6E809)]
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
