"""Read-only (DBFL_KILL): bytes, item heads and owners of the untiled gaps inside the register
ranges the re-baseline re-derives (finding 124).
Input:  analysis/s1/gap_probe_in.json  [[lo, hi]...]
Output: analysis/s1/gap_probe.json     [{lo, hi, sha256, heads: [[ea, cls, size, func, disasm]]}]"""
import hashlib, json, traceback
import idaapi, idc, ida_funcs, ida_bytes
IN = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\gap_probe_in.json"
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\gap_probe.json"
R = []
try:
    for lo, hi in json.load(open(IN)):
        rows, ea = [], lo
        while ea < hi:
            fl = ida_bytes.get_flags(ea)
            h = ida_bytes.get_item_head(ea)
            sz = max(1, ida_bytes.get_item_size(h))
            f = ida_funcs.get_func(ea)
            rows.append([h, "C" if ida_bytes.is_code(fl) else "D" if ida_bytes.is_data(fl) else "U", sz,
                         f.start_ea if f else None, idc.generate_disasm_line(h, 0)])
            ea = h + sz if h + sz > ea else ea + 1
        raw = ida_bytes.get_bytes(lo, hi - lo) or b""
        R.append({"lo": lo, "hi": hi, "sha256": hashlib.sha256(raw).hexdigest(), "hex": raw.hex(),
                  "heads": rows})
except Exception:
    R = {"error": traceback.format_exc()}
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
