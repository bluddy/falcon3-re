"""
vgraph_check_ips.py  —  find which of the 122 observed VGRAPH IPs are
already functions and which still need to be registered.
Run: idat -A -S"analysis/s1/vgraph_check_ips.py" analysis/ida_falconcd/FALCONCD.EXE.i64
"""
import json, ida_funcs, idc, idaapi, traceback
from pathlib import Path

LOG = Path("analysis/s1/vgraph_check_ips.log")
OUT = Path("analysis/s1/vgraph_check_ips.json")

VGRAPH_EA = 0x85AE0

try:
    data = json.loads(Path("analysis/traces/boundary_report.json").read_text())
    other = data.get("other", [])
    vg = [r for r in other if isinstance(r, dict) and r.get("cs") == 30627]

    results = {"already_fn": [], "need_fn": [], "not_code_head": []}
    log = ["VGRAPH observed IPs: %d" % len(vg)]

    for r in sorted(vg, key=lambda x: -x.get("calls", 0)):
        ip = r["ip"]
        ea = VGRAPH_EA + ip
        calls = r.get("calls", 0)
        f = ida_funcs.get_func(ea)
        if f and f.start_ea == ea:
            results["already_fn"].append({"ea": hex(ea), "ip": ip, "calls": calls})
        elif ida_bytes.is_code(ida_bytes.get_flags(ea)) if hasattr(ida_bytes, 'get_flags') else False:
            results["need_fn"].append({"ea": hex(ea), "ip": ip, "calls": calls})
        else:
            # check if it's a code head
            import ida_bytes
            fl = ida_bytes.get_flags(ea)
            is_code = ida_bytes.is_code(fl)
            head = ida_bytes.get_item_head(ea)
            if is_code and head == ea:
                results["need_fn"].append({"ea": hex(ea), "ip": ip, "calls": calls,
                                           "mnem": idc.print_insn_mnem(ea)})
            else:
                results["not_code_head"].append({"ea": hex(ea), "ip": ip, "calls": calls,
                                                 "is_code": is_code, "head": hex(head)})

    log.append("already fn: %d" % len(results["already_fn"]))
    log.append("need fn: %d" % len(results["need_fn"]))
    log.append("not code head: %d" % len(results["not_code_head"]))
    log.append("")
    log.append("Need fn (top 20 by calls):")
    for r in sorted(results["need_fn"], key=lambda x: -x["calls"])[:20]:
        log.append("  ip=0x%04X ea=%s calls=%d mnem=%r" % (r["ip"], r["ea"], r["calls"], r.get("mnem","")))
    log.append("")
    log.append("Not code head (top 10):")
    for r in sorted(results["not_code_head"], key=lambda x: -x["calls"])[:10]:
        log.append("  ip=0x%04X ea=%s calls=%d is_code=%s head=%s" % (
            r["ip"], r["ea"], r["calls"], r["is_code"], r["head"]))

    OUT.write_text(json.dumps(results, indent=1))
    LOG.write_text("\n".join(log))
except Exception:
    LOG.write_text(traceback.format_exc())

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
