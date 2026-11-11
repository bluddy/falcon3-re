"""S2 VGRAPH (finding 176/177): add game/VGRAPH as an IDA segment at 0x85AE0
and register all 122 traced call targets as functions.

VGRAPH is a 12,005-byte runtime-loaded graphics driver (game\VGRAPH).
At runtime it is MCB-allocated at CS = 0x77A3 (link_seg 0x75AE).
IDA address: link_seg * 16 + 0x10000 = 0x75AE0 + 0x10000 = 0x85AE0.

Steps:
  1. Create segment VGRAPH at 0x85AE0, selector 0x85AE, 16-bit code.
  2. Write the raw file bytes.
  3. Mark range for code analysis and decode from each known entry point.
  4. Register the 40 entry-table slots as functions named vgraph_slot_N.
  5. Register all 122 traced call targets (from boundary_report.json).
  6. Add entry-table comment.
  7. Save the database.

Usage:
  idat -A -S"tools/add_vgraph.py" analysis/ida_falconcd/FALCONCD.EXE.i64
"""
import json
import struct
import traceback
from pathlib import Path

import ida_segment
import ida_bytes
import ida_funcs
import ida_ua
import idaapi
import ida_loader
import idautils
import idc

ROOT      = r"C:\Users\ybarnoy\projects\falcon3"
ROOT_PATH = Path(ROOT)
VGRAPH_PATH    = ROOT + r"\game\VGRAPH"
LOG_PATH       = ROOT + r"\analysis\ida_falconcd\add_vgraph.log"
IDB_PATH       = ROOT + r"\analysis\ida_falconcd\FALCONCD.EXE.i64"
BOUNDARY_PATH  = ROOT + r"\analysis\traces\boundary_report.json"

VGRAPH_EA    = 0x85AE0          # IDA linear start
VGRAPH_SEL   = 0x85AE           # selector = IDA_linear >> 4
VGRAPH_SIZE  = 12005            # file size in bytes
ENTRY_WORDS  = 40               # 40-word entry table at file offset 0

log = []


def main():
    data = open(VGRAPH_PATH, "rb").read()
    assert len(data) == VGRAPH_SIZE, "unexpected VGRAPH size %d" % len(data)
    log.append("read %d bytes from %s" % (len(data), VGRAPH_PATH))

    # -- 1: check / create segment --
    if ida_segment.getseg(VGRAPH_EA) is not None:
        log.append("segment already exists at 0x%X" % VGRAPH_EA)
    else:
        ok = ida_segment.add_segm(
            VGRAPH_SEL, VGRAPH_EA, VGRAPH_EA + VGRAPH_SIZE,
            "VGRAPH", "CODE", 0)
        log.append("add_segm result: %s" % ok)

    # -- 2: force 16-bit (finding 52: new segs default to 32-bit) --
    seg = ida_segment.getseg(VGRAPH_EA)
    if seg is not None and seg.bitness != 0:
        seg.bitness = 0
        ida_segment.update_segm(seg)
        log.append("bitness forced to 0 (16-bit)")

    # -- 3: write bytes --
    ida_bytes.put_bytes(VGRAPH_EA, data)
    log.append("bytes written (0x%X..0x%X)" % (VGRAPH_EA, VGRAPH_EA + len(data)))

    # -- 4: decode from each entry table IP (no auto_wait to avoid draining main queue) --
    idc.auto_mark_range(VGRAPH_EA, VGRAPH_EA + VGRAPH_SIZE, idc.AU_CODE)
    for slot in range(ENTRY_WORDS):
        file_off = slot * 2
        (ip,) = struct.unpack_from("<H", data, file_off)
        if ip != 0:
            idc.create_insn(VGRAPH_EA + ip)
    log.append("code decode started for %d entry points" % ENTRY_WORDS)

    # -- 5: register 40 entry-table functions --
    for slot in range(ENTRY_WORDS):
        file_off = slot * 2
        (ip,) = struct.unpack_from("<H", data, file_off)
        if ip == 0:
            continue
        ea = VGRAPH_EA + ip
        f = ida_funcs.get_func(ea)
        if f is None or f.start_ea != ea:
            ida_funcs.add_func(ea)
        name = "vgraph_slot_%d" % slot
        cur = idc.get_func_name(ea)
        if cur and cur.startswith("sub_"):
            idc.set_name(ea, name, idc.SN_NOWARN)

    log.append("registered 40 entry-table slots")

    # -- 6: register all 122 traced VGRAPH call targets from boundary_report --
    trace_added = 0
    try:
        boundary = json.loads(Path(BOUNDARY_PATH).read_text())
        vg_ips = sorted(
            [r for r in boundary.get("other", [])
             if isinstance(r, dict) and r.get("cs") == 30627],
            key=lambda x: -x.get("calls", 0))
        for r in vg_ips:
            ip = r["ip"]
            ea = VGRAPH_EA + ip
            # decode if not already a code head
            fl = ida_bytes.get_flags(ea)
            if not (ida_bytes.is_code(fl) and ida_bytes.get_item_head(ea) == ea):
                ida_ua.create_insn(ea)
            # add_func if not already registered
            f = ida_funcs.get_func(ea)
            if f is None or f.start_ea != ea:
                ida_funcs.add_func(ea)
                trace_added += 1
        log.append("registered %d additional traced call-target functions" % trace_added)
    except Exception:
        log.append("traced IP error: " + traceback.format_exc())

    # -- 7: comment the entry table --
    idc.set_cmt(VGRAPH_EA,
        "VGRAPH 40-word entry table (file offset 0); "
        "runtime CS=0x77A3; IDA 0x85AE0..0x889C5; "
        "paras=751 (12005 bytes); link_seg=0x75AE; "
        "1.0M far calls traced (9.4%% of all); 122 distinct IPs",
        0)

    # -- 8: count resulting functions --
    fn_count = sum(1 for _ in idautils.Functions(VGRAPH_EA, VGRAPH_EA + VGRAPH_SIZE))
    log.append("functions in VGRAPH segment: %d" % fn_count)

    # -- save --
    ida_loader.save_database(IDB_PATH, 0)
    log.append("database saved: %s" % IDB_PATH)


try:
    main()
except Exception:
    log.append("ERROR:\n" + traceback.format_exc())
    try:
        ida_loader.save_database(IDB_PATH, 0)
        log.append("database saved after error")
    except Exception:
        log.append("save after error also failed")

open(LOG_PATH, "w").write("\n".join(log))
idaapi.qexit(0)
