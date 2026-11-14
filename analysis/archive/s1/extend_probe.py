"""Read-only (DBFL_KILL): for each function whose main chunk ends with flow into code owned by no
function, the natural extent of that orphan code: consecutive heads while the next head is reached
by flow, then where every jump inside it lands (inside the run / the function / elsewhere) and
every xref into it from outside.  Input: analysis/s1/extend_probe_in.json [func_ea...]
Output: analysis/s1/extend_probe.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes
IN = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\extend_probe_in.json"
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\extend_probe.json"
R = []
try:
    for fea in json.load(open(IN)):
        f = ida_funcs.get_func(fea)
        lo = f.end_ea
        ea, heads = lo, []
        while ida_bytes.is_code(ida_bytes.get_flags(ea)) and not ida_funcs.get_func(ea):
            heads.append(ea)
            nx = idc.next_head(ea, idaapi.BADADDR)
            if nx != ea + ida_bytes.get_item_size(ea) or not ida_bytes.is_flow(ida_bytes.get_flags(nx)):
                ea = ea + ida_bytes.get_item_size(ea)
                break
            ea = nx
        hi = ea
        jumps, inrefs = [], []
        for h in heads:
            for t in idautils.CodeRefsFrom(h, 0):
                if t == h + ida_bytes.get_item_size(h):
                    continue
                where = ("run" if lo <= t < hi else "func" if ida_funcs.get_func(t) and
                         ida_funcs.get_func(t).start_ea == fea else
                         "fn:%X" % ida_funcs.get_func(t).start_ea if ida_funcs.get_func(t) else "free")
                jumps.append([h, t, where, idc.print_insn_mnem(h)])
            for x in idautils.XrefsTo(h, 0):
                if not (lo <= x.frm < hi) and x.frm != idc.prev_head(lo, 0):
                    inrefs.append([h, x.frm, x.type])
        nf = ida_funcs.get_func(hi)
        R.append({"func": fea, "name": idc.get_func_name(fea), "lo": lo, "hi": hi,
                  "last": idc.generate_disasm_line(heads[-1], 0) if heads else None,
                  "after": [idc.generate_disasm_line(hi, 0), nf.start_ea if nf else None,
                            "C" if ida_bytes.is_code(ida_bytes.get_flags(hi)) else "D/U"],
                  "jumps": jumps, "inrefs": inrefs,
                  "noret": bool(f.flags & ida_funcs.FUNC_NORET),
                  "rets_in_run": [h for h in heads if idc.print_insn_mnem(h).startswith("ret")]})
except Exception:
    R = {"error": traceback.format_exc()}
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
