"""Find the 14 mismatched manifest entries."""
import os; os.environ["DBFL_KILL"] = "1"
import json, hashlib, traceback
import ida_bytes, ida_funcs, idc, idaapi, idautils

ROOT = r"C:\Users\ybarnoy\projects\falcon3"
MANIFEST = ROOT + r"\registry\orphan_funcs_expected.json"
OUT = ROOT + r"\analysis\s1\states_debug.txt"

def sha(ea, end):
    return hashlib.sha256(ida_bytes.get_bytes(ea, end - ea)).hexdigest()

def chunks(ea):
    f = ida_funcs.get_func(ea)
    if not f or f.start_ea != ea: return None
    out, it = [], ida_funcs.func_tail_iterator_t(f)
    ok = it.main()
    while ok:
        out.append([it.chunk().start_ea, it.chunk().end_ea]); ok = it.next()
    return sorted(out)

def sp_state(x):
    ea, at, end = x["ea"], x["at"], x["end"]
    if sha(ea, at) != x["sha256_head"] or sha(at, end) != x["sha256_tail"]:
        return "mismatch:sha"
    fo = ida_funcs.get_func(ea)
    if not fo or fo.start_ea != ea: return "mismatch:no_fn"
    if fo.end_ea == at and chunks(ea) == [[ea, at]]:
        ft = ida_funcs.get_func(at)
        if ft and ft.start_ea == at: return "applied"
    if fo.end_ea == end and chunks(ea) == [[ea, end]]: return "fresh"
    return "mismatch:state ea=0x%X end=0x%X fo.end=0x%X" % (ea, end, fo.end_ea)

try:
    doc = json.loads(open(MANIFEST, encoding="utf-8").read().replace("\r\n", "\n"))
    out = open(OUT, "w")
    mismatch = []
    for x in doc.get("split_funcs", []):
        s = sp_state(x)
        if "mismatch" in s:
            mismatch.append("SPLIT ea=0x%X at=0x%X end=0x%X: %s" % (x["ea"], x["at"], x["end"], s))
    # Also check other types
    for x in doc.get("add_funcs", []):
        # basic check
        f = ida_funcs.get_func(x["ea"])
        if not f or f.start_ea != x["ea"]:
            mismatch.append("ADD ea=0x%X: no function" % x["ea"])
    out.write("Total mismatches: %d\n" % len(mismatch))
    for m in mismatch:
        out.write(m + "\n")
    out.close()
except Exception:
    open(OUT, "w").write(traceback.format_exc())
idc.qexit(0)
