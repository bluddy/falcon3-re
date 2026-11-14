"""Read-only: for far-call targets into R05 that are mid-body, compare same-offset bytes/flags in R27/R28/R29."""
import json, traceback
import idaapi, idc, ida_bytes, ida_funcs
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\variant_probe.json"
V = {"R05": (0x2e100, 0x388f0), "R27": (0x10c9e0, 0x4b40), "R28": (0x111530, 0xae80), "R29": (0x11c3c0, 0x388f0)}
R = {"rows": []}
try:
    S = json.load(open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\segbase.json"))
    seen = set()
    for x in S["calls"]:
        t = x["t"]
        if not (0x2e100 <= t < 0x669f0) or x["bytes"][:2] != "9a" or t in seen:
            continue
        seen.add(t)
        off = t - 0x2e100
        row = {"t": t, "off": off, "caller": x["ea"], "cseg": x["cseg"], "v": {}}
        for n, (b, l) in V.items():
            if off >= l:
                continue
            ea = b + off
            fl = ida_bytes.get_flags(ea)
            f = ida_funcs.get_func(ea)
            row["v"][n] = {"bytes": (idc.get_bytes(ea, 8) or b"").hex(), "code": ida_bytes.is_code(fl),
                           "head": ida_bytes.get_item_head(ea) == ea, "unk": ida_bytes.is_unknown(fl),
                           "fstart": f.start_ea == ea if f else None,
                           "dis": idc.generate_disasm_line(ea, 0) if ida_bytes.is_code(fl) else None}
        R["rows"].append(row)
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
