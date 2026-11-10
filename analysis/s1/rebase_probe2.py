"""Read-only (DBFL_KILL): orphan run around 0x15CCB/0x15E42, thunk 0x2C013 -> 0x6CD90, 0x161945.
Output: analysis/s1/rebase_probe2.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\rebase_probe2.json"
R = {}


def run_bounds(ea):
    """orphan (function-less) code run containing ea"""
    lo = ea
    while True:
        p = idc.prev_head(lo, 0)
        if p == idaapi.BADADDR or not ida_bytes.is_code(ida_bytes.get_flags(p)) or ida_funcs.get_func(p):
            break
        lo = p
    hi = ea
    while ida_bytes.is_code(ida_bytes.get_flags(hi)) and not ida_funcs.get_func(hi):
        hi = idc.next_head(hi, idaapi.BADADDR)
    return lo, hi


def refs_into(lo, hi):
    out = []
    for h in idautils.Heads(lo, hi):
        for x in idautils.XrefsTo(h, 0):
            if x.type == 21 and lo <= x.frm < hi:
                continue                              # internal flow
            if lo <= x.frm < hi and x.iscode:
                continue                              # internal branch
            out.append([h, x.frm, x.type, bool(x.user), idc.get_func_name(x.frm) or "", idc.generate_disasm_line(x.frm, 0)])
    return out


try:
    for ea in (0x15CCB, 0x15E42):
        lo, hi = run_bounds(ea)
        R["run_%X" % ea] = {"lo": lo, "hi": hi, "f_before": idc.get_func_name(idc.prev_head(lo, 0)),
                            "f_after": idc.get_func_name(hi), "prev": idc.generate_disasm_line(idc.prev_head(lo, 0), 0),
                            "refs": refs_into(lo, hi),
                            "terminators": [[h, idc.generate_disasm_line(h, 0)] for h in idautils.Heads(lo, hi)
                                            if idc.print_insn_mnem(h) in ("jmp", "retn", "retf", "iret")][:60]}
    f = ida_funcs.get_func(0x2C013)
    ch, it = [], ida_funcs.func_tail_iterator_t(f)
    ok = it.main()
    while ok:
        ch.append([it.chunk().start_ea, it.chunk().end_ea])
        ok = it.next()
    R["thunk_2C013"] = {"func": [f.start_ea, f.end_ea, idc.get_func_name(f.start_ea)], "chunks": ch,
                        "dis": [[h, idc.generate_disasm_line(h, 0)] for h in idautils.Heads(0x2C000, 0x2C030)],
                        "bytes_6CD80": idc.get_bytes(0x6CD80, 0x60).hex(),
                        "refs_6CD90": [[x.frm, x.type, bool(x.user), idc.get_func_name(x.frm)] for x in idautils.XrefsTo(0x6CD90, 0)],
                        "f_6CD8E": idc.get_func_name(0x6CD8E),
                        "dis_6CD60": [[h, idc.generate_disasm_line(h, 0)] for h in idautils.Heads(0x6CD60, 0x6CDB8)]}
    tails = []
    for fs in idautils.Functions():
        f = ida_funcs.get_func(fs)
        it = ida_funcs.func_tail_iterator_t(f)
        ok = it.main()
        while ok:
            c = it.chunk()
            if c.start_ea != f.start_ea and abs(c.start_ea - f.start_ea) > 0x10000:
                tails.append([fs, idc.get_func_name(fs), c.start_ea, c.end_ea])
            ok = it.next()
    R["far_tails"] = tails
    R["dis_161930"] = [[h, idc.generate_disasm_line(h, 0)] for h in idautils.Heads(0x161930, 0x161980)]
    R["bytes_161940"] = idc.get_bytes(0x161940, 0x40).hex()
    R["refs_161946"] = [[x.frm, x.type, bool(x.user), idc.get_func_name(x.frm)] for x in idautils.XrefsTo(0x161946, 0)]
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
