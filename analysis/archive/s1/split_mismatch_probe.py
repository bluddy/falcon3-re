"""split_mismatch_probe.py: find which split_funcs entries are in mismatch state."""
import os, json, hashlib, traceback
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, idc, idautils, idaapi

ROOT = r"C:\Users\ybarnoy\projects\falcon3"
MANIFEST = ROOT + r"\registry\orphan_funcs_expected.json"
OUT = ROOT + r"\analysis\s1\split_mismatch.json"

def sha(ea, end):
    return hashlib.sha256(ida_bytes.get_bytes(ea, end - ea)).hexdigest()

def chunks(ea):
    f = ida_funcs.get_func(ea)
    if not f or f.start_ea != ea:
        return None
    out, it = [], ida_funcs.func_tail_iterator_t(f)
    ok = it.main()
    while ok:
        out.append([it.chunk().start_ea, it.chunk().end_ea])
        ok = it.next()
    return sorted(out)

def sp_state(x):
    ea, at, end = x["ea"], x["at"], x["end"]
    h1 = sha(ea, at)
    h2 = sha(at, end)
    sha_ok = (h1 == x["sha256_head"], h2 == x["sha256_tail"])
    fo = ida_funcs.get_func(ea)
    ft = ida_funcs.get_func(at)
    return {
        "ea": "0x%X" % ea, "at": "0x%X" % at, "end": "0x%X" % end,
        "sha_head_ok": sha_ok[0], "sha_tail_ok": sha_ok[1],
        "owner_ea": "0x%X" % fo.start_ea if fo else None,
        "owner_end": "0x%X" % fo.end_ea if fo else None,
        "tail_ea": "0x%X" % ft.start_ea if ft else None,
        "tail_end": "0x%X" % ft.end_ea if ft else None,
        "chunks_owner": chunks(ea),
    }

try:
    doc = json.loads(open(MANIFEST, encoding="utf-8").read().replace("\r\n", "\n"))
    results = []
    mismatch = []
    for x in doc.get("split_funcs", []):
        s = sp_state(x)
        if (s["sha_head_ok"] and s["sha_tail_ok"]
                and s["owner_end"] == s["at"]
                and s["tail_ea"] == s["at"] and s["tail_end"] == s["end"]
                and s["chunks_owner"] == [[x["ea"], x["at"]]]):
            results.append({"state": "applied", **s})
        elif (s["sha_head_ok"] and s["sha_tail_ok"]
              and s["owner_end"] == s["end"]
              and s["chunks_owner"] == [[x["ea"], x["end"]]]):
            results.append({"state": "fresh", **s})
            mismatch.append({"state": "fresh", **s})
        else:
            results.append({"state": "MISMATCH", **s})
            mismatch.append({"state": "MISMATCH", **s})
    applied = sum(1 for r in results if r["state"] == "applied")
    open(OUT, "w").write(json.dumps({
        "total": len(results), "applied": applied, "mismatch_count": len(mismatch),
        "mismatches": mismatch
    }, indent=1))
except Exception:
    open(OUT, "w").write(json.dumps({"error": traceback.format_exc()}))

idc.qexit(0)
