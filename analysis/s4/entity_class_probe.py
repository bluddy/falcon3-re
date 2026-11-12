"""entity_class_probe.py — resolve entity class codes + FarObj struct gaps.

Fixes vs v1:
  - proper indentation (all body inside try:)
  - use idc.get_segm_name(ea) not ida_segment.get_segm_name(ea)
  - DS_BASE = 0x43AE0 (link_para 0x33AE * 16 + 0x10000)
  - absolute-safe paths via idc.GetIdbPath()
"""
import idc, ida_funcs, ida_bytes, idautils, idaapi, ida_segment
import traceback, json
from pathlib import Path

# Use IDB location as base for output paths
_idb = Path(idc.get_idb_path()).parent
LOG = _idb / "entity_class.log"
OUT = _idb / "entity_class.json"

log = []
results = {}

try:
    # -----------------------------------------------------------------------
    # 1. Read entity type tables
    # -----------------------------------------------------------------------
    # farobj_entity_attr_setup (0x44352):
    #   shl bx,1
    #   mov cx, [bx+1662h]   <- table A: entity attr word
    #   mov bx, [bx+16F4h]   <- table B: entity class byte (low)
    #   mov [si+14h], bx      <- FarObj.entity_class = low byte of table B entry
    #
    # DS_BASE for R05_33AE = link_para * 16 + 0x10000
    #                       = 0x33AE * 16 + 0x10000 = 0x43AE0
    DS_BASE = 0x43AE0
    table_b_base = DS_BASE + 0x16F4   # 0x451D4
    table_a_base = DS_BASE + 0x1662   # 0x45142

    log.append("DS_BASE       = 0x%X" % DS_BASE)
    log.append("Table B base  = 0x%X (DS+0x16F4)" % table_b_base)
    log.append("Table A base  = 0x%X (DS+0x1662)" % table_a_base)

    # Read 40 entries from each table (class index = BX/2)
    table_b = []
    table_a = []
    for i in range(40):
        wb = ida_bytes.get_word(table_b_base + i * 2)
        wa = ida_bytes.get_word(table_a_base + i * 2)
        table_b.append({"i": i, "word": "0x%04X" % wb, "lo": "0x%02X" % (wb & 0xFF)})
        table_a.append({"i": i, "word": "0x%04X" % wa})
        log.append("  B[%2d]=0x%04X (class=0x%02X)  A[%2d]=0x%04X" % (i, wb, wb & 0xFF, i, wa))

    results["table_b"] = table_b
    results["table_a"] = table_a

    # -----------------------------------------------------------------------
    # 2. Find entity class comparisons (cmp al, 0x12/14/33/38)
    # -----------------------------------------------------------------------
    log.append("\n=== Entity class comparisons (cmp al, 0x12/14/33/38) ===")
    TARGET_CLS = {0x12, 0x14, 0x33, 0x38}
    hits = {}

    for s_ea in idautils.Segments():
        nm = idc.get_segm_name(s_ea)
        s = ida_segment.getseg(s_ea)
        if s is None:
            continue
        if s.sclass != idc.SEG_CODE:
            continue
        a = s_ea
        while a < s.end_ea - 1:
            b0 = ida_bytes.get_byte(a)
            b1 = ida_bytes.get_byte(a + 1)
            if b0 == 0x3C and b1 in TARGET_CLS:
                fn = ida_funcs.get_func(a)
                fn_name = idc.get_func_name(fn.start_ea) if fn else "?"
                hits[hex(a)] = {
                    "fn": fn_name,
                    "imm": "0x%02X" % b1,
                    "dis": idc.generate_disasm_line(a, 0),
                }
                log.append("  cmp al,0x%02X @ 0x%X  in %s" % (b1, a, fn_name))
            a += 1

    results["class_comparisons"] = hits
    log.append("  total hits: %d" % len(hits))

    # -----------------------------------------------------------------------
    # 3. FarObj struct fields 0x2E..0x73
    #    Pattern: 26 <mov-op> <ModRM=01..101b (DI+disp8)> <disp>
    #    ES: prefix = 0x26
    #    ModRM & 0xC7 == 0x45  =>  mod=01, rm=DI(5)
    # -----------------------------------------------------------------------
    log.append("\n=== FarObj struct fields 0x2E..0x73 (ES:[DI+N]) ===")
    field_accesses = {}

    for s_ea in idautils.Segments():
        s = ida_segment.getseg(s_ea)
        if s is None:
            continue
        if s.sclass != idc.SEG_CODE:
            continue
        a = s_ea
        end = s.end_ea - 4
        while a < end:
            b0 = ida_bytes.get_byte(a)
            if b0 != 0x26:
                a += 1
                continue
            b1 = ida_bytes.get_byte(a + 1)
            b2 = ida_bytes.get_byte(a + 2)
            b3 = ida_bytes.get_byte(a + 3)
            # mov/test with ModRM mod=01 rm=DI(5)
            if b1 in (0x8B, 0x8A, 0x89, 0x88, 0x85):
                if (b2 & 0xC7) == 0x45:
                    disp = b3
                    if 0x2E <= disp <= 0x73:
                        fn = ida_funcs.get_func(a)
                        fn_name = idc.get_func_name(fn.start_ea) if fn else "?"
                        d = idc.generate_disasm_line(a, 0)
                        key = "0x%02X" % disp
                        if key not in field_accesses:
                            field_accesses[key] = []
                        field_accesses[key].append({"fn": fn_name, "ea": hex(a), "dis": d[:70]})
            a += 1

    # Summarize
    for off in sorted(field_accesses.keys(), key=lambda x: int(x, 16)):
        accesses = field_accesses[off]
        fns = list({a["fn"] for a in accesses[:5]})
        log.append("  [DI+%s]: %d accesses, funcs: %s" % (off, len(accesses), ", ".join(fns[:3])))

    results["field_accesses"] = field_accesses

    # -----------------------------------------------------------------------
    # 4. Write outputs
    # -----------------------------------------------------------------------
    OUT.write_text(json.dumps(results, indent=1), encoding='utf-8')
    LOG.write_text("\n".join(log), encoding='utf-8')
    log.append("\nProbe complete. Outputs written.")

except Exception:
    LOG.write_text(traceback.format_exc(), encoding='utf-8')

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
