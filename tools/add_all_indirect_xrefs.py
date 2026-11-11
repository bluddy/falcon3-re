"""S3 Trace edges (finding 177 cont): add all traced indirect-far call xrefs.

Reads all 'indirect_far' records from fileio trace files, converts caller CS:IP
and target CS:IP to IDA ea using the standard formula:
    link_seg = cs - IMAGE_PARA (0x1F5)
    ida_ea   = link_seg * 16 + 0x10000 + ip_offset

Only adds xrefs when BOTH caller and target have valid code heads in the IDB.
Annotates target functions with traced call counts.

Usage:
  idat -A -S"tools/add_all_indirect_xrefs.py" analysis/ida_falconcd/FALCONCD.EXE.i64
"""
import json
import traceback
from pathlib import Path

import idc
import idaapi
import ida_loader
import ida_funcs
import ida_bytes
import idautils
import ida_segment

ROOT       = r"C:\Users\ybarnoy\projects\falcon3"
LOG_PATH   = ROOT + r"\analysis\ida_falconcd\add_indirect_xrefs.log"
IDB_PATH   = ROOT + r"\analysis\ida_falconcd\FALCONCD.EXE.i64"

IMAGE_PARA = 0x1F5

TRACE_FILES = [
    ROOT + r"\memdump\harvctl3_fileio.jsonl",
    ROOT + r"\memdump\debug_test_fileio.jsonl",
    ROOT + r"\memdump\trace_20261014_231428_fileio.jsonl",
]

log = []


def runtime_to_ida(cs, ip):
    link_seg = cs - IMAGE_PARA
    return link_seg * 16 + 0x10000 + ip


def is_valid_code_ea(ea):
    """Return True if ea is a code head in a known IDA segment."""
    seg = ida_segment.getseg(ea)
    if seg is None:
        return False
    fl = ida_bytes.get_flags(ea)
    return ida_bytes.is_code(fl)


def main():
    # Collect unique (caller_ida, target_ida) pairs with counts
    pairs = {}
    target_counts = {}
    skipped_no_seg = 0
    skipped_low_cs = 0

    for fname in TRACE_FILES:
        path = Path(fname)
        if not path.exists():
            log.append("SKIP (not found): %s" % fname)
            continue
        n_found = n_total = 0
        with open(fname, encoding="utf-8", errors="replace") as f:
            for line in f:
                if "indirect_far" not in line:
                    continue
                try:
                    r = json.loads(line)
                    if r.get("ev") != "indirect_far":
                        continue
                    target = r.get("target", "")
                    caller = r.get("caller", "")
                    if not target or not caller:
                        continue
                    tcs = int(target.split(":")[0], 16)
                    tip = int(target.split(":")[1], 16)
                    ccs = int(caller.split(":")[0], 16)
                    cip = int(caller.split(":")[1], 16)
                    n_total += 1
                    if ccs <= IMAGE_PARA or tcs <= IMAGE_PARA:
                        skipped_low_cs += 1
                        continue
                    caller_ida = runtime_to_ida(ccs, cip)
                    target_ida = runtime_to_ida(tcs, tip)
                    if not is_valid_code_ea(caller_ida) or not is_valid_code_ea(target_ida):
                        skipped_no_seg += 1
                        continue
                    key = (caller_ida, target_ida)
                    pairs[key] = pairs.get(key, 0) + 1
                    target_counts[target_ida] = target_counts.get(target_ida, 0) + 1
                    n_found += 1
                except Exception:
                    pass
        log.append("%s: %d/%d pairs resolved" % (Path(fname).name, n_found, n_total))

    log.append("Unique resolved (caller, target) pairs: %d" % len(pairs))
    log.append("Unique target functions: %d" % len(target_counts))
    log.append("Skipped (no segment): %d" % skipped_no_seg)
    log.append("Skipped (cs <= IMAGE_PARA): %d" % skipped_low_cs)

    # Add xrefs
    added = 0
    for (caller_ida, target_ida), count in sorted(pairs.items()):
        # Already have VGRAPH xrefs from finding 177; still adds them again (idempotent)
        idc.add_cref(caller_ida, target_ida, idc.fl_CF | idc.XREF_USER)
        added += 1
    log.append("Xrefs added: %d" % added)

    # Annotate target functions with call counts
    annotated = 0
    for target_ida, count in sorted(target_counts.items(), key=lambda x: -x[1]):
        f = ida_funcs.get_func(target_ida)
        if f and f.start_ea == target_ida:
            existing = idc.get_cmt(target_ida, 0) or ""
            cmt = "traced calls: %d" % count
            if cmt not in existing:
                idc.set_cmt(target_ida, cmt, 0)
            annotated += 1
    log.append("Functions annotated: %d" % annotated)

    # Save
    ida_loader.save_database(IDB_PATH, 0)
    log.append("database saved")


try:
    main()
except Exception:
    log.append("ERROR:\n" + traceback.format_exc())
    try:
        ida_loader.save_database(IDB_PATH, 0)
    except Exception:
        pass

open(LOG_PATH, "w").write("\n".join(log))
idaapi.qexit(0)
