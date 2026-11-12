"""farobj_callers_probe.py — dump every caller of farptr_table_get (0x2703F).

For each caller:
  - full disassembly (up to 80 lines)
  - offset accesses into ES:DI (the object) — pattern: mov ax, es:[di+N] etc.
  - calls made after getting the pointer
  - static callers of this caller (one level up)
"""
import idc, ida_funcs, ida_bytes, idautils, idaapi, ida_segment
import traceback, json, re
from pathlib import Path

LOG  = Path("analysis/s4/farobj_callers.log")
OUT  = Path("analysis/s4/farobj_callers.json")

FARPTR_TABLE_GET_EA = 0x2703F  # farptr_table_get

log = []
results = {}

def seg_name(ea):
    s = ida_segment.getseg(ea)
    return ida_segment.get_segm_name(s) if s else "?"

def disasm_fn(fn):
    lines = []
    a = fn.start_ea
    while a < fn.end_ea:
        lines.append("  %05X  %s" % (a, idc.generate_disasm_line(a, 0)))
        a += ida_bytes.get_item_size(a)
        if len(lines) >= 80:
            lines.append("  ... truncated at 80 lines")
            break
    return lines

def callers_of(ea, limit=8):
    result = []
    for xr in idautils.XrefsTo(ea, 0):
        if not xr.iscode: continue
        m = idc.print_insn_mnem(xr.frm)
        fn = ida_funcs.get_func(xr.frm)
        fn_name = idc.get_func_name(fn.start_ea) if fn else "?"
        result.append((hex(xr.frm), fn_name, m))
        if len(result) >= limit: break
    return result

def extract_offset_accesses(fn):
    """Find patterns like ES:[DI+N] or word ptr ES:[DI+N] in disasm of fn."""
    offsets = set()
    a = fn.start_ea
    while a < fn.end_ea:
        disasm = idc.generate_disasm_line(a, 0)
        # Look for es:[di+N] or es:[di-N] patterns
        m = re.findall(r'es:\[di[+\-](0x[0-9a-fA-F]+|[0-9]+)\w*\]', disasm)
        for x in m:
            try:
                offsets.add(int(x, 16) if x.startswith('0x') else int(x))
            except ValueError:
                pass
        a += ida_bytes.get_item_size(a)
    return sorted(offsets)

def extract_calls_after(fn):
    """Find call targets within the function (not farptr_table_get itself)."""
    calls = []
    seen = set()
    a = fn.start_ea
    while a < fn.end_ea:
        m = idc.print_insn_mnem(a)
        if m.lower().startswith('call'):
            for xr in idautils.CodeRefsFrom(a, 0):
                if xr == FARPTR_TABLE_GET_EA: continue
                tgt_fn = ida_funcs.get_func(xr)
                if tgt_fn:
                    nm = idc.get_func_name(tgt_fn.start_ea)
                    if nm not in seen:
                        seen.add(nm)
                        calls.append(nm)
        a += ida_bytes.get_item_size(a)
    return calls

try:
    # Collect all static callers of farptr_table_get
    caller_eas = set()
    for xr in idautils.XrefsTo(FARPTR_TABLE_GET_EA, 0):
        if not xr.iscode: continue
        fn = ida_funcs.get_func(xr.frm)
        if fn:
            caller_eas.add(fn.start_ea)

    log.append("farptr_table_get (0x%X) has %d static callers" % (FARPTR_TABLE_GET_EA, len(caller_eas)))
    log.append("")

    for ea in sorted(caller_eas):
        fn = ida_funcs.get_func(ea)
        if fn is None: continue
        name = idc.get_func_name(ea)
        size = fn.end_ea - fn.start_ea
        seg  = seg_name(ea)
        dis  = disasm_fn(fn)
        offsets = extract_offset_accesses(fn)
        calls   = extract_calls_after(fn)
        my_callers = callers_of(ea, limit=5)
        
        entry = {
            "ea": hex(ea), "name": name, "size": size, "seg": seg,
            "disasm": dis,
            "di_offsets": offsets,
            "calls_after": calls,
            "my_callers": my_callers,
        }
        results[hex(ea)] = entry
        
        log.append("=== 0x%X  %s  %dB  %s ===" % (ea, name, size, seg))
        for d in dis:
            log.append(d)
        log.append("  ES:[DI+?] offsets: %s" % offsets)
        log.append("  Calls: %s" % calls)
        log.append("  My callers: %s" % [c[1] for c in my_callers])
        log.append("")

    OUT.write_text(json.dumps(results, indent=1))
    LOG.write_text("\n".join(log))

except Exception:
    LOG.write_text(traceback.format_exc())

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
