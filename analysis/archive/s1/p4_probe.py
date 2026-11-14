"""
p4_probe.py  —  enumerate all 'other' and 'merged_fn' mid-body targets,
annotate which are fix_decode byproducts, and list shared tails vs real cases.
Run: idat -A -S"analysis/s1/p4_probe.py" analysis/s1/probe_p4.i64
"""
import json, collections, traceback
import idaapi, idautils, idc, ida_funcs, ida_bytes, ida_segment, ida_ua, ida_idp
from pathlib import Path

OUT  = Path("analysis/s1/p4_probe.json")
LOG  = Path("analysis/s1/p4_probe.log")

# Load fix_decode manifest entries so we can flag byproducts
MANIFEST = Path("registry/orphan_funcs_expected.json")
fd_heads = set()   # the original misdecoded heads (the byte BEFORE the real target)
fd_targets = set() # the fixed code heads: fd_head+1
if MANIFEST.exists():
    m = json.loads(MANIFEST.read_text())
    for e in m.get("fix_decode_funcs", []):
        h = e["head"]
        fd_heads.add(h)
        fd_targets.add(h + 1)   # target is head+1

results = {"other": [], "merged_fn": [], "fallthrough_entry_proloque": [], "fallthrough_secondary": []}
log = []

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

    for t, frm in sorted(tg.items()):
        g = ida_funcs.get_func(t)
        head = ida_bytes.get_item_head(t) == t
        prev = idc.prev_head(t, g.start_ea)
        pm = idc.print_insn_mnem(prev) if prev != idaapi.BADADDR else ""
        pfx = pm in ("retn", "retf", "iret", "jmp", "jmpf")
        fall = any(x == prev for x in idautils.CodeRefsTo(t, 1))
        ins = idc.print_insn_mnem(t)
        is_fd = t in fd_targets

        # Classify (same logic as survey_mid.py)
        if not head:
            k = "not_head"
        elif pfx and not fall:
            k = "after_ret_or_jmp(merged_fn)"
        elif ins in ("push", "enter", "mov") and fall:
            k = "fallthrough_entry_proloque"
        elif fall:
            k = "fallthrough_secondary"
        else:
            k = "other"

        # Check if any internal (non-call) xref from owner jumps to t
        internal_jmp_xrefs = []
        for xr in idautils.XrefsTo(t, 0):
            if not xr.iscode: continue
            xf = ida_funcs.get_func(xr.frm)
            if xf and xf.start_ea == g.start_ea:
                m2 = idc.print_insn_mnem(xr.frm)
                if m2 not in ("call", "callf"):
                    internal_jmp_xrefs.append({"from": hex(xr.frm), "mnem": m2})

        entry = {
            "ea": hex(t), "owner": idc.get_func_name(g.start_ea),
            "owner_ea": hex(g.start_ea), "owner_end": hex(g.end_ea),
            "cls": k, "is_fd_byproduct": is_fd,
            "prev_mnem": pm, "mnem": ins, "sites": len(frm),
            "internal_jmps": internal_jmp_xrefs,
            "callers": [hex(x) for x in frm[:5]]
        }

        if k == "after_ret_or_jmp(merged_fn)":
            results["merged_fn"].append(entry)
        elif k == "other":
            results["other"].append(entry)
        elif k == "fallthrough_entry_proloque":
            results["fallthrough_entry_proloque"].append(entry)
        elif k == "fallthrough_secondary":
            results["fallthrough_secondary"].append(entry)

    log.append("other: %d targets (%d fd_byproducts, %d real)" % (
        len(results["other"]),
        sum(1 for e in results["other"] if e["is_fd_byproduct"]),
        sum(1 for e in results["other"] if not e["is_fd_byproduct"])))
    log.append("merged_fn: %d targets" % len(results["merged_fn"]))
    log.append("fallthrough_entry_proloque: %d targets" % len(results["fallthrough_entry_proloque"]))
    log.append("")
    log.append("=== OTHER (real, not fd byproducts) ===")
    for e in results["other"]:
        if not e["is_fd_byproduct"]:
            log.append("  ea=0x%s owner=%s prev=%s mnem=%s sites=%d internal_jmps=%s" % (
                e["ea"][2:].upper(), e["owner"], e["prev_mnem"], e["mnem"], e["sites"], e["internal_jmps"]))
    log.append("")
    log.append("=== OTHER (fd byproducts) ===")
    for e in results["other"]:
        if e["is_fd_byproduct"]:
            log.append("  ea=0x%s owner=%s prev=%s mnem=%s sites=%d" % (
                e["ea"][2:].upper(), e["owner"], e["prev_mnem"], e["mnem"], e["sites"]))
    log.append("")
    log.append("=== MERGED_FN (all) ===")
    for e in results["merged_fn"]:
        log.append("  ea=0x%s owner=%s prev=%s mnem=%s sites=%d internal_jmps=%s" % (
            e["ea"][2:].upper(), e["owner"], e["prev_mnem"], e["mnem"], e["sites"], e["internal_jmps"]))
    log.append("")
    log.append("=== FALLTHROUGH_ENTRY_PROLOQUE (remaining) ===")
    for e in results["fallthrough_entry_proloque"]:
        log.append("  ea=0x%s owner=%s prev=%s mnem=%s sites=%d internal_jmps=%s" % (
            e["ea"][2:].upper(), e["owner"], e["prev_mnem"], e["mnem"], e["sites"], e["internal_jmps"]))

    OUT.write_text(json.dumps(results, indent=1))
    LOG.write_text("\n".join(log))
except Exception:
    LOG.write_text(traceback.format_exc())

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
