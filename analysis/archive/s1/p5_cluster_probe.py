"""
p5_cluster_probe.py  —  analyse the R30 menu handler cluster 0x6E696..0x6E8B7
to understand the split pieces, their names, the switch structure, and what
a merge would look like.

Run: idat -A -S"analysis/s1/p5_cluster_probe.py" analysis/ida_falconcd/FALCONCD.EXE.i64
"""
import idc, ida_funcs, ida_bytes, ida_segment, idautils, idaapi
import json, traceback
from pathlib import Path

LOG = Path("analysis/s1/p5_cluster_probe.log")
OUT = Path("analysis/s1/p5_cluster_probe.json")

CLUSTER_LO = 0x6E696
CLUSTER_HI = 0x6E8B7   # exclusive

results = {}
log = []

try:
    # 1. List all functions in the range
    fns = []
    for ea in idautils.Functions(CLUSTER_LO, CLUSTER_HI):
        f = ida_funcs.get_func(ea)
        if f is None: continue
        name = idc.get_func_name(ea)
        has_user_name = ida_bytes.has_user_name(ida_bytes.get_flags(ea))
        # get callers (xrefs to function start)
        callers = []
        for xr in idautils.XrefsTo(ea, 0):
            if xr.iscode:
                callers.append(hex(xr.frm))
        fns.append({
            "ea": hex(ea), "end": hex(f.end_ea), "size": f.end_ea - ea,
            "name": name, "user_name": has_user_name,
            "callers": callers[:5], "n_callers": len(callers)
        })
        log.append("  0x%X..0x%X (%dB) %s%s callers=%d" % (
            ea, f.end_ea, f.end_ea-ea, name,
            " [USER]" if has_user_name else "", len(callers)))
    
    log.insert(0, "Functions in 0x%X..0x%X: %d" % (CLUSTER_LO, CLUSTER_HI, len(fns)))
    
    # 2. Check orphan runs in range
    orphans = []
    ea = CLUSTER_LO
    while ea < CLUSTER_HI:
        f = ida_funcs.get_func(ea)
        if f is None:
            # Check if it's a code head
            fl = ida_bytes.get_flags(ea)
            is_code = ida_bytes.is_code(fl)
            if is_code and ida_bytes.get_item_head(ea) == ea:
                orphans.append(hex(ea))
            ea += max(ida_bytes.get_item_size(ea), 1)
        else:
            ea = f.end_ea
    if orphans:
        log.append("Orphan code heads in range: %s" % orphans)
    
    # 3. Check if there's one entry that calls the others (the switch dispatcher)
    log.append("")
    log.append("Checking for switch dispatcher pattern:")
    for fn in fns:
        ea = int(fn['ea'], 16)
        # Count calls TO functions in the cluster from outside
        outside_callers = []
        for xr in idautils.XrefsTo(ea, 0):
            if not xr.iscode: continue
            xf = ida_funcs.get_func(xr.frm)
            if xf and not (CLUSTER_LO <= xf.start_ea < CLUSTER_HI):
                outside_callers.append(hex(xr.frm))
        if outside_callers:
            log.append("  0x%X (%s): %d outside callers: %s" % (
                ea, fn['name'], len(outside_callers), outside_callers[:3]))
    
    # 4. Check the range just before cluster (0x69209 switch table?)
    log.append("")
    log.append("Context before cluster (0x6E5xx area):")
    for ea in idautils.Functions(0x6E5A0, CLUSTER_LO):
        f = ida_funcs.get_func(ea)
        if f:
            log.append("  0x%X..0x%X (%dB) %s" % (
                ea, f.end_ea, f.end_ea-ea, idc.get_func_name(ea)))
    
    results = {"functions": fns, "orphans": orphans, "range": [hex(CLUSTER_LO), hex(CLUSTER_HI)]}
    OUT.write_text(json.dumps(results, indent=1))
    LOG.write_text("\n".join(log))

except Exception:
    LOG.write_text(traceback.format_exc())

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
