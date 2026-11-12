"""p5_connections.py — understand the jump/call structure between the P5 fragments."""
import idc, ida_funcs, ida_bytes, idautils, ida_ua, idaapi, traceback, json
from pathlib import Path

LOG = Path("analysis/s1/p5_connections.log")

CLUSTER_LO = 0x67F58
CLUSTER_HI = 0x6940E  # exclusive — ui_loadout_menu_enter ends here

log = []

try:
    # For each fragment, show how it's reached and where it goes
    fns = list(idautils.Functions(CLUSTER_LO, CLUSTER_HI))
    log.append("Fragments in 0x%X..0x%X: %d" % (CLUSTER_LO, CLUSTER_HI, len(fns)))
    log.append("")

    for ea in fns:
        f = ida_funcs.get_func(ea)
        if f is None: continue
        name = idc.get_func_name(ea)
        
        # How is this entry reached? (xrefs TO start)
        entry_xrefs = []
        for xr in idautils.XrefsTo(ea, 0):
            if not xr.iscode: continue
            m = idc.print_insn_mnem(xr.frm)
            xf = ida_funcs.get_func(xr.frm)
            owner = idc.get_func_name(xf.start_ea) if xf else "?"
            entry_xrefs.append("%s @0x%X (%s)" % (m, xr.frm, owner))
        
        # First few instructions
        head = ea
        instrs = []
        for _ in range(3):
            m = idc.print_insn_mnem(head)
            o1 = idc.print_operand(head, 0)
            instrs.append("%s %s" % (m, o1) if o1 else m)
            head += ida_bytes.get_item_size(head)
        
        # Last instruction (before end)
        prev = idc.prev_head(f.end_ea, ea)
        last = idc.print_insn_mnem(prev) if prev != idaapi.BADADDR else "?"
        last_op = idc.print_operand(prev, 0) if prev != idaapi.BADADDR else ""
        
        log.append("0x%X..0x%X (%dB) %s" % (ea, f.end_ea, f.end_ea - ea, name))
        log.append("  reached by: %s" % (', '.join(entry_xrefs) if entry_xrefs else "(none/jump-only)"))
        log.append("  starts: %s" % ' | '.join(instrs[:3]))
        log.append("  ends with: %s %s" % (last, last_op))
        log.append("")
    
    # Also check the switch table at 0x69209
    log.append("=== Switch table at 0x69209 ===")
    ea = 0x69209
    for i in range(15):
        w = ida_bytes.get_word(ea + i*2)
        log.append("  [%2d] = 0x%04X  (target=0x%X)" % (i, w, 0x669F0 + w))
    
    LOG.write_text("\n".join(log))

except Exception:
    LOG.write_text(traceback.format_exc())

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
