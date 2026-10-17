"""Read-only: what instruction heads exist inside specific thunk slots?

Explains why 20 slots inside sub_2BFCD and the span-20 fn-start never emit a
ref from slot+3 (finding 55's "27/303").

Output: analysis/ida_falconcd/heads56.log
Usage: cmd /c "tools\\run_idat.bat tools\\heads56.py"
"""
import traceback

import ida_bytes
import ida_funcs
import idaapi
import idautils
import idc

LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\heads56.log"
log = []
try:
    probe = [0x2BD9D,   # slot #000  - emits (8B fn)
             0x2BE83,   # slot #023  - fn START of the 20B merged fn, silent
             0x2BE8D,   # slot #024  - inside the 20B merged fn, silent
             0x2BFCD,   # slot #056  - fn START of the 210B merged fn, emits
             0x2BFD7,   # slot #057  - inside the 210B merged fn, silent
             0x2C095]   # slot #076  - last one inside sub_2BFCD
    for s in probe:
        f = ida_funcs.get_func(s)
        log.append("slot 0x%X  bytes=%s" % (s, (ida_bytes.get_bytes(s, 10) or b"").hex()))
        log.append("   containing fn: %s" % (
            ("%s 0x%X..0x%X (%dB)" % (idc.get_func_name(f.start_ea), f.start_ea,
                                      f.end_ea, f.end_ea - f.start_ea)) if f else "NONE"))
        # is slot+3 an instruction head?
        p3 = s + 3
        is_head = ida_bytes.is_head(p3)
        log.append("   slot+3=0x%X  is_head=%s  mnem=%r  nrefs=%d"
                   % (p3, is_head, idc.print_insn_mnem(p3) or "",
                      len(list(idautils.CodeRefsFrom(p3, 0))) if is_head else -1))
        # list every defined head in [s, s+10)
        heads = [h for h in idautils.Heads(s, s + 10)]
        log.append("   heads in [slot,slot+10): %s"
                   % ["0x%X:%s" % (h, idc.print_insn_mnem(h) or "unk") for h in heads])
        # what is the first head at/after s+3?
        h2 = ida_bytes.next_head(s, s + 12)
        log.append("   first head after slot: 0x%X mnem=%r" % (h2, idc.print_insn_mnem(h2) or ""))
        log.append("")
except Exception:
    log.append(traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
