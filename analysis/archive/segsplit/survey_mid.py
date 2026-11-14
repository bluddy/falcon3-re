"""Read-only: classify direct calls whose target is inside a function body (not its start)."""
import json, collections, traceback
import idaapi, idautils, idc, ida_funcs, ida_bytes, ida_segment, ida_ua, ida_idp
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\segsplit\survey_mid.json"
R = {"cls": collections.Counter(), "samples": collections.defaultdict(list), "targets": 0}
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
    R["targets"] = len(tg)
    for t, frm in tg.items():
        g = ida_funcs.get_func(t)
        head = ida_bytes.get_item_head(t) == t
        prev = idc.prev_head(t, g.start_ea)
        pm = idc.print_insn_mnem(prev) if prev != idaapi.BADADDR else ""
        pfx = pm in ("retn", "retf", "iret", "jmp", "jmpf")
        # how is t reached inside g: does anything fall into t?
        fall = any(x == prev for x in idautils.CodeRefsTo(t, 1))
        ins = idc.print_insn_mnem(t)
        if not head:
            k = "not_head"
        elif pfx and not fall:
            k = "after_ret_or_jmp(merged_fn)"
        elif ins in ("push", "enter", "mov") and fall:
            k = "fallthrough_entry_proloque"
        elif fall:
            k = "fallthrough_secondary_entry"
        else:
            k = "other"
        seg = ida_segment.get_segm_name(ida_segment.getseg(t))
        R["cls"][k] += len(frm)
        R["cls"]["T:" + k] += 1
        if len(R["samples"][k]) < 12:
            R["samples"][k].append(["%X" % t, idc.get_func_name(g.start_ea), "%X" % g.start_ea, seg, pm, ins, len(frm)])
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
