"""Read-only (DBFL_KILL): sub-classify the survey_mid 'after_ret_or_jmp(merged_fn)' targets.
For each call target t inside function g where the previous head is a ret/jmp and nothing falls into t:
  pure_split   no code xref into t from inside g except the calls (so [g.start, t) and [t, g.end) are independent)
  shared_tail  some jmp/jcc inside g (other than a call) reaches t: t is a tail of g, not a separate function
  multi_chunk  g has tail chunks (t may be in a tail chunk)
Output: analysis/s1/merged_split.json  (counts, size histogram, first 40 samples per class)"""
import json, collections, traceback
import idaapi, idautils, idc, ida_funcs, ida_bytes, ida_ua, ida_idp
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\merged_split.json"
R = {"cls": collections.Counter(), "sites": collections.Counter(), "samples": collections.defaultdict(list)}
try:
    tg = collections.defaultdict(list)
    for fea in idautils.Functions():
        for item in idautils.FuncItems(fea):
            insn = ida_ua.insn_t()
            if not ida_ua.decode_insn(insn, item) or not ida_idp.is_call_insn(insn):
                continue
            if insn.ops[0].type not in (idaapi.o_near, idaapi.o_far):
                continue
            for t in idautils.CodeRefsFrom(item, 0):
                g = ida_funcs.get_func(t)
                if g and g.start_ea != t:
                    tg[t].append(item)
    for t, frm in tg.items():
        g = ida_funcs.get_func(t)
        if ida_bytes.get_item_head(t) != t:
            continue
        prev = idc.prev_head(t, g.start_ea)
        pm = idc.print_insn_mnem(prev) if prev != idaapi.BADADDR else ""
        if pm not in ("retn", "retf", "iret", "jmp", "jmpf"):
            continue
        if any(x == prev for x in idautils.CodeRefsTo(t, 1)):
            continue
        inner = []
        for x in idautils.XrefsTo(t, 0):
            if not x.iscode:
                continue
            f2 = ida_funcs.get_func(x.frm)
            if f2 and f2.start_ea == g.start_ea:
                m = idc.print_insn_mnem(x.frm)
                if m not in ("call", "callf"):
                    inner.append((x.frm, m))
        chunks = []
        it = ida_funcs.func_tail_iterator_t(g)
        ok = it.main()
        while ok:
            c = it.chunk(); chunks.append((c.start_ea, c.end_ea)); ok = it.next()
        in_tail = not (g.start_ea <= t < g.end_ea)
        k = "shared_tail" if inner else ("multi_chunk" if len(chunks) > 1 else "pure_split")
        R["cls"][k] += 1
        R["sites"][k] += len(frm)
        if len(R["samples"][k]) < 40:
            R["samples"][k].append({"t": "%X" % t, "fn": "%X" % g.start_ea, "name": idc.get_func_name(g.start_ea),
                                    "fn_end": "%X" % g.end_ea, "tail_len": g.end_ea - t, "chunks": len(chunks),
                                    "callers": len(frm), "inner": ["%X:%s" % x for x in inner[:4]]})
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
