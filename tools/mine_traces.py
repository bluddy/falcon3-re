#!/usr/bin/env python3
"""Mine FALCON_TRACE outputs (tools/run_falcon_traced.ps1 sessions).

Reads memdump/trace_*_{fileio,fartrans}.jsonl and produces:

  analysis/traces/file_summary.json       per-file open/read/byte stats per run
  analysis/traces/overlay_reads.json      EXE tail reads -> RAM segment map
                                          (RTLink overlay loads, finding 30a)
  analysis/traces/segment_classes.json    symbolic classification of observed
                                          segments: VGA, DGROUP candidates,
                                          overlay pool, resident targets

Everything here is derived ground truth from the instrumented build
(provenance PROVEN for the capture; interpretations are HYPOTHESIS until
cross-checked against memdump/*.BIN and the static IDB).
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DUMP_DIR = ROOT / "memdump"
OUT_DIR = ROOT / "analysis" / "traces"

# MZ tail start of FALCONCD.EXE (registry/FALCONCD.EXE.yaml: derived.tail_start)
TAIL_START = 0x1FB51
OVERLAY_READ_MIN = 1024   # bytes; below this, reads are not overlay candidates
VGA_LO, VGA_HI = 0xA000, 0xBFFF


def load_runs() -> dict[str, dict[str, list[dict]]]:
    runs: dict[str, dict[str, list[dict]]] = defaultdict(dict)
    for kind in ("fileio", "fartrans"):
        for path in sorted(DUMP_DIR.glob(f"trace_*_{kind}.jsonl")):
            run = path.name[: -len(f"_{kind}.jsonl")]
            runs[run][kind] = [json.loads(line) for line in path.open()]
    return dict(runs)


def mine_fileio(events: list[dict]) -> dict:
    per_file: dict[str, dict] = {}
    overlay_reads: list[dict] = []
    for e in events:
        ev = e.get("ev")
        name = (e.get("name") or "").lower()
        if not name:
            continue
        st = per_file.setdefault(name, {"opens": 0, "reads": 0, "bytes": 0})
        if ev == "open" and e.get("ok"):
            st["opens"] += 1
        elif ev == "read" and e.get("ok"):
            st["reads"] += 1
            st["bytes"] += e["size"]
            buf_seg = int(e["buf"][:4], 16)
            buf_off = int(e["buf"][5:], 16)
            if (name.endswith(".exe") and e["size"] >= OVERLAY_READ_MIN
                    and e["offset"] >= TAIL_START and buf_off == 0):
                overlay_reads.append({
                    "file": e["name"],
                    "offset": e["offset"],
                    "size": e["size"],
                    "buf_seg": buf_seg,
                })
    overlay_reads.sort(key=lambda r: r["offset"])
    top = sorted(per_file.items(), key=lambda kv: -kv[1]["bytes"])[:20]
    return {
        "files": per_file,
        "top_by_bytes": [
            {"file": f, **st} for f, st in top if st["bytes"]
        ],
        "overlay_reads": overlay_reads,
    }


def mine_fartrans(rows: list[dict]) -> dict:
    ds_hist: Counter[int] = Counter()
    es_hist: Counter[int] = Counter()
    ss_hist: Counter[int] = Counter()
    cs_totals: dict[int, dict] = {}
    for r in rows:
        cs = r["cs"]
        t = cs_totals.setdefault(cs, {
            "calls": 0, "jumps": 0, "targets": [],
            "ds": Counter(), "es": Counter(),
        })
        t["calls"] += r["calls"]
        t["jumps"] += r["jumps"]
        t["targets"].append(r["ip"])
        for h in r["ds"]:
            if h["seg"] is not None:
                ds_hist[h["seg"]] += h["n"]
                t["ds"][h["seg"]] += h["n"]
        for h in r["es"]:
            if h["seg"] is not None:
                es_hist[h["seg"]] += h["n"]
                t["es"][h["seg"]] += h["n"]

    total_ds = sum(ds_hist.values()) or 1
    dgroup_candidates = [
        {"seg": seg, "n": n, "share": round(n / total_ds, 4)}
        for seg, n in ds_hist.most_common(8)
    ]
    vga_es = [
        {"seg": seg, "n": n}
        for seg, n in es_hist.most_common()
        if VGA_LO <= seg <= VGA_HI
    ]
    targets = []
    for cs, t in sorted(cs_totals.items(), key=lambda kv: -(kv[1]["calls"] + kv[1]["jumps"])):
        targets.append({
            "cs": cs,
            "calls": t["calls"],
            "jumps": t["jumps"],
            "n_ips": len(set(t["targets"])),
            "dominant_ds": t["ds"].most_common(1)[0][0] if t["ds"] else None,
            "dominant_es": t["es"].most_common(1)[0][0] if t["es"] else None,
        })
    return {
        "far_calls_total": sum(t["calls"] for t in cs_totals.values()),
        "far_jumps_total": sum(t["jumps"] for t in cs_totals.values()),
        "distinct_target_cs": len(cs_totals),
        "entry_ds_top": dgroup_candidates,
        "entry_es_vga": vga_es,
        "targets": targets,
    }


def cross_correlate(runs: dict[str, dict]) -> dict:
    """Overlay pool = EXE-tail read destinations; overlay code = their CS
    values that also appear as far-call targets (or not — data blocks)."""
    result: dict = {"offset_to_segments": {}, "pool_by_run": {}}
    offset_map: dict[int, set[int]] = defaultdict(set)
    for run, kinds in runs.items():
        pool: Counter[int] = Counter()
        for r in kinds.get("fileio_mined", {}).get("overlay_reads", []):
            offset_map[r["offset"]].add(r["buf_seg"])
            pool[r["buf_seg"]] += r["size"]
        if pool:
            result["pool_by_run"][run] = [
                {"seg": seg, "bytes_read": n} for seg, n in pool.most_common()
            ]
        # which pool segments host far-call targets (=> code overlays)
        ft = kinds.get("fartrans_mined", {})
        code = {t["cs"] for t in ft.get("targets", [])}
        if pool:
            result.setdefault("pool_code_segments", {})[run] = [
                {"seg": seg, "bytes_read": n, "is_farcall_target": seg in code}
                for seg, n in pool.most_common()
            ]
    result["offset_to_segments"] = {
        str(off): sorted(segs) for off, segs in sorted(offset_map.items())
    }
    # stability: offsets mapping to >1 segment across all runs
    unstable = {
        off: segs for off, segs in result["offset_to_segments"].items()
        if len(segs) > 1
    }
    result["unstable_offsets"] = unstable
    return result


def cross_ref_rtlink(runs: dict[str, dict]) -> dict:
    """Join overlay reads with static RTLink records (overlay_placement.json:
    data_file = record offset in the EXE) -> record idx -> runtime segment.

    This is finding 30 deliverable (a): RTLink overlay loads as
    file-offset -> RAM-segment, joined to the static record table.
    """
    placement_path = ROOT / "analysis" / "ida_falconcd" / "overlay_placement.json"
    if not placement_path.exists():
        return {"error": "overlay_placement.json not found"}
    placement = json.loads(placement_path.read_text())

    ranges = []
    for rec in placement:
        start = rec.get("data_file")
        if start is None:
            continue
        size = max(rec.get("span_bytes") or 0, rec.get("length") or 0,
                   rec.get("real_len") or 0)
        ranges.append((start, start + max(size, 1), rec["idx"], size))

    loads: list[dict] = []
    unmatched = 0
    record_segments: dict[int, dict] = {}
    for run, kinds in runs.items():
        for r in kinds.get("fileio_mined", {}).get("overlay_reads", []):
            off = r["offset"]
            hit = next((rg for rg in ranges if rg[0] <= off < rg[1]), None)
            if hit is None:
                # fall back: nearest record start at/below the offset
                candidates = [rg for rg in ranges if rg[0] <= off]
                if not candidates:
                    unmatched += 1
                    continue
                hit = max(candidates, key=lambda rg: rg[0])
            rec_idx = hit[2]
            entry = record_segments.setdefault(
                rec_idx, {"record_idx": rec_idx, "segments": Counter(),
                          "offsets": set(), "bytes": 0})
            entry["segments"][r["buf_seg"]] += r["size"]
            entry["offsets"].add(off)
            entry["bytes"] += r["size"]
            loads.append({"run": run, "record_idx": rec_idx,
                          "offset": off, "size": r["size"],
                          "buf_seg": r["buf_seg"]})

    out_records = []
    for rec_idx, e in sorted(record_segments.items()):
        out_records.append({
            "record_idx": rec_idx,
            "segments": [seg for seg, _ in e["segments"].most_common()],
            "bytes_read": e["bytes"],
            "offsets": sorted(e["offsets"]),
            "stable_segment": len(e["segments"]) == 1,
        })
    return {"loads": loads, "records": out_records,
            "unmatched_reads": unmatched}


def main() -> int:
    runs_raw = load_runs()
    if not runs_raw:
        print(f"no trace_* files in {DUMP_DIR}")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary: dict = {}
    for run, kinds in sorted(runs_raw.items()):
        fio = mine_fileio(kinds.get("fileio", []))
        ft = mine_fartrans(kinds.get("fartrans", []))
        kinds["fileio_mined"] = fio
        kinds["fartrans_mined"] = ft
        summary[run] = {
            "fileio_events": len(kinds.get("fileio", [])),
            "top_files": fio["top_by_bytes"][:10],
            "overlay_reads": len(fio["overlay_reads"]),
            "far_calls": ft["far_calls_total"],
            "far_jumps": ft["far_jumps_total"],
            "distinct_target_cs": ft["distinct_target_cs"],
            "entry_ds_top": ft["entry_ds_top"][:4],
            "entry_es_vga": ft["entry_es_vga"],
        }
        # per-run artifacts
        (OUT_DIR / f"{run}_file_summary.json").write_text(
            json.dumps({"files": fio["files"], "top_by_bytes": fio["top_by_bytes"]},
                       indent=1) + "\n")
        (OUT_DIR / f"{run}_overlay_reads.json").write_text(
            json.dumps(fio["overlay_reads"], indent=1) + "\n")
        (OUT_DIR / f"{run}_segment_classes.json").write_text(
            json.dumps({k: v for k, v in ft.items() if k != "targets"} |
                       {"targets": ft["targets"][:200]}, indent=1) + "\n")

    xcorr = cross_correlate(runs_raw)
    (OUT_DIR / "overlay_load_map.json").write_text(
        json.dumps(xcorr, indent=1) + "\n")
    rt = cross_ref_rtlink(runs_raw)
    (OUT_DIR / "rtlink_loads.json").write_text(
        json.dumps(rt, indent=1) + "\n")
    (OUT_DIR / "summary.json").write_text(
        json.dumps(summary, indent=1) + "\n")

    # readable report
    for run, s in summary.items():
        print(f"== {run} ==")
        print(f"  far calls {s['far_calls']}, jumps {s['far_jumps']}, "
              f"target CS {s['distinct_target_cs']}, overlay reads {s['overlay_reads']}")
        print(f"  top DS: {s['entry_ds_top']}")
        print(f"  VGA ES: {s['entry_es_vga']}")
        for f in s["top_files"][:5]:
            print(f"  file {f['file']}: {f['bytes']} B in {f['reads']} reads")
    n_unstable = len(xcorr["unstable_offsets"])
    print(f"overlay offsets tracked: {len(xcorr['offset_to_segments'])}, "
          f"unstable across runs: {n_unstable}")
    for run, segs in xcorr.get("pool_code_segments", {}).items():
        code = [s for s in segs if s["is_farcall_target"]]
        print(f"  {run}: pool {len(segs)} segs, of which {len(code)} host far-call targets")
    if "records" in rt:
        stable = sum(1 for r in rt["records"] if r["stable_segment"])
        multi = [r for r in rt["records"] if not r["stable_segment"]]
        print(f"RTLink join: {len(rt['records'])} records loaded at runtime, "
              f"{stable} stable segment, {len(multi)} reused elsewhere, "
              f"unmatched reads {rt.get('unmatched_reads')}")
        for r in multi:
            print(f"  record {r['record_idx']} segments={[hex(s) for s in r['segments']]}")
    print(f"wrote {OUT_DIR}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
