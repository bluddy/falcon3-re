import traceback
import ida_bytes, ida_ua, ida_segment, idaapi, idc
ROOT = r"C:\Users\yotam\projects\falcon3"
LOG = ROOT + r"\analysis\ida_falconcd\stop_probe.log"
CASES = [0x3B830, 0x3B83A, 0x54AF2, 0x54AF3, 0x4E520, 0x3B831, 0x2E2F0, 0x5A868]
log = []
try:
    for ea in CASES:
        seg = ida_segment.getseg(ea)
        raw = idc.get_bytes(ea, 6)
        ins = ida_ua.insn_t()
        n = ida_ua.decode_insn(ins, ea)
        ins2 = ida_ua.insn_t()
        n2 = ida_ua.decode_insn(ins2, ea)   # second attempt (state?)
        perm = seg.perm if seg else -1
        log.append("0x%-7X bytes=%s perm=%d exec=%s n=%d n2=%d mnem=%s flags_unknown=%s"
                   % (ea, raw.hex() if raw else "?", perm,
                      bool(seg and (seg.perm & 1)), n, n2,
                      (ins.get_canon_mnem() or "-") if n else "-",
                      bool(ida_bytes.is_unknown(ida_bytes.get_flags(ea)))))
    # does an IDA-created instruction at a zero run work?
    log.append("---- decode at 0x3B83A followed ----")
    for ea in (0x3B83A, 0x3B83C, 0x3B83E):
        ins = ida_ua.insn_t()
        n = ida_ua.decode_insn(ins, ea)
        log.append("0x%-7X n=%d %s" % (ea, n, (ins.get_canon_mnem() or "-") if n else "-"))
except Exception:
    log.append(traceback.format_exc())
open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)