"""Fix overlay cross-references in FALCONCD.EXE.i64 (Finding 119).

Repairs three classes of overlay jump/call cross-references in IDA without
modifying any instruction bytes or function spans:
  1. RTLink Thunk Jumps (0x2BD9D..0x2C973, slots 0..301):
     Replaces automatic flat-linear crefs with XREF_USER fl_JF crefs to the
     true target overlay entry_ea specified by dw wid at thunk_ea + 8.
  2. Intra-Overlay Far Calls/Jumps (9A/EA) in Synthetic Overlays (rows 3..68):
     Replaces automatic crefs (which point to real-arena overlays such as
     R30_569F or R05_1E10) with XREF_USER fl_CF/fl_JF crefs to the true
     intra-overlay target `lo + (unreloc_seg - w0) * 16 + tgt_off`.
  3. Cluster-B CS-Relative Switch Jump Tables (2E FF A7 disp16 in R50..R68):
     Formats switch jump tables outside functions as dw words and adds
     XREF_USER fl_JN case crefs and dr_O table drefs.

Usage: cmd /c "tools\\run_idat.bat tools\\fix_overlay_jumps_ida.py"
"""
import json
import struct
import traceback
from collections import Counter
from pathlib import Path

import ida_bytes
import ida_funcs
import ida_loader
import ida_segment
import ida_xref
import idaapi
import idautils

ROOT = Path(r"C:\Users\yotam\projects\falcon3")
EXE = (ROOT / "game/FALCONCD.EXE").read_bytes()
IDA = ROOT / "analysis/ida_falconcd"
IDB = str(IDA / "FALCONCD.EXE.i64")
LOG = IDA / "fix_overlay_jumps.log"

log = []
ok_all = False

try:
    pl = {p["idx"]: p for p in json.loads((IDA / "overlay_placement.json").read_text())}
    fixups = {int(k): v for k, v in json.loads((IDA / "fixups_to_apply.json").read_text()).items()}

    # Snapshot all function spans before touching any xrefs
    fn_spans_before = [(s, ida_funcs.get_func(s).end_ea) for s in idautils.Functions()]

    # 1. Fix RTLink Thunk Jumps (0x2BD9D..0x2C973, slots 0..301)
    THUNK_FILE = 0x1E99D
    THUNK_IDA = 0x2BD9D
    thunk_fixed = 0
    thunk_del = 0
    for i in range(302):
        o = THUNK_FILE + i * 10
        if EXE[o] != 0xE8 or EXE[o + 3] != 0xEA:
            continue
        loff, lseg, wid = struct.unpack_from("<HHH", EXE, o + 4)
        target_linear = ((0x1000 + lseg) << 4) + loff
        p = pl.get(wid)
        if not p or not p.get("ida_ea") or not p.get("ida_len"):
            continue
        rel = target_linear - p["real_ea"]
        want_ea = p["ida_ea"] + rel
        if ida_segment.getseg(want_ea) is None:
            continue
        jmp_ea = THUNK_IDA + i * 10 + 3
        existing = list(idautils.CodeRefsFrom(jmp_ea, 0))
        for dst in existing:
            if dst != want_ea:
                ida_xref.del_cref(jmp_ea, dst, 0)
                thunk_del += 1
        if want_ea not in list(idautils.CodeRefsFrom(jmp_ea, 0)):
            ida_xref.add_cref(jmp_ea, want_ea, ida_xref.fl_JF | ida_xref.XREF_USER)
            thunk_fixed += 1

    log.append(f"1. RTLink thunk jumps: deleted {thunk_del} wrong crefs, added {thunk_fixed} true overlay crefs")

    # 2. Fix Intra-Overlay Far Calls/Jumps in Synthetic Overlays (rows 3..68)
    intra_fixed = 0
    intra_del = 0
    for idx, plist in sorted(fixups.items()):
        p = pl.get(idx)
        if not p or not p.get("ida_ea") or not p["seg_name"].endswith("s"):
            continue
        lo = p["ida_ea"]
        hi = lo + p["ida_len"]
        w0 = p["w0"]
        span = p["span_bytes"] >> 4
        for rel, word_before in plist:
            unreloc_seg = word_before & 0xFFFF
            if not (w0 <= unreloc_seg < w0 + span):
                continue
            if rel < 3 or rel + 2 > p["ida_len"]:
                continue
            src_ea = lo + rel - 3
            if ida_bytes.get_item_head(src_ea) != src_ea:
                continue
            if not ida_bytes.is_code(ida_bytes.get_flags(src_ea)):
                continue
            if ida_bytes.get_item_size(src_ea) != 5:
                continue
            op = ida_bytes.get_byte(src_ea)
            if op not in (0x9A, 0xEA):
                continue
            tgt_off = ida_bytes.get_word(src_ea + 1)
            want_ea = lo + (unreloc_seg - w0) * 16 + tgt_off
            if not (lo <= want_ea < hi):
                continue
            existing = list(idautils.CodeRefsFrom(src_ea, 0))
            for dst in existing:
                if dst != want_ea:
                    ida_xref.del_cref(src_ea, dst, 0)
                    intra_del += 1
            fl = (ida_xref.fl_CF if op == 0x9A else ida_xref.fl_JF) | ida_xref.XREF_USER
            if want_ea not in list(idautils.CodeRefsFrom(src_ea, 0)):
                ida_xref.add_cref(src_ea, want_ea, fl)
                intra_fixed += 1

    log.append(f"2. Intra-overlay far calls/jumps: deleted {intra_del} wrong crefs, added {intra_fixed} true intra-overlay crefs")

    # 3. Fix Switch Jump Tables in Cluster B (R50..R68, including R53 sub-blocks)
    sw_fixed = 0
    sw_del = 0
    sw_crefs_added = 0
    for idx in range(50, 69):
        p = pl[idx]
        lo = p["ida_ea"]
        ln = p["ida_len"]
        hi = lo + ln
        w0 = p["w0"]
        span = ln >> 4
        tbl = EXE[p["fixup_pos"]:p["data_file"]]

        fix_sites = {}
        for i in range(0, len(tbl), 4):
            off, seg = struct.unpack_from("<HH", tbl, i)
            if w0 <= seg < w0 + span:
                site_off = (seg - w0) * 16 + off
                fix_sites[site_off] = seg

        subblock_segs = sorted(set(fix_sites.values()) | {w0})
        subblock_bases = [lo + (s - w0) * 16 for s in subblock_segs if w0 <= s < w0 + span]

        def get_subblock_base(ea_val):
            return max([b for b in subblock_bases if b <= ea_val], default=lo)

        for f_start in idautils.Functions(lo, hi):
            f_obj = ida_funcs.get_func(f_start)
            if not f_obj:
                continue
            f_end = f_obj.end_ea
            sb_base = get_subblock_base(f_start)

            # Collect all switch instructions (2E FF A7 disp16) in this function
            raw_switches = []
            for h in idautils.Heads(f_start, f_end):
                if ida_bytes.is_code(ida_bytes.get_flags(h)) and ida_bytes.get_item_size(h) == 5:
                    if (ida_bytes.get_byte(h) == 0x2E
                            and ida_bytes.get_byte(h + 1) == 0xFF
                            and ida_bytes.get_byte(h + 2) == 0xA7):
                        disp = ida_bytes.get_word(h + 3)
                        jpt_ea = sb_base + disp
                        if lo <= jpt_ea < hi:
                            raw_switches.append((h, jpt_ea))

            if not raw_switches:
                continue

            jpt_starts = sorted({j for _, j in raw_switches})
            for sw_ea, jpt_ea in raw_switches:
                nxt_jpt = next((j for j in jpt_starts if j > jpt_ea), hi)
                cases = []
                pos = jpt_ea
                while pos + 2 <= min(nxt_jpt, hi):
                    w = ida_bytes.get_word(pos)
                    tgt = sb_base + w
                    if f_start <= tgt < f_end and ida_bytes.is_code(ida_bytes.get_flags(tgt)):
                        cases.append(tgt)
                        pos += 2
                    else:
                        break
                ncases = len(cases)
                if not ncases:
                    continue
                if not ida_funcs.get_func(jpt_ea):
                    ida_bytes.del_items(jpt_ea, ida_bytes.DELIT_SIMPLE, ncases * 2)
                    for c_i in range(ncases):
                        ida_bytes.create_word(jpt_ea + c_i * 2, 2)
                want_set = set(cases)
                existing = list(idautils.CodeRefsFrom(sw_ea, 0))
                for dst in existing:
                    if dst not in want_set:
                        ida_xref.del_cref(sw_ea, dst, 0)
                        sw_del += 1
                cur_refs = set(idautils.CodeRefsFrom(sw_ea, 0))
                for c_tgt in sorted(want_set):
                    if c_tgt not in cur_refs:
                        ida_xref.add_cref(sw_ea, c_tgt, ida_xref.fl_JN | ida_xref.XREF_USER)
                        sw_crefs_added += 1
                ida_xref.add_dref(sw_ea, jpt_ea, ida_xref.dr_O | ida_xref.XREF_USER)
                sw_fixed += 1

    log.append(f"3. Cluster-B switch tables: configured {sw_fixed} switches, deleted {sw_del} bogus crefs, added {sw_crefs_added} case crefs")

    # Guard: verify zero function spans changed
    fn_spans_after = [(s, ida_funcs.get_func(s).end_ea) for s in idautils.Functions()]
    if fn_spans_before != fn_spans_after:
        log.append(f"GUARD FAILED: function spans changed ({len(fn_spans_before)} -> {len(fn_spans_after)})")
        ok_all = False
    else:
        log.append(f"GUARD PASSED: all {len(fn_spans_after)} function spans identical")
        ok_all = True

except Exception:
    log.append("EXCEPTION:\n" + traceback.format_exc())
    ok_all = False

if ok_all:
    ida_loader.save_database(IDB, 0)
    log.append("SAVED")
else:
    log.append("NOT SAVED")

LOG.write_text("\n".join(log), encoding="utf-8")
idaapi.qexit(0)
