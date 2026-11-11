"""S3 VGRAPH xrefs (finding 177): add traced indirect-far call xrefs to VGRAPH
from the fileio trace data (harvctl3 + debug_test).

Reads all 'indirect_far' records with target CS = 0x77A3 from the trace files,
converts caller CS:IP -> IDA ea using the standard formula:
    link_seg = cs - IMAGE_PARA (0x1F5)
    ida_ea   = link_seg * 16 + 0x10000 + ip

Adds add_cref(caller_ida, target_ida, fl_CF | XREF_USER) for each unique pair.
Annotates each VGRAPH function with its traced call count.

Usage:
  idat -A -S"tools/add_vgraph_xrefs.py" analysis/ida_falconcd/FALCONCD.EXE.i64
"""
import json
import traceback
from pathlib import Path

import idc
import idaapi
import ida_loader
import ida_funcs
import ida_bytes

ROOT       = r"C:\Users\ybarnoy\projects\falcon3"
LOG_PATH   = ROOT + r"\analysis\ida_falconcd\add_vgraph_xrefs.log"
IDB_PATH   = ROOT + r"\analysis\ida_falconcd\FALCONCD.EXE.i64"

VGRAPH_EA    = 0x85AE0
IMAGE_PARA   = 0x1F5
VGRAPH_CS    = 0x77A3   # runtime CS

TRACE_FILES = [
    ROOT + r"\memdump\harvctl3_fileio.jsonl",
    ROOT + r"\memdump\debug_test_fileio.jsonl",
    ROOT + r"\memdump\trace_20261015_211031_fileio.jsonl",
    ROOT + r"\memdump\trace_20261014_231428_fileio.jsonl",
]

log = []


def runtime_to_ida(cs, ip):
    """Convert runtime CS:IP to IDA linear address."""
    link_seg = cs - IMAGE_PARA
    return link_seg * 16 + 0x10000 + ip


def parse_hex_csip(s):
    cs_s, ip_s = s.upper().split(":")
    return int(cs_s, 16), int(ip_s, 16)


def main():
    # Collect unique (caller_ida, target_ida) pairs with call counts
    pairs = {}  # (caller_ida, target_ida) -> count
    target_counts = {}  # target_ida -> count

    for fname in TRACE_FILES:
        path = Path(fname)
        if not path.exists():
            log.append("SKIP (not found): %s" % fname)
            continue
        n = 0
        with open(fname, encoding="utf-8", errors="replace") as f:
            for line in f:
                if "indirect_far" not in line or "77A3" not in line.upper():
                    continue
                try:
                    r = json.loads(line)
                    if r.get("ev") != "indirect_far":
                        continue
                    target = r.get("target", "")
                    caller = r.get("caller", "")
                    if not target or not caller:
                        continue
                    tcs, tip = parse_hex_csip(target)
                    ccs, cip = parse_hex_csip(caller)
                    if tcs != VGRAPH_CS:
                        continue
                    caller_ida = runtime_to_ida(ccs, cip)
                    target_ida = VGRAPH_EA + tip
                    key = (caller_ida, target_ida)
                    pairs[key] = pairs.get(key, 0) + 1
                    target_counts[target_ida] = target_counts.get(target_ida, 0) + 1
                    n += 1
                except Exception:
                    pass
        log.append("%s: %d VGRAPH call records" % (Path(fname).name, n))

    log.append("Total unique (caller, target) pairs: %d" % len(pairs))
    log.append("Total VGRAPH targets with traces: %d" % len(target_counts))

    # Add xrefs
    added = 0
    skipped_no_caller = 0
    for (caller_ida, target_ida), count in sorted(pairs.items()):
        # Verify target is in VGRAPH segment
        if not (VGRAPH_EA <= target_ida < VGRAPH_EA + 12005):
            continue
        # Check if caller has a valid code head
        fl = ida_bytes.get_flags(caller_ida)
        if not ida_bytes.is_code(fl):
            skipped_no_caller += 1
            continue
        # Add the xref (fl_CF = 16 = far call, XREF_USER)
        idc.add_cref(caller_ida, target_ida, idc.fl_CF | idc.XREF_USER)
        added += 1

    log.append("Xrefs added: %d (skipped caller not code: %d)" % (added, skipped_no_caller))

    # Annotate VGRAPH functions with call counts
    annotated = 0
    for target_ida, count in sorted(target_counts.items(), key=lambda x: -x[1]):
        f = ida_funcs.get_func(target_ida)
        if f and f.start_ea == target_ida:
            existing = idc.get_cmt(target_ida, 0) or ""
            cmt = "traced calls: %d" % count
            if cmt not in existing:
                idc.set_cmt(target_ida, cmt, 0)
            annotated += 1
    log.append("Functions annotated with call counts: %d" % annotated)

    # Count resulting xrefs into VGRAPH
    vg_xrefs = sum(1 for f_ea in idautils.Functions(VGRAPH_EA, VGRAPH_EA + 12005)
                   for _ in idautils.CodeRefsTo(f_ea, 0))
    log.append("Total xrefs into VGRAPH segment: %d" % vg_xrefs)

    # Save
    ida_loader.save_database(IDB_PATH, 0)
    log.append("database saved: %s" % IDB_PATH)


try:
    import idautils
    main()
except Exception:
    log.append("ERROR:\n" + traceback.format_exc())
    try:
        ida_loader.save_database(IDB_PATH, 0)
    except Exception:
        log.append("save after error failed")

open(LOG_PATH, "w").write("\n".join(log))
idaapi.qexit(0)
