"""Read-only (DBFL_KILL) after S1a: (1) each distinct planned cref target that is not a function start:
state, fresh decode run; (2) R05-arena functions whose callers were all re-pointed by S1a."""
import json, traceback, collections
import idaapi, idautils, idc, ida_bytes, ida_funcs, ida_ua, ida_segment, ida_xref
ROOT = "C:/Users/ybarnoy/projects/falcon3/"
OUT = ROOT + "analysis/s1/s1a_after.json"
TERM = ("retn", "retf", "iret", "jmp", "jmpf", "jmpfi", "jmpni")
R = {"targets": [], "orphans": []}
def run_from(t):
    x, run, term, kinds = t, 0, None, set()
    while run < 600:
        insn = ida_ua.insn_t(); n = ida_ua.decode_insn(insn, x)
        if n <= 0:
            term = "undecodable"; break
        fl = ida_bytes.get_flags(x)
        kinds.add("data" if ida_bytes.is_data(fl) else "code" if ida_bytes.is_code(fl) else "unk")
        f = ida_funcs.get_func(x)
        if f and x != t: kinds.add("fn")
        run += 1; m = insn.get_canon_mnem(); x += n
        if m in TERM:
            term = m; break
    return run, term, x, sorted(kinds)
try:
    doc = json.load(open(ROOT + "registry/variant_sel_expected.json"))
    tg = collections.defaultdict(list)
    for c in doc["crefs"]:
        tg[c["to"]].append(c["ea"])
    for t, cs in sorted(tg.items()):
        f = ida_funcs.get_func(t)
        if f and f.start_ea == t:
            continue
        fl = ida_bytes.get_flags(t)
        run, term, end, kinds = run_from(t)
        R["targets"].append({"t": t, "n": len(cs), "callers": cs[:4], "state": "head" if ida_bytes.is_code(fl) and ida_bytes.get_item_head(t) == t else "code-mid" if ida_bytes.is_code(fl) else "data" if ida_bytes.is_data(fl) else "unk",
                             "infn": f.start_ea if f else None, "seg": ida_segment.get_segm_name(ida_segment.getseg(t)),
                             "bytes": (idc.get_bytes(t, 8) or b"").hex(), "run": run, "term": term, "end": end, "kinds": kinds})
    old = collections.Counter()
    for c in doc["crefs"]:
        for to, ty, u in c["before"]:
            if to != c["to"]:
                old[to] += 1
    for t, n in sorted(old.items()):
        f = ida_funcs.get_func(t)
        if not f or f.start_ea != t:
            continue
        left = [x.frm for x in idautils.XrefsTo(t, 0) if x.iscode and x.type in (ida_xref.fl_CF, ida_xref.fl_JF, ida_xref.fl_CN, ida_xref.fl_JN)]
        R["orphans"].append({"t": t, "end": f.end_ea, "name": idc.get_func_name(t), "lost": n, "left": len(left),
                             "seg": ida_segment.get_segm_name(ida_segment.getseg(t)), "bytes": (idc.get_bytes(t, 8) or b"").hex()})
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
