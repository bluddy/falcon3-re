"""Split R05_1E10 / R29_1E10s into their RTLink sub-segments (finding 120).

Both records are linked out of many object segments, each with its own frame
paragraph (the distinct `seg` words of the record's fixup table, finding 56).
As one IDA segment they decode every near CALL/JMP/Jcc relative to the record
base instead of the runtime CS, so ~4,300 R05 and ~275 R29 branch targets
(and their crefs) point at the wrong bytes.  This script gives each object
segment its own IDA segment whose base paragraph IS that frame:

  base_i  = record ida_ea + (seg_i - w0) * 16        (frame paragraph)
  start_i = max(base_i, end of block i-1's last fixup word), pushed past any
            live function it would cut (an object segment may start at a
            non-zero offset inside its frame)
  extra   : a block reaching >= 64 KiB past its base gets a tail cut at
            base + 0x10000 (only data lives there)

Bytes, items, functions and names are untouched; only segment boundaries and
the xrefs of instructions in re-based segments change (each code head there
is re-created so its crefs/drefs are recomputed against the new CS).

Manifest-first: DRYRUN=1 writes registry/segsplit_expected.json and exits
without saving.  A real run recomputes the plan, refuses to proceed unless it
equals the committed manifest, applies it, and saves.  Idempotent: if every
segment already matches the manifest the run is a no-op (re-decoding twice is
not -- IDA's sreg emulation is order dependent).  Any failure discards the
in-memory changes (DBFL_KILL) so the IDB on disk is untouched.

Usage: idat -A -S"tools\\split_overlay_segments.py" <idb>      (DRYRUN=1 env for plan)
"""
import collections
import json
import os
import struct
import traceback
from pathlib import Path

import ida_auto
import ida_bytes
import ida_funcs
import ida_loader
import ida_segment
import ida_segregs
import ida_ua
import ida_xref
import idaapi
import idautils

ROOT = Path(__file__).resolve().parent.parent
EXE = (ROOT / "game/FALCONCD.EXE").read_bytes()
IDA = ROOT / "analysis/ida_falconcd"
MANIFEST = ROOT / "registry/segsplit_expected.json"
LOG = IDA / "split_overlay_segments.log"
DRYRUN = os.environ.get("DRYRUN") == "1"

DIR = 0x1E24F            # RTLink record directory (finding 56)
CLUSTER_B0 = 0x100000
SPECIAL = {0x1D0D, 0x1D31}
RECORDS = (5, 29)        # R05_1E10, R29_1E10s

log = []


def table_pos(r, located):
    # same rule as tools/validate_fixup_semantics.py
    if 50 <= r["idx"] <= 69:
        return CLUSTER_B0 + (r["w2"] << 4)
    e = located.get(r["idx"])
    if r["fixups"] and r["w2"] >= 0x1000:
        ov = set(range(r["w0"], r["w0"] + max(1, r["span"]))) | SPECIAL
        bp = r["w2"] << 4
        ok = sum(1 for k in range(r["fixups"])
                 if struct.unpack_from("<H", EXE, bp + k * 4 + 2)[0] in ov) / r["fixups"]
        if ok >= 0.8:
            return bp
    if e and e["fixup_frac"] >= 0.8:
        return e["fixup_pos"]
    if r["w2"] >= 0x1000:
        return r["w2"] << 4
    return None


def containing_func(ea):
    f = ida_funcs.get_func(ea)
    return f if f and f.start_ea < ea < f.end_ea else None


def make_plan():
    placements = {p["idx"]: p for p in json.loads((IDA / "overlay_placement.json").read_text())}
    located = {e["idx"]: e for e in json.loads((IDA / "record_fixup_located.json").read_text())}
    plan, problems = [], []
    for idx in RECORDS:
        w0, _, w2, _, w4, w5 = struct.unpack_from("<6H", EXE, DIR + idx * 18)
        r = dict(idx=idx, w0=w0, w2=w2, span=w4, fixups=w5)
        p = placements[idx]
        lo, hi = p["ida_ea"], p["ida_ea"] + p["ida_len"]
        pos = table_pos(r, located)
        arena = set(range(w0, w0 + max(1, w4)))
        blocks = {}
        for k in range(w5):
            off, seg = struct.unpack_from("<HH", EXE, pos + k * 4)
            if seg not in arena or seg in SPECIAL:
                continue
            ea = lo + (seg - w0) * 16 + off
            if ea >= hi:
                continue
            b = blocks.setdefault(seg, [ea, ea])
            b[0], b[1] = min(b[0], ea), max(b[1], ea + 2)
        segs = sorted(blocks)
        if segs[0] != w0:
            problems.append("idx%d first anchor %04X != w0 %04X" % (idx, segs[0], w0))
        rows = []
        reach = lo
        for i, seg in enumerate(segs):
            base = lo + (seg - w0) * 16
            start = lo if i == 0 else max(base, reach)
            f = containing_func(start)
            while f:
                start = f.end_ea
                f = containing_func(start)
            if start > blocks[seg][0]:
                problems.append("idx%d %04X start 0x%X past first fixup 0x%X"
                                % (idx, seg, start, blocks[seg][0]))
            rows.append({"seg": seg, "base": base, "start": start})
            reach = blocks[seg][1]
        # tails: a frame can only address 64 KiB
        out = []
        for i, row in enumerate(rows):
            end = rows[i + 1]["start"] if i + 1 < len(rows) else hi
            out.append(row)
            while end - row["base"] > 0x10000:
                t = row["base"] + 0x10000
                if containing_func(t):
                    problems.append("idx%d tail cut 0x%X inside a function" % (idx, t))
                row = {"seg": row["seg"] + 0x1000, "base": t, "start": t, "tail": True}
                out.append(row)
        for i, row in enumerate(out):
            row["end"] = out[i + 1]["start"] if i + 1 < len(out) else hi
            sfx = "s" if p["seg_name"].endswith("s") else ""
            row["name"] = p["seg_name"] if i == 0 else "R%02d_%04X%s" % (idx, row["seg"], sfx)
            row["para"] = row["base"] >> 4
            row["record"] = idx
            if row["start"] >= row["end"]:
                problems.append("%s empty" % row["name"])
            for fs in idautils.Functions(row["start"], row["end"]):
                fe = ida_funcs.get_func(fs).end_ea
                if fe > row["end"] or fe - row["base"] > 0x10000:
                    problems.append("%s fn 0x%X..0x%X does not fit" % (row["name"], fs, fe))
        plan += out
    return plan, problems


SREGS = ("es", "ds", "ss", "cs")


def sreg_at_heads(start, end):
    regs = [idaapi.str2reg(r) for r in SREGS]
    return {h: tuple(ida_segregs.get_sreg(h, r) for r in regs)
            for h in idautils.Heads(start, end) if ida_bytes.is_code(ida_bytes.get_flags(h))}


def sreg_ranges(start, end):
    """Segment-register change points in [start, end) -- re-applied after the
    split because new segments start with default (unknown) sreg values."""
    out = []
    for name in SREGS[:3]:
        reg = idaapi.str2reg(name)
        rr = ida_segregs.sreg_range_t()
        for n in range(ida_segregs.get_sreg_ranges_qty(reg)):
            ida_segregs.getn_sreg_range(rr, reg, n)
            if start <= rr.start_ea < end:
                out.append((rr.start_ea, reg, rr.val, rr.tag))
    return out


def snapshot_funcs():
    return [(fs, ida_funcs.get_func(fs).end_ea, idaapi.get_name(fs)) for fs in idautils.Functions()]


def redecode(start, end):
    """Re-create every code head so its xrefs are recomputed against the new CS.
    User xrefs (finding 119 repairs) are kept; analysis-generated ones are
    dropped first so stale targets do not survive."""
    n = dropped = 0
    for h in idautils.Heads(start, end):
        if not ida_bytes.is_code(ida_bytes.get_flags(h)):
            continue
        sz = ida_bytes.get_item_size(h)
        probe = ida_ua.insn_t()
        if ida_ua.decode_insn(probe, h) != sz:
            # a truncated head (fixup word / overlapping item); re-creating it
            # would swallow the following items
            log.append("  skip 0x%X: item size %d, decodes as %d" % (h, sz, probe.size))
            continue
        for x in list(idautils.XrefsFrom(h, ida_xref.XREF_FAR)):
            if x.user:
                continue
            if x.iscode:
                if x.type == ida_xref.fl_F and x.to == h + sz:
                    continue
                ida_xref.del_cref(h, x.to, 0)
            else:
                ida_xref.del_dref(h, x.to)
            dropped += 1
        if ida_ua.create_insn(h) != sz:
            raise RuntimeError("create_insn changed item size at 0x%X" % h)
        n += 1
    return n, dropped


def already_split(plan):
    for row in plan:
        s = ida_segment.getseg(row["start"])
        if not (s and s.start_ea == row["start"] and s.end_ea == row["end"]
                and ida_segment.get_segm_base(s) == row["base"]):
            return False
    return True


def apply(plan):
    before = snapshot_funcs()
    lo, hi = min(r["start"] for r in plan), max(r["end"] for r in plan)
    regs_before = sreg_at_heads(lo, hi)
    ranges = sreg_ranges(lo, hi)
    log.append("sreg change points saved: %d" % len(ranges))
    sregs = [idaapi.str2reg(r) for r in SREGS[:3]]
    entry = {r["start"]: [ida_segregs.get_sreg(r["start"], g) for g in sregs] for r in plan}
    done = 0
    for row in sorted(plan, key=lambda r: -r["start"]):
        s = ida_segment.getseg(row["start"])
        if (s and s.start_ea == row["start"] and s.end_ea == row["end"]
                and ida_segment.get_segm_base(s) == row["base"]):
            continue
        parent = ida_segment.getseg(row["start"])
        if parent is None or parent.start_ea > row["start"] or parent.end_ea < row["end"]:
            raise RuntimeError("no parent segment covering %s" % row["name"])
        if parent.start_ea == row["start"]:
            # first piece: keep the segment, only trim its end
            if not ida_segment.set_segm_end(parent.start_ea, row["end"], ida_segment.SEGMOD_KEEP):
                raise RuntimeError("set_segm_end failed for %s" % row["name"])
            continue
        tmpl = ida_segment.segment_t()
        tmpl.start_ea, tmpl.end_ea = row["start"], row["end"]
        tmpl.sel = ida_segment.setup_selector(row["para"])
        tmpl.bitness = 0
        tmpl.align, tmpl.comb, tmpl.perm, tmpl.type = parent.align, parent.comb, parent.perm, parent.type
        if not ida_segment.set_segm_end(parent.start_ea, row["start"], ida_segment.SEGMOD_KEEP):
            raise RuntimeError("set_segm_end failed before %s" % row["name"])
        if not ida_segment.add_segm_ex(tmpl, row["name"], "CODE", ida_segment.ADDSEG_NOTRUNC):
            raise RuntimeError("add_segm_ex failed for %s" % row["name"])
        s = ida_segment.getseg(row["start"])
        if s.bitness != 0:
            s.bitness = 0
        # carry the DS/ES/SS value live at the cut into the new segment
        for g, v in zip(sregs, entry[row["start"]]):
            ida_segregs.set_default_sreg_value(s, g, v)
        done += 1
    log.append("segments created: %d" % done)
    bad = [(ea, reg, val, tag) for ea, reg, val, tag in ranges
           if not ida_segregs.split_sreg_range(ea, reg, val, tag)]
    log.append("sreg replay failures: %d" % len(bad))
    tot = drop = 0
    for row in plan:
        n, d = redecode(row["start"], row["end"])
        tot += n
        drop += d
    # Re-decoding re-runs IDA's sreg emulation, so values may legitimately
    # change: CS-relative ones follow the new CS, `mov es,ax` after an
    # immediate is newly tracked, `mov ds,cs:[x]` now reads x at the right CS.
    # Only known -> unknown is a loss.
    kinds, lost = collections.Counter(), []
    for h, v in sreg_at_heads(lo, hi).items():
        b = regs_before.get(h, v)
        for nb, na, rn in zip(b[:3], v[:3], SREGS):
            if nb == na:
                continue
            if nb == b[3] and na == v[3]:
                kinds[rn + " follows CS"] += 1
            elif na == idaapi.BADSEL:
                kinds[rn + " known->unknown"] += 1
                lost.append(h)
            elif nb == idaapi.BADSEL:
                kinds[rn + " unknown->known"] += 1
            else:
                kinds[rn + " known->other"] += 1
    log.append("sreg changes after re-decode: %s" % sorted(kinds.items()))
    if len(lost) > len(regs_before) // 1000:
        log.append("  lost e.g. %s" % ["0x%X" % h for h in lost[:10]])
        raise RuntimeError("sreg tracking lost at %d heads" % len(lost))
    log.append("re-decoded %d heads, dropped %d analysis xrefs" % (tot, drop))
    after = snapshot_funcs()
    if before != after:
        # IDA treats a leading `nop` that lost its (analysis) xref as padding
        # and nudges the function start by one; put recorded spans back.
        fixed = 0
        for fs, fe, nm in sorted(set(before) - set(after)):
            f = ida_funcs.get_func(fs) or ida_funcs.get_func(fs + 1)
            if f and f.end_ea == fe and abs(f.start_ea - fs) <= 1 and ida_funcs.set_func_start(f.start_ea, fs) == ida_funcs.MOVE_FUNC_OK:
                idaapi.set_name(fs, nm, idaapi.SN_NOWARN | idaapi.SN_NOCHECK)
                fixed += 1
        log.append("restored %d nudged function starts" % fixed)
        after = snapshot_funcs()
    if before != after:
        gone = sorted(set(before) - set(after))
        new = sorted(set(after) - set(before))
        log.append("function table: %d gone %s" % (len(gone), ["0x%X..0x%X %s" % g for g in gone[:20]]))
        log.append("function table: %d new %s" % (len(new), ["0x%X..0x%X %s" % g for g in new[:20]]))
        raise RuntimeError("function table changed")
    log.append("function table unchanged (%d)" % len(after))
    for row in plan:
        s = ida_segment.getseg(row["start"])
        if not (s and s.start_ea == row["start"] and s.end_ea == row["end"]
                and ida_segment.get_segm_base(s) == row["base"] and s.bitness == 0):
            raise RuntimeError("post-check failed for %s" % row["name"])
    log.append("auto queue empty: %s" % ida_auto.auto_is_ok())


def main():
    plan, problems = make_plan()
    for p in problems:
        log.append("PROBLEM " + p)
    for r in plan:
        log.append("  %-12s base=0x%06X start=0x%06X end=0x%06X para=%05X%s"
                   % (r["name"], r["base"], r["start"], r["end"], r["para"],
                      " tail" if r.get("tail") else ""))
    if problems:
        log.append("ABORT: plan has problems; nothing changed")
        return
    if DRYRUN:
        MANIFEST.write_text(json.dumps({"finding": 120, "segments": plan}, indent=1))
        log.append("DRYRUN: wrote %s (%d segments)" % (MANIFEST, len(plan)))
        return
    want = json.loads(MANIFEST.read_text())["segments"]
    if want != plan:
        log.append("ABORT: live plan != committed manifest; nothing changed")
        return
    if already_split(plan):
        # re-decoding is not idempotent (IDA's sreg emulation is order
        # dependent), so a second pass must not touch anything
        log.append("already split: nothing to do")
        return
    apply(plan)
    ida_loader.save_database(idaapi.get_path(idaapi.PATH_TYPE_IDB), 0)
    log.append("database saved")


try:
    main()
except Exception:
    log.append("ERROR (not saved):\n" + traceback.format_exc())
open(LOG if not os.environ.get("SPLITLOG") else os.environ["SPLITLOG"], "w").write("\n".join(log))
idaapi.qexit(0)
