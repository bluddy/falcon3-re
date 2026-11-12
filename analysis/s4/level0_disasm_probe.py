"""level0_disasm_probe.py — dump disassembly + context for top Level-0 functions.

For each target ea:
  - current name, size, segment
  - full disassembly (up to 60 lines)
  - all call/jump xrefs FROM (callees)
  - static callers (up to 8)
  - named data xrefs (global accesses)
"""
import idc, ida_funcs, ida_bytes, idautils, idaapi, ida_segment
import traceback, json
from pathlib import Path

LOG  = Path("analysis/s4/level0_disasm.log")
OUT  = Path("analysis/s4/level0_disasm.json")

# Top Level-0 functions by dynamic call count + a few selected ones
TARGET_EAS = [
    0x1018F,  # mouse_int33_dispatch - 337K dyn
    0x112A1,  # input_status_pack    - 318K dyn
    0x24E5D,  # bda_equipment_flag_get - 243K dyn
    0x22AFF,  # timer_tick_isr       - 229K dyn
    0x2703F,  # farptr_table_get     - 210K dyn, 78 callers
    0x2228F,  # active_farptr_restore - 206K dyn
    0x22285,  # active_farptr_set    - 203K dyn
    0x1122A,  # joystick_poll        - 95K dyn
    0x215B7,  # flag_byte_get        - 76K dyn
    0x21266,  # es_ptr_slots_init    - 54K dyn
    0x22C91,  # fixed_vec3_accumulate_a - 52K dyn
    0x1BCFA,  # irq_unmask_and_query - 48K dyn
    0x25F93,  # segment_clip_test    - 42K dyn
    0x24DB8,  # far_cb_with_args     - 41K dyn
    0x26099,  # (unnamed)            - 37K dyn
    0x1FCC9,  # flag_clear           - 36K dyn
    0x25EF4,  # dispatch_220ec_invoke - 36K dyn
    0x1FCBD,  # flag_set_lowbit      - 12B
    0x25F0D,  # dispatch_220ec_stub  - 35K dyn
    0x22C89,  # (unnamed)            - 35K dyn
    # Additional interesting ones
    0x263F0,  # 32K dyn, 17 callers
    0x25EBD,  # 28K dyn, 25 callers
    0x25EC9,  # 28K dyn, 25 callers
    0x22EE8,  # 25K dyn, 11 callers
    0x16F10,  # 20K dyn, 15 callers
    0x24CF7,  # 19K dyn, 11 callers
    0x263F6,  # 18K dyn, 8 callers
    0x128A1,  # 16K dyn, 6 callers -- state_farptr_get
]

log = []
results = {}

def seg_name(ea):
    s = ida_segment.getseg(ea)
    return ida_segment.get_segm_name(s) if s else "?"

def disasm_fn(ea, fn):
    lines = []
    a = fn.start_ea
    limit = 80
    count = 0
    while a < fn.end_ea and count < limit:
        disasm = idc.generate_disasm_line(a, 0)
        lines.append("  %05X  %s" % (a, disasm))
        a += ida_bytes.get_item_size(a)
        count += 1
    if a < fn.end_ea:
        lines.append("  ... (%d more bytes)" % (fn.end_ea - a))
    return lines

def callers_of(ea, limit=10):
    result = []
    for xr in idautils.XrefsTo(ea, 0):
        if not xr.iscode: continue
        m = idc.print_insn_mnem(xr.frm)
        if m.startswith("call") or m.startswith("j"):
            fn = ida_funcs.get_func(xr.frm)
            fn_name = idc.get_func_name(fn.start_ea) if fn else "?"
            result.append({"from": hex(xr.frm), "fn": fn_name, "mnem": m})
        if len(result) >= limit: break
    return result

def data_refs(ea, fn):
    """Named global data references (DS: or ES: memory accesses)."""
    refs = []
    seen = set()
    a = fn.start_ea
    while a < fn.end_ea:
        for xr in idautils.DataRefsFrom(a):
            nm = idc.get_name(xr)
            if nm and nm not in seen:
                seen.add(nm)
                refs.append({"ea": hex(xr), "name": nm})
        a += ida_bytes.get_item_size(a)
    return refs

try:
    for ea in TARGET_EAS:
        fn = ida_funcs.get_func(ea)
        if fn is None or fn.start_ea != ea:
            log.append("SKIP 0x%X: not a function start (fn=%s)" % (ea, hex(fn.start_ea) if fn else "none"))
            continue

        name = idc.get_func_name(ea)
        size = fn.end_ea - fn.start_ea
        seg  = seg_name(ea)
        flags_str = "far" if (fn.flags & ida_funcs.FUNC_FAR) else "near"

        disasm = disasm_fn(ea, fn)
        callers = callers_of(ea)
        drefs = data_refs(ea, fn)

        entry = {
            "ea": hex(ea), "name": name, "size": size, "seg": seg,
            "far": bool(fn.flags & ida_funcs.FUNC_FAR),
            "disasm": disasm,
            "callers": callers,
            "data_refs": drefs,
        }
        results[hex(ea)] = entry

        log.append("\n=== 0x%X  %s  %dB  %s  [%s] ===" % (ea, name, size, seg, flags_str))
        for d in disasm[:40]:
            log.append(d)
        if len(disasm) > 40:
            log.append("  ... (%d more lines)" % (len(disasm)-40))
        log.append("  Callers(%d): %s" % (len(callers), ", ".join(c["fn"] for c in callers[:5])))
        log.append("  Data refs: %s" % ", ".join(d["name"] for d in drefs[:8]))

    OUT.write_text(json.dumps(results, indent=1))
    LOG.write_text("\n".join(log))

except Exception:
    LOG.write_text(traceback.format_exc())

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
