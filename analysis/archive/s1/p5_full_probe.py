"""p5_full_probe.py — full analysis of the R30 menu handler cluster."""
import idc, ida_funcs, ida_bytes, idautils, idaapi, traceback, json
from pathlib import Path

LOG = Path("analysis/s1/p5_full_probe.log")
OUT = Path("analysis/s1/p5_full_probe.json")

# From status.md: "67F58..683C5 stretch + 683C5..6940E giant fn"
# Also: undecoded bodies at 0x68A18, 0x68AE2, etc.
PROBE_LO = 0x67F00
PROBE_HI = 0x69500

log = []
results = {"functions": [], "gaps": []}

try:
    # List all functions in the range
    ea = PROBE_LO
    while ea < PROBE_HI:
        f = ida_funcs.get_func(ea)
        if f and f.start_ea >= PROBE_LO:
            name = idc.get_func_name(f.start_ea)
            user = ida_bytes.has_user_name(ida_bytes.get_flags(f.start_ea))
            callers_in = []
            callers_out = []
            for xr in idautils.XrefsTo(f.start_ea, 0):
                if not xr.iscode: continue
                xf = ida_funcs.get_func(xr.frm)
                if xf and PROBE_LO <= xf.start_ea < PROBE_HI:
                    callers_in.append(hex(xr.frm))
                else:
                    callers_out.append(hex(xr.frm))
            fn = {
                "ea": hex(f.start_ea), "end": hex(f.end_ea),
                "size": f.end_ea - f.start_ea,
                "name": name, "user_name": user,
                "callers_outside": callers_out[:3],
                "n_callers_outside": len(callers_out),
                "callers_inside": callers_in[:3],
                "n_callers_inside": len(callers_in)
            }
            results["functions"].append(fn)
            log.append("  0x%X..0x%X (%4dB) %-40s n_ext=%d n_int=%d%s" % (
                f.start_ea, f.end_ea, f.end_ea-f.start_ea, name,
                len(callers_out), len(callers_in),
                " [USER]" if user else ""))
            ea = f.end_ea
        else:
            # Gap
            if not ida_funcs.get_func(ea):
                fl = ida_bytes.get_flags(ea)
                is_code = ida_bytes.is_code(fl)
                if is_code and ida_bytes.get_item_head(ea) == ea:
                    results["gaps"].append({"ea": hex(ea), "is_code": True,
                                            "mnem": idc.print_insn_mnem(ea)})
            ea += 1

    log.insert(0, "Functions in 0x%X..0x%X: %d" % (PROBE_LO, PROBE_HI, len(results["functions"])))
    log.append("")
    log.append("Gaps (orphan code): %d" % len(results["gaps"]))
    for g in results["gaps"][:10]:
        log.append("  %s mnem=%r" % (g["ea"], g["mnem"]))

    OUT.write_text(json.dumps(results, indent=1))
    LOG.write_text("\n".join(log))

except Exception:
    LOG.write_text(traceback.format_exc())

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
