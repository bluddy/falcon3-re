"""p3_probe.py: enumerate all fallthrough_entry_proloque and fallthrough_secondary_entry targets.
Output: analysis/s1/p3_all.json
"""
import os; os.environ["DBFL_KILL"] = "1"
import json, collections, traceback
import idaapi, idautils, idc, ida_funcs, ida_bytes, ida_segment, ida_ua, ida_idp

OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\p3_all.json"

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

    prologue = []  # fallthrough_entry_proloque
    secondary = []  # fallthrough_secondary_entry
    
    for t, frm in tg.items():
        g = ida_funcs.get_func(t)
        if not ida_bytes.is_code(ida_bytes.get_flags(t)) or ida_bytes.get_item_head(t) != t:
            continue
        prev = idc.prev_head(t, g.start_ea)
        pm = idc.print_insn_mnem(prev) if prev != idaapi.BADADDR else ""
        pfx = pm in ("retn", "retf", "iret", "jmp", "jmpf")
        fall = any(x == prev for x in idautils.CodeRefsTo(t, 1))
        ins = idc.print_insn_mnem(t)
        
        if pfx and not fall:
            continue  # merged_fn, skip
        
        # fall-in entry (fall==True OR prev not a terminator)
        if not fall:
            continue  # 'other', skip
        
        seg = ida_segment.get_segm_name(ida_segment.getseg(t))
        entry = {
            "t": "%X" % t, "fn": "%X" % g.start_ea, "fn_end": "%X" % g.end_ea,
            "fn_name": idc.get_func_name(g.start_ea) or "", "seg": seg,
            "prev_mnem": pm, "ins": ins, "callers": len(frm),
            "disasm_prev": idc.generate_disasm_line(prev, 0) if prev != idaapi.BADADDR else "",
            "disasm_t": idc.generate_disasm_line(t, 0),
        }
        
        has_prologue = ins in ("push", "enter", "mov")
        (prologue if has_prologue else secondary).append(entry)
    
    prologue.sort(key=lambda x: int(x["fn"], 16))
    secondary.sort(key=lambda x: int(x["fn"], 16))
    
    open(OUT, "w").write(json.dumps({
        "prologue_count": len(prologue), "secondary_count": len(secondary),
        "prologue": prologue, "secondary": secondary
    }, indent=1))

except Exception:
    open(OUT, "w").write(json.dumps({"error": traceback.format_exc()}))

idc.qexit(0)
