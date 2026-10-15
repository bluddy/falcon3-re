"""Register IDA-missed functions found in boundary re-check (step 4, finding 37).

Finding 37: boundary_report.json's 87 UNKNOWN targets decompose as:
  67 = .RTLink thunk-table entries (10-byte stride, 0x2BD9D..0x2C973) -- not fns
  13 = data / dispatch-table labels (zero-fill, far-ptr tables `xx 9f 56`)
   4 = real code candidates, of which 0x1018F is airtight:
     0x1018F  433B far dispatcher, 132,401 far calls (2nd-hottest target),
              prologue 55 8b ec, ends cb exactly where sub_10340 begins.
     (0x10853 / 0x2E100 / 0x2E20A are mid-function tails or long fallthrough
      fragments -- NOT registered here; documented in findings log.)

Registration only, no renaming beyond default sub_XXXXX so naming ledger
stays authoritative.

Usage: cmd /c "tools\\run_idat.bat tools\\add_boundary_functions.py"
"""
import traceback

import ida_bytes
import ida_funcs
import ida_loader
import ida_name
import ida_ua
import idaapi

IDB = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64"
LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\addfunc_boundary.log"

# (ea, end_ea, name) -- finding 37 boundary re-check
# 0x1018F: 122B far dispatcher (11 je converge to off 110, retf at off 119),
#          132,401 far calls (2nd-hottest target). End is 0x10207, NOT
#          0x10340 -- that crosses seg000 (ends 0x10210) into seg001, and the
#          cb at 0x1033F belongs to a different fn. add_func with a
#          cross-segment range fails silently (finding 37).
NEW_FUNCS = [
    (0x1018F, 0x10207, "sub_1018F"),   # 122B far dispatcher, 132K calls
]

log = []
try:
    for ea, end_ea, name in NEW_FUNCS:
        # v2 pattern from apply_trace_functions.py: force chunk conversion
        # first (del_items + create_insn) or add_func refuses (finding 33).
        ida_bytes.del_items(ea, ida_bytes.DELIT_EXPAND, end_ea - ea)
        pos = ea
        while pos < end_ea:
            if not ida_ua.create_insn(pos):
                log.append("  create_insn failed at 0x%X" % pos)
                break
            pos = ida_bytes.next_head(pos, end_ea)
        ok = ida_funcs.add_func(ea, end_ea)
        ida_name.set_name(ea, name, ida_name.SN_CHECK)
        f = ida_funcs.get_func(ea)
        log.append("%s add_func(0x%X..0x%X)=%s -> %s"
                   % (name, ea, end_ea, ok,
                      (hex(f.start_ea) + "-" + hex(f.end_ea)) if f else "NONE"))
    idaapi.auto_wait()
    ida_loader.save_database(IDB, 0)
    log.append("saved")
except Exception:
    log.append(traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
