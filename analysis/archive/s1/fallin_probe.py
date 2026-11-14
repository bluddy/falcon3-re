"""fallin_probe.py: enumerate fall-in entries (fallthrough_entry_proloque and fallthrough_secondary_entry)
and show their disassembly context.  Also enumerate the 'other' targets to explain the increase.
Output: analysis/s1/fallin_all.json
"""
import os
os.environ["DBFL_KILL"] = "1"
import json
import collections
import traceback

import idaapi
import ida_bytes
import ida_funcs
import ida_ua
import ida_idp
import ida_segment
import idc
import idautils

OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\fallin_all.json"
RETS = {"retn", "retf", "iret", "iretw", "retnw", "retfw"}

def chunks(ea):
    f = ida_funcs.get_func(ea)
    if not f or f.start_ea != ea: return None
    out, it = [], ida_funcs.func_tail_iterator_t(f)
    ok = it.main()
    while ok:
        out.append([it.chunk().start_ea, it.chunk().end_ea]); ok = it.next()
    return sorted(out)

def disasm_range(lo, hi, max_insns=4):
    out = []
    a = lo
    while a < hi and len(out) < max_insns:
        if ida_bytes.is_code(ida_bytes.get_flags(a)) and ida_bytes.get_item_head(a) == a:
            out.append({"ea": "%X" % a, "text": idc.generate_disasm_line(a, 0)})
            a += ida_bytes.get_item_size(a)
        else:
            out.append({"ea": "%X" % a, "text": "db %02X" % (ida_bytes.get_byte(a) & 0xFF)})
            a += 1
    return out

try:
    # collect every call target that lands inside a function (not at start)
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

    results = {"fallthrough_entry_proloque": [], "fallthrough_secondary_entry": [], 
               "not_head": [], "other": [], "after_ret_or_jmp": []}

    for t, callers in tg.items():
        g = ida_funcs.get_func(t)
        if not g:
            continue
        # must be on an instruction head
        if ida_bytes.get_item_head(t) != t:
            results["not_head"].append({
                "t": "%X" % t, "fn": "%X" % g.start_ea, "fn_name": idc.get_func_name(g.start_ea) or "",
                "fn_end": "%X" % g.end_ea, "callers": len(callers)})
            continue

        prev = idc.prev_head(t, g.start_ea)
        pm = idc.print_insn_mnem(prev) if prev != idaapi.BADADDR else ""
        
        # check for fall-through (no ret/jmp before t)
        has_fallthru = any(x == prev for x in idautils.CodeRefsTo(t, 1))
        
        if pm in ("retn", "retf", "iret", "jmp", "jmpf") and not has_fallthru:
            # merged function (after ret/jmp, no fall-through)
            results["after_ret_or_jmp"].append({
                "t": "%X" % t, "fn": "%X" % g.start_ea, "callers": len(callers)})
            continue
        
        if has_fallthru or pm not in ("retn", "retf", "iret", "jmp", "jmpf"):
            # check if t has a function prologue (push bp, enter, or similar)
            first_mnem = idc.print_insn_mnem(t) if ida_bytes.is_code(ida_bytes.get_flags(t)) else ""
            has_prologue = first_mnem in ("push", "enter", "sub", "mov") and "bp" in idc.generate_disasm_line(t, 0)
            
            cat = "fallthrough_entry_proloque" if has_prologue else "fallthrough_secondary_entry"
            s = ida_segment.getseg(t)
            seg_name = ida_segment.get_segm_name(s) if s else "?"
            results[cat].append({
                "t": "%X" % t, "fn": "%X" % g.start_ea, "fn_name": idc.get_func_name(g.start_ea) or "",
                "fn_end": "%X" % g.end_ea, "callers": len(callers),
                "seg": seg_name,
                "prev_mnem": pm,
                "first_mnem": first_mnem,
                "disasm_at_prev": disasm_range(idc.prev_head(idc.prev_head(t, g.start_ea), g.start_ea) if prev != idaapi.BADADDR else t, t+4, 3),
                "disasm_at_t": disasm_range(t, min(t+16, g.end_ea), 4)
            })
            continue
        
        # other
        results["other"].append({
            "t": "%X" % t, "fn": "%X" % g.start_ea, "fn_name": idc.get_func_name(g.start_ea) or "",
            "fn_end": "%X" % g.end_ea, "callers": len(callers),
            "prev_mnem": pm,
            "disasm_at_t": disasm_range(t, min(t+8, g.end_ea), 3)
        })

    for k in results:
        results[k].sort(key=lambda x: int(x["fn"], 16))
    
    summary = {k: len(v) for k, v in results.items()}
    open(OUT, "w").write(json.dumps({"summary": summary, **results}, indent=1))
    
except Exception:
    open(OUT, "w").write(json.dumps({"error": traceback.format_exc()}))

idc.qexit(0)
