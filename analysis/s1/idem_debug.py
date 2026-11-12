"""idem_debug.py — check trim_state and rb_state for finding 178 entries."""
import hashlib, json
import ida_bytes, ida_funcs, ida_name, idaapi, idc, idautils
from pathlib import Path

LOG = Path("C:/Users/ybarnoy/projects/falcon3/analysis/s1/idem_debug.log")
log = []

ROOT = Path(__file__).resolve().parent.parent.parent  # tools/../..
MANIFEST = ROOT / "registry/orphan_funcs_expected.json"

def sha(ea, end):
    return hashlib.sha256(ida_bytes.get_bytes(ea, end - ea)).hexdigest()

def uname(ea):
    return idaapi.get_name(ea) if ida_bytes.has_user_name(ida_bytes.get_flags(ea)) else None

def chunks(ea):
    f = ida_funcs.get_func(ea)
    if not f or f.start_ea != ea: return None
    out, it = [], ida_funcs.func_tail_iterator_t(f)
    ok = it.main()
    while ok:
        out.append([it.chunk().start_ea, it.chunk().end_ea])
        ok = it.next()
    return sorted(out)

try:
    doc = json.loads(MANIFEST.read_text(encoding='utf-8'))
    
    # Find trim entry for 0x683C5
    for tr in doc.get("trim_funcs", []):
        if tr["ea"] == 0x683C5:
            ea, oe, ne, wh, ch = tr["ea"], tr["old_end"], tr["end"], tr["words_hi"], tr["clear_hi"]
            f = ida_funcs.get_func(ea)
            log.append("=== TRIM 0x683C5 ===")
            log.append("  f exists: %s" % bool(f))
            if f:
                log.append("  f.start_ea=0x%X, f.end_ea=0x%X (expected ne=0x%X, oe=0x%X)" % (f.start_ea, f.end_ea, ne, oe))
                log.append("  uname(0x%X)=%r  x[name]=%r" % (ea, uname(ea), tr.get("name")))
                log.append("  sha check: computed=%s" % sha(ea, ch)[:16])
                log.append("  sha stored:         %s" % tr.get("sha256","")[:16])
                log.append("  sha match: %s" % (sha(ea, ch) == tr.get("sha256","")))
                log.append("  chunks: %s" % chunks(ea))
            break
    
    # Find rebase entry for 0x6940B
    for rb in doc.get("rebase_funcs", []):
        if rb["ea"] == 0x6940B:
            old, new, end = rb["old_ea"], rb["ea"], rb["end"]
            f_new = ida_funcs.get_func(new)
            f_old = ida_funcs.get_func(old)
            log.append("=== REBASE 0x6940B ===")
            log.append("  f_new: %s" % (("start=0x%X end=0x%X" % (f_new.start_ea, f_new.end_ea)) if f_new else "NONE"))
            log.append("  f_old (should be same fn): %s" % (("start=0x%X" % f_old.start_ea) if f_old else "NONE"))
            if f_new:
                log.append("  uname(0x%X)=%r  x[name]=%r" % (new, uname(new), rb.get("name")))
                log.append("  chunks: %s" % chunks(new))
                log.append("  sha(new,end) match: %s" % (sha(new, end) == rb.get("sha256","")))
            # Check "fresh" condition
            f_old_check = ida_funcs.get_func(old)
            if f_old_check:
                log.append("  fresh: start_ea match: %s (%s)" % (f_old_check.start_ea == old, hex(f_old_check.start_ea)))
            break
    
except Exception as e:
    import traceback
    log.append(traceback.format_exc())

idaapi.set_database_flag(idaapi.DBFL_KILL)
LOG.write_text("\n".join(log))
idc.qexit(0)
