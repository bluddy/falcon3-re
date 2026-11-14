"""
p8_secondary_probe.py  —  enumerate all 24 fallthrough_secondary_entry targets.
Run: idat -A -S"analysis/s1/p8_secondary_probe.py" analysis/s1/probe_survey.i64
"""
import json, collections
import idaapi, idautils, idc, ida_funcs, ida_bytes, ida_segment, ida_ua, ida_idp
from pathlib import Path

OUT = Path("analysis/s1/p8_secondary.json")
LOG = Path("analysis/s1/p8_secondary.log")

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

results = []
log = []

for t, frm in sorted(tg.items()):
    g = ida_funcs.get_func(t)
    head = ida_bytes.get_item_head(t) == t
    prev = idc.prev_head(t, g.start_ea)
    pm = idc.print_insn_mnem(prev) if prev != idaapi.BADADDR else ""
    pfx = pm in ("retn", "retf", "iret", "jmp", "jmpf")
    fall = any(x == prev for x in idautils.CodeRefsTo(t, 1))
    ins = idc.print_insn_mnem(t)
    if head and not pfx and fall:
        # Check if prologue
        if ins in ("push", "enter", "mov"):
            k = "fallthrough_entry_proloque"
        else:
            k = "fallthrough_secondary"
        if k == "fallthrough_secondary":
            seg = ida_segment.get_segm_name(ida_segment.getseg(t))
            results.append({
                "ea": hex(t), "owner": idc.get_func_name(g.start_ea),
                "owner_ea": hex(g.start_ea), "owner_end": hex(g.end_ea),
                "mnem": ins, "sites": len(frm),
                "seg": seg, "callers": [hex(x) for x in frm[:5]]
            })
            log.append("0x%X (%s, owner=0x%X) mnem=%r sites=%d seg=%s" % (
                t, idc.get_func_name(g.start_ea), g.start_ea, ins, len(frm), seg))

log.insert(0, "Total secondary entries: %d" % len(results))
OUT.write_text(json.dumps(results, indent=1))
LOG.write_text("\n".join(log))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
