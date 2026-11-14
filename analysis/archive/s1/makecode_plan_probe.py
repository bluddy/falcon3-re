"""Plan probe (run on a COPY, DBFL_KILL): re-decode the 5 ranges after cut call sites.  Records the item layout
before and after del_items + sequential create_insn.  Output: analysis/s1/makecode_plan.json"""
import hashlib, json, traceback
import idaapi, idc, ida_bytes, ida_funcs, ida_ua
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\makecode_plan.json"
RANGES = [(0x2F99E, 0x2F9AC), (0x326FF, 0x32700), (0x3273E, 0x32740), (0x32A43, 0x32A44), (0x32AA1, 0x32AA2)]


def kind(ea):
    fl = ida_bytes.get_flags(ea)
    if ida_bytes.is_code(fl):
        return "code"
    if ida_bytes.is_align(fl):
        return "align"
    return "data"


def layout(lo, hi):
    out, ea = [], ida_bytes.get_item_head(lo)
    while ea < hi:
        out.append([ea, ida_bytes.get_item_size(ea), kind(ea)])
        ea += ida_bytes.get_item_size(ea)
    return out


R = {"ranges": []}
try:
    for lo, hi in RANGES:
        f = ida_funcs.get_func(lo)
        row = {"ea": lo, "end": hi, "owner": f.start_ea, "sha256": hashlib.sha256(ida_bytes.get_bytes(lo, hi - lo)).hexdigest(),
               "before": layout(lo, hi)}
        # items that straddle lo/hi would change the neighbours; record them
        row["head_lo"] = ida_bytes.get_item_head(lo)
        row["tail_end"] = ida_bytes.get_item_head(hi - 1) + ida_bytes.get_item_size(hi - 1)
        ida_bytes.del_items(lo, ida_bytes.DELIT_SIMPLE, hi - lo)
        ea = lo
        while ea < hi:
            n = ida_ua.create_insn(ea)
            if n <= 0:
                row["fail"] = ea
                break
            ea += n
        row["after"] = layout(lo, hi)
        row["reached_end"] = ea
        row["owner_after"] = ida_funcs.get_func(lo).start_ea
        row["disasm"] = [idc.generate_disasm_line(a, 0) for a, _s, _k in row["after"]]
        R["ranges"].append(row)
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
