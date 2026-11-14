"""Read-only (DBFL_KILL): every far tail chunk (>64K from owner) - owner, how the owner reaches it,
chunk disassembly, what precedes it. Output: analysis/s1/fartail_bak_defds.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes, ida_segment
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\fartail_bak_defds.json"
R = []
try:
    for fs in idautils.Functions():
        f = ida_funcs.get_func(fs)
        it = ida_funcs.func_tail_iterator_t(f)
        ok = it.main()
        while ok:
            c = it.chunk()
            if c.start_ea != f.start_ea and abs(c.start_ea - f.start_ea) > 0x10000:
                p = idc.prev_head(c.start_ea, 0)
                R.append({
                    "owner": fs, "owner_name": idc.get_func_name(fs), "owner_end": f.end_ea,
                    "owner_dis": [[h, idc.generate_disasm_line(h, 0), idc.get_bytes(h, idc.get_item_size(h)).hex()]
                                  for h in idautils.FuncItems(fs) if f.start_ea <= h < f.end_ea],
                    "lo": c.start_ea, "hi": c.end_ea,
                    "seg": ida_segment.get_segm_name(ida_segment.getseg(c.start_ea)),
                    "refs": [[x.frm, x.type, idc.get_func_name(x.frm)] for x in idautils.XrefsTo(c.start_ea, 0)],
                    "prev": [p, idc.generate_disasm_line(p, 0), idc.get_func_name(p) or "",
                             bool(ida_bytes.is_code(ida_bytes.get_flags(p)))],
                    "dis": [[h, idc.generate_disasm_line(h, 0)] for h in idautils.Heads(c.start_ea, c.end_ea)][:30],
                    "after": [c.end_ea, idc.generate_disasm_line(c.end_ea, 0), idc.get_func_name(c.end_ea) or ""],
                })
            ok = it.next()
except Exception:
    R.append({"error": traceback.format_exc()})
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
