import ida_bytes, ida_funcs, ida_ua, idaapi, idc, idautils, json, os
ROOT = r"C:\Users\yotam\projects\falcon3"
log = []
# sub_22C91: current span 0x22C91..0x22C9E (13B).  Does a clean chain reach a
# terminator BEFORE the next function?  Decode from entry, see where it lands.
for ea, label in [(0x22C91, "sub_22C91"), (0x22C62, "sub_22C62")]:
    fn = ida_funcs.get_func(ea)
    cur_end = fn.end_ea if fn else ea
    log.append("=== %s entry=0x%X current_end=0x%X ===" % (label, ea, cur_end))
    # walk forward decoding, note item heads and terminator
    cur = ea
    steps = []
    for _ in range(80):
        h = ida_bytes.get_item_head(cur)
        if h != cur:
            steps.append("0x%X: MID of item@0x%X" % (cur, h))
            cur = h + ida_bytes.get_item_size(h)
            continue
        insn = ida_ua.insn_t()
        k = ida_ua.decode_insn(insn, cur)
        if k <= 0:
            steps.append("0x%X: UNDECODABLE byte=0x%02X" % (cur, ida_bytes.get_byte(cur)))
            break
        mn = idc.print_insn_mnem(cur)
        marker = ""
        if cur >= cur_end:
            marker = "  <-- PAST current fn end"
        steps.append("0x%X: %s%s%s" % (cur, mn,
                     " " + idc.print_operand(cur,0) if idc.print_operand(cur,0) else "",
                     marker))
        if mn.lower() in ("retn","retf","ret","iret"):
            steps.append("   >>> TERMINATOR %s at 0x%X" % (mn.upper(), cur))
            break
        cur += k
    for s in steps:
        log.append("  " + s)
    # what fn is at the terminator?
    log.append("")
# also: is 0x22C9E (nullsub_19) a real fn or padding?
import json as _json
_cls = _json.load(open(os.path.join(ROOT, "analysis/ida_falconcd/classification.json"), encoding="utf-8"))
_ns = _cls.get("nullsub_19", {})
log.append("nullsub_19 ea=0x%X size=%s class=%s" % (0x22C9E, _ns.get("size"), _ns.get("class")))
with open(os.path.join(ROOT, "analysis/ida_falconcd/diag_data.log"), "w") as f:
    f.write("\n".join(log))
idaapi.qexit(0)