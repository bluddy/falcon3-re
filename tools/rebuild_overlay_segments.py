"""Rebuild overlay segments in the FALCONCD IDB from raw record bytes.

Reads analysis/ida_falconcd/overlay_placement.json (findings 17/18):
  - deletes all existing segments at >= 0x2CF60 (old wrong overlay layout, finding 16)
  - creates one segment per placed record:
      real      : arena base (0x1000+w0)<<4, clipped at next arena
      synthetic : 0x100000+ (transient records sharing an arena)
      skipped   : cluster-B (unplaced) and zero-span placeholders -> nothing
  - writes RAW record bytes (no fixup application yet - fixup decode still open)
  - runs autoanalysis and SAVES the database BEFORE the report (headless -A
    does not reliably auto-save; reporting must never block persistence)

NOTE: same-arena transient overlap is BY DESIGN (finding 18); only the first
placed record per arena holds the real address, others live at synthetic bases.
"""
import json
import traceback

import ida_segment
import ida_bytes
import idaapi
import ida_loader
import idautils

ROOT = r"C:\Users\yotam\projects\falcon3"
PLACEMENT = ROOT + r"\analysis\ida_falconcd\overlay_placement.json"
EXE = ROOT + r"\game\FALCONCD.EXE"
LOG = ROOT + r"\analysis\ida_falconcd\rebuild_overlay.log"
IDB_PATH = ROOT + r"\analysis\ida_falconcd\FALCONCD.EXE.i64"

placements = json.load(open(PLACEMENT))
exefile = open(EXE, "rb").read()
log = []


def main():
    # 1) delete old segments beyond the resident image
    to_del = []
    for i in range(ida_segment.get_segm_qty()):
        seg = ida_segment.getnseg(i)
        if seg.start_ea >= 0x2CF60 and seg.start_ea < 0x1000000:
            to_del.append((seg.start_ea, seg.end_ea))
    for start, end in reversed(to_del):
        ida_segment.del_segm(start, ida_segment.SEGMOD_KILL)
    log.append("deleted %d old overlay segments" % len(to_del))

    # 2) create new segments + write bytes
    written = 0
    skipped = 0
    total = 0
    for p in placements:
        if p["addr"] == "skip" or not p["ida_len"]:
            skipped += 1
            continue
        ea = p["ida_ea"]
        ln = p["ida_len"]
        if ida_segment.getseg(ea) is not None:
            log.append("  SKIP idx%d: segment already at 0x%X" % (p["idx"], ea))
            skipped += 1
            continue
        ok = ida_segment.add_segm(ea >> 4, ea, ea + ln, p["seg_name"], "CODE", 0)
        data = exefile[p["data_file"]:p["data_file"] + ln]
        if len(data) < ln:
            log.append("  WARN idx%d short read (%d < %d)" % (p["idx"], len(data), ln))
        ida_bytes.put_bytes(ea, data)
        ida_bytes.set_cmt(
            ea,
            "record idx=%d w0=%04X runtime=0x%X flags=0x%02X order=%s file=0x%X"
            % (p["idx"], p["w0"], p["real_ea"], p["flags"], p["order"], p["data_file"]),
            0,
        )
        if not ok:
            log.append("  WARN idx%d add_segm returned %s" % (p["idx"], ok))
        written += 1
        total += len(data)

    log.append("wrote %d segments (%d bytes), skipped %d" % (written, total, skipped))
    idaapi.auto_wait()
    log.append("autoanalysis done")

    # save FIRST - reporting must never block persistence
    path = IDB_PATH
    ida_loader.save_database(path, 0)
    log.append("database saved: %s" % path)

    count = 0
    for i in range(ida_segment.get_segm_qty()):
        seg = ida_segment.getnseg(i)
        if seg.start_ea >= 0x2CF60:
            funcs = list(idautils.Functions(seg.start_ea, seg.end_ea))
            count += len(funcs)
            log.append("  %-12s 0x%X-0x%X  funcs=%d" % (
                seg.name, seg.start_ea, seg.end_ea, len(funcs)))
    log.append("total overlay funcs: %d" % count)


try:
    main()
except Exception:
    log.append("ERROR:\n" + traceback.format_exc())
    try:
        path = IDB_PATH
        ida_loader.save_database(path, 0)
        log.append("database saved after error: %s" % path)
    except Exception:
        log.append("save after error also failed")

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)

