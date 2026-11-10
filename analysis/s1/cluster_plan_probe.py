"""Plan probe (COPY, DBFL_KILL): extend sub_12C518 -> 12C66A and sub_12C7C6 -> 12C951 (set_func_end), add
12C683..12C7C6, 12C951..12C970, 12CCE9..12CE9D, 12C4F2..12C504, 12C9D0..12C9DF.  Reports spans, chunks,
non-code heads inside each, and any change to other functions.  Output: analysis/s1/cluster_plan.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\cluster_plan.json"
EXT = [(0x12C518, 0x12C66A), (0x12C7C6, 0x12C951)]
ADD = [(0x12C683, 0x12C7C6), (0x12C951, 0x12C970), (0x12CCE9, 0x12CE9D), (0x12C4F2, 0x12C504), (0x12C9D0, 0x12C9DF)]


def chunks(ea):
    f = ida_funcs.get_func(ea)
    out, it = [], ida_funcs.func_tail_iterator_t(f)
    ok = it.main()
    while ok:
        out.append([hex(it.chunk().start_ea), hex(it.chunk().end_ea)])
        ok = it.next()
    return sorted(out)


def noncode(lo, hi):
    out, a = [], lo
    while a < hi:
        h = ida_bytes.get_item_head(a)
        if not ida_bytes.is_code(ida_bytes.get_flags(h)):
            out.append(hex(h))
        a = h + max(ida_bytes.get_item_size(h), 1)
    return out


R = {"ext": [], "add": []}
try:
    before = {fs: (idaapi.get_name(fs), chunks(fs)) for fs in idautils.Functions()}
    for ea, end in EXT:
        f = ida_funcs.get_func(ea)
        row = {"ea": hex(ea), "end_before": hex(f.end_ea), "chunks_before": chunks(ea)}
        row["ok"] = bool(ida_funcs.set_func_end(ea, end))
        f = ida_funcs.get_func(ea)
        row.update(end_after=hex(f.end_ea), chunks_after=chunks(ea), noncode=noncode(ea, f.end_ea))
        R["ext"].append(row)
    for ea, end in ADD:
        row = {"ea": hex(ea), "end": hex(end), "owned_before": [hex(a) for a in range(ea, end) if ida_funcs.get_func(a)][:3]}
        row["ok"] = bool(ida_funcs.add_func(ea, end))
        if row["ok"]:
            f = ida_funcs.get_func(ea)
            row.update(end_after=hex(f.end_ea), chunks=chunks(ea), noncode=noncode(ea, end),
                       last=idc.generate_disasm_line(idc.prev_head(end, ea), 0))
        R["add"].append(row)
    after = {fs: (idaapi.get_name(fs), chunks(fs)) for fs in idautils.Functions()}
    touched = {e for e, _ in EXT}
    R["changed_other"] = [hex(k) for k in before if k not in touched and before[k] != after.get(k)]
    R["new"] = sorted(hex(k) for k in after if k not in before)
    R["n"] = [len(before), len(after)]
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
