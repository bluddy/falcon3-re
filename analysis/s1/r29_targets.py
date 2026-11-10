"""Read-only: fresh-decode each distinct resolved arena target that is not a function start."""
import json, traceback
import idaapi, idc, ida_bytes, ida_funcs, ida_ua, ida_segment
D = "C:/Users/ybarnoy/projects/falcon3/analysis/s1/"
OUT = D + "r29_targets.json"
TERM = ("retn", "retf", "iret", "jmp", "jmpf", "jmpfi", "jmpni")
R = {"t": []}
try:
    A = json.load(open(D + "arena_resolve.json"))["rows"]
    seen = {}
    for r in A:
        if r["target"] is None or r["tstate"] == "F":
            continue
        seen.setdefault(r["target"], []).append(r["ea"])
    for t, callers in sorted(seen.items()):
        x, run, term, kinds = t, 0, None, set()
        while run < 400:
            insn = ida_ua.insn_t()
            n = ida_ua.decode_insn(insn, x)
            if n <= 0:
                term = "undecodable"; break
            fl = ida_bytes.get_flags(x)
            kinds.add("data" if ida_bytes.is_data(fl) else "code" if ida_bytes.is_code(fl) else "unk")
            f = ida_funcs.get_func(x)
            if f and x != t:
                kinds.add("fn")
            run += 1
            m = insn.get_canon_mnem()
            if m in TERM:
                term = m; x += n; break
            x += n
        f = ida_funcs.get_func(t)
        R["t"].append({"t": t, "n": len(callers), "callers": callers[:4], "run": run, "term": term, "end": x,
                       "kinds": sorted(kinds), "infn": f.start_ea if f else None,
                       "seg": ida_segment.get_segm_name(ida_segment.getseg(t)),
                       "bytes": (idc.get_bytes(t, 8) or b"").hex()})
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
