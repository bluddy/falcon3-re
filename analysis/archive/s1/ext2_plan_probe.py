"""Plan probe (COPY, DBFL_KILL): try extending five functions over their fl_F continuation.  Output: analysis/s1/ext2_plan.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\ext2_plan.json"
# (func, run_lo, run_hi)
EXT = [(0x10CC60, 0x10CC8E, 0x10CE05), (0x2D31A, 0x2D353, 0x2D375), (0x3F6A9, 0x3F6C7, 0x3F6D6),
       (0x2142E, 0x215FE, 0x21631), (0x2520B, 0x25220, 0x25224)]


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


R = {"rows": []}
try:
    before = {fs: (idaapi.get_name(fs), chunks(fs)) for fs in idautils.Functions()}
    for fs, lo, hi in EXT:
        f = ida_funcs.get_func(fs)
        row = {"func": hex(fs), "chunks_before": chunks(fs), "end_before": hex(f.end_ea), "flags_before": hex(f.flags)}
        # the chunk that ends at lo
        tail_end = None
        for c in chunks(fs):
            if int(c[1], 16) == lo:
                tail_end = c
        row["chunk_ending_at_run"] = tail_end
        main_ends_at_run = f.end_ea == lo
        row["main_ends_at_run"] = main_ends_at_run
        if main_ends_at_run:
            row["method"] = "set_func_end"
            row["ok"] = bool(ida_funcs.set_func_end(fs, hi))
        else:
            row["method"] = "append_func_tail"
            row["ok"] = bool(ida_funcs.append_func_tail(f, lo, hi))
        f = ida_funcs.get_func(fs)
        row.update(end_after=hex(f.end_ea), chunks_after=chunks(fs), noncode=noncode(lo, hi),
                   owner_of_run_start=hex(ida_funcs.get_func(lo).start_ea) if ida_funcs.get_func(lo) else None,
                   flags_after=hex(f.flags))
        R["rows"].append(row)
    after = {fs: (idaapi.get_name(fs), chunks(fs)) for fs in idautils.Functions()}
    touched = {e for e, _, _ in EXT}
    R["changed_other"] = [hex(k) for k in before if k not in touched and before[k] != after.get(k)]
    R["new"] = sorted(hex(k) for k in after if k not in before)
    R["n"] = [len(before), len(after)]
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
