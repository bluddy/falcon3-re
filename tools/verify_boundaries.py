#!/usr/bin/env python3
"""Trace-driven function-boundary verification (finding 32 follow-up).

The far-call/far-jump targets in the FALCON_TRACE fartrans logs are TRUE
runtime function entry points. Convert them to IDA addresses using the
PROVEN session-A mapping (finding 32):

    runtime_seg = ida_seg - 0xE0B        (image base para 0x1F5)
    ida_lin     = runtime_lin + 0xE0B0

Overlay-pool targets are resolved via analysis/traces/rtlink_loads.json
(runtime segment -> RTLink record -> record ida_ea from
analysis/ida_falconcd/overlay_placement.json).

Each target is classified against function_bytes.json ground truth:

    EXACT   a registered function starts at exactly this address
    MID     lands strictly inside a registered function
            (= finding-29-style boundary error evidence)
    UNKNOWN no registered function covers it (missed-function candidate
            if resident; unregistered overlay fn if in a pool record)
    OTHER   not in the image/pool (BIOS, DOS, drivers, VGA) — counted only

Output: analysis/traces/boundary_report.json + readable summary.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACE_DIR = ROOT / "analysis" / "traces"
FB_PATH = ROOT / "analysis" / "ida_falconcd" / "function_bytes.json"
PLACEMENT_PATH = ROOT / "analysis" / "ida_falconcd" / "overlay_placement.json"
RTLINK_LOADS = TRACE_DIR / "rtlink_loads.json"
OUT_PATH = TRACE_DIR / "boundary_report.json"

# finding 32 (session A)
IDA_BASE_LINEAR = 0x10000
IMAGE_PARA = 0x1F5
RESIDENT_LO = IMAGE_PARA
RESIDENT_HI = IMAGE_PARA + (0x1CF51 >> 4)  # ~0x1EEA


def load_merged_targets() -> dict[tuple[int, int], dict]:
    merged: dict[tuple[int, int], dict] = {}
    dump_dir = ROOT / "memdump"
    for path in sorted(dump_dir.glob("trace_*_fartrans.jsonl")):
        run = path.name[: -len("_fartrans.jsonl")]
        for line in path.open():
            r = json.loads(line)
            key = (r["cs"], r["ip"])
            m = merged.setdefault(key, {
                "calls": 0, "jumps": 0, "runs": set(),
                "dominant_ds": None, "ds_n": 0,
            })
            m["calls"] += r["calls"]
            m["jumps"] += r["jumps"]
            m["runs"].add(run)
            for h in r["ds"]:
                if h["seg"] is not None and h["n"] > m["ds_n"]:
                    m["dominant_ds"] = h["seg"]
                    m["ds_n"] = h["n"]
    return merged


def classify_target(cs: int, ip: int, seg_to_records: dict[int, list[int]],
                    placement: dict[int, dict], fns_by_ea: dict[int, tuple[str, dict]],
                    fn_intervals: list[tuple[int, int, str, dict]]) -> dict:
    if RESIDENT_LO <= cs < RESIDENT_HI:
        ida_ea = (cs << 4) + ip + (IDA_BASE_LINEAR - (IMAGE_PARA << 4))
        region = "resident"
    elif cs in seg_to_records:
        rec_idx = seg_to_records[cs][0]
        rec = placement.get(rec_idx)
        if not rec or rec.get("ida_ea") is None:
            return {"region": "overlay", "ida_ea": None, "status": "NO_RECORD"}
        ida_ea = rec["ida_ea"] + ip
        region = f"overlay:rec{rec_idx}"
    else:
        return {"region": "other", "ida_ea": None, "status": "OTHER"}

    out: dict = {"region": region, "ida_ea": ida_ea}
    if ida_ea in fns_by_ea:
        key, fn = fns_by_ea[ida_ea]
        out.update(status="EXACT", fn=key, fn_size=fn["size"],
                   fn_name=fn.get("name"))
        return out
    import bisect
    starts = [iv[0] for iv in fn_intervals]
    i = bisect.bisect_right(starts, ida_ea) - 1
    if i >= 0:
        start, end, key, fn = fn_intervals[i]
        if ida_ea < end:
            out.update(status="MID", fn=key, fn_ea=start, fn_size=fn["size"],
                       offset=ida_ea - start, fn_name=fn.get("name"))
            return out
    # unknown: upper bound = next known ea or +0x400
    j = bisect.bisect_right(starts, ida_ea)
    next_ea = fn_intervals[j][0] if j < len(fn_intervals) else ida_ea + 0x400
    out.update(status="UNKNOWN", span_to_next_fn=next_ea - ida_ea)
    return out


def main() -> int:
    fb = json.loads(FB_PATH.read_text())
    fns_by_ea = {v["ea"]: (k, v) for k, v in fb.items()}
    fn_intervals = sorted(
        (v["ea"], v["ea"] + max(v["size"], 1), k, v) for k, v in fb.items())

    placement = {p["idx"]: p for p in json.loads(PLACEMENT_PATH.read_text())}
    seg_to_records: dict[int, list[int]] = defaultdict(list)
    rt = json.loads(RTLINK_LOADS.read_text())
    for rec in rt.get("records", []):
        for seg in rec["segments"]:
            seg_to_records[seg].append(rec["record_idx"])

    targets = load_merged_targets()
    report: dict = {
        "mapping": {"image_para": IMAGE_PARA,
                    "resident_runtime_range": [RESIDENT_LO, RESIDENT_HI]},
        "counts": defaultdict(int),
        "exact": [], "mid": [], "unknown": [], "other": [],
    }
    for (cs, ip), m in sorted(targets.items(), key=lambda kv: -(kv[1]["calls"] + kv[1]["jumps"])):
        info = classify_target(cs, ip, seg_to_records, placement,
                               fns_by_ea, fn_intervals)
        status = info["status"]
        report["counts"][status] += 1
        entry = {"cs": cs, "ip": ip, "calls": m["calls"], "jumps": m["jumps"],
                 "dominant_ds": m["dominant_ds"], **info}
        if status == "EXACT":
            report["exact"].append(entry)
        elif status == "MID":
            report["mid"].append(entry)
        elif status == "UNKNOWN":
            report["unknown"].append(entry)
        else:
            report["other"].append(entry)

    report["counts"] = dict(report["counts"])
    OUT_PATH.write_text(json.dumps(report, indent=1, default=list) + "\n")

    c = report["counts"]
    print(f"targets: {len(targets)}  {c}")
    mid_res = [e for e in report["mid"] if e["region"] == "resident"]
    print(f"MID (resident, boundary errors): {len(mid_res)}")
    for e in mid_res[:15]:
        print(f"  {e['cs']:04X}:{e['ip']:04X} +{e['offset']:#x} into "
              f"{e['fn']}({e['fn_size']}B) calls={e['calls']}")
    unk_res = [e for e in report["unknown"] if e["region"] == "resident"]
    unk_ovr = [e for e in report["unknown"] if e["region"].startswith("overlay")]
    print(f"UNKNOWN resident (missed fns): {len(unk_res)}; "
          f"overlay (unregistered): {len(unk_ovr)}")
    for e in unk_res[:15]:
        print(f"  res {e['cs']:04X}:{e['ip']:04X} calls={e['calls']} "
              f"span_to_next={e['span_to_next_fn']:#x}")
    for e in unk_ovr[:10]:
        print(f"  ovr {e['cs']:04X}:{e['ip']:04X} {e['region']} calls={e['calls']} "
              f"ida={e['ida_ea']:#x}")
    print(f"wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
