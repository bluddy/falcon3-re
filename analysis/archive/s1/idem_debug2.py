"""idem_debug2.py — simulate state check logic exactly as apply_orphan_funcs.py does it."""
import hashlib, json
import ida_bytes, ida_funcs, ida_name, idaapi, idc, idautils
from pathlib import Path

LOG = Path("C:/Users/ybarnoy/projects/falcon3/analysis/s1/idem_debug2.log")

ROOT = Path("C:/Users/ybarnoy/projects/falcon3")
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

def trim_state(x):
    ea, oe, ne, wh, ch = x["ea"], x["old_end"], x["end"], x["words_hi"], x["clear_hi"]
    f = ida_funcs.get_func(ea)
    if not f or f.start_ea != ea:
        return "mismatch:no_func"
    if uname(ea) != x["name"]:
        return "mismatch:name %r vs %r" % (uname(ea), x["name"])
    if sha(ea, ch) != x["sha256"]:
        return "mismatch:sha"
    if f.end_ea == oe and chunks(ea) == [[ea, oe]]:
        return "fresh"
    if f.end_ea == ne and chunks(ea) == [[ea, ne]]:
        for a in range(ne, wh, 2):
            if not (ida_bytes.is_data(ida_bytes.get_flags(a)) and ida_bytes.get_item_size(a) == 2):
                return "mismatch:words"
        return "applied"
    return "mismatch:end %X vs ne=%X oe=%X" % (f.end_ea, ne, oe)

def rb_state(x):
    old, new, end = x["old_ea"], x["ea"], x["end"]
    f = ida_funcs.get_func(new)
    if f and f.start_ea == new and f.end_ea == end and chunks(new) == [[new, end]] and uname(new) == x["name"]:
        return "applied"
    f2 = ida_funcs.get_func(old)
    if (f2 and f2.start_ea == old and f2.end_ea == end and chunks(old) == [[old, end]] and uname(old) == x["name"]
            and sha(new, end) == x["sha256"] and not any(ida_funcs.get_func(a) for a in range(new, old))):
        return "fresh"
    # Detail why not applied
    details = []
    if not f: details.append("f_new=NONE")
    elif f.start_ea != new: details.append("start=%X!=%X" % (f.start_ea, new))
    elif f.end_ea != end: details.append("end=%X!=%X" % (f.end_ea, end))
    elif chunks(new) != [[new, end]]: details.append("chunks=%s" % chunks(new))
    elif uname(new) != x["name"]: details.append("uname=%r!=%r" % (uname(new), x["name"]))
    return "mismatch: " + ", ".join(details)

log = []
try:
    doc = json.loads(MANIFEST.read_text(encoding='utf-8'))
    
    for tr in doc.get("trim_funcs", []):
        if tr["ea"] == 0x683C5:
            log.append("trim_state(0x683C5): %s" % trim_state(tr))
    
    for rb in doc.get("rebase_funcs", []):
        if rb["ea"] == 0x6940B:
            log.append("rb_state(0x6940B): %s" % rb_state(rb))

except Exception as e:
    import traceback
    log.append(traceback.format_exc())

idaapi.set_database_flag(idaapi.DBFL_KILL)
LOG.write_text("\n".join(log))
idc.qexit(0)
