#!/usr/bin/env python3
"""Symbolic segment classification from a FALCON_TRACE run.

Consumes memdump/<run>_fartrans.jsonl + <run>_fileio.jsonl and the mined
artifacts under analysis/traces/, and emits one record per observed segment:

  seg -> { kind, alias, evidence }

kinds (advice.md §2 table):
  SEG_DGROUP          the one DS most far-calls enter with
  SEG_STATIC + delta  resident image (segment containing the load base)
  SEG_OVERLAY_ID(n)   RTLink overlay pool slot, n = pool index
  SEG_HEAP_ALLOC      observed as an INT 21h AH=48h block (site-tagged)
  SEG_VGA_VRAM        0xA000-0xBFFF
  SEG_UNKNOWN         everything else worth keeping

DGROUP selection is a HYPOTHESIS: the highest-share entry DS, printed with
its share so a reviewer can judge. Cross-run agreement is reported so a
segment that is DGROUP in one run and not the other is flagged.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DUMP_DIR = ROOT / "memdump"
OUT_DIR = ROOT / "analysis" / "traces"

VGA_LO, VGA_HI = 0xA000, 0xBFFF

# Resident-image mapping, PROVEN in finding 33 (see
# analysis/traces/boundary_report.json:{"mapping"}):
#     runtime_seg = ida_seg - 0xE0B      (image base para 0x1F5)
#     ida_lin     = runtime_lin + 0xE0B0
# IDA seg000 spans 0x10000-0x10210 and seg020 0x1F6C0-0x2AA30, so the runtime
# image window is [0x1F5, 0x1F5 + (0x2CF51-0x10000)>>4) = [0x1F5, 0x1EDF).
IMAGE_PARA = 0x1F5
RESIDENT_LO = 0x1F5
RESIDENT_HI = 0x1F5 + ((0x2CF51 - 0x10000) >> 4)  # 0x1EDF
NON_CODE_CS = {0x188}  # PSP-style entry point (segment, offset 0); not code


def iter_runs() -> list[str]:
    names = {p.name.split("_fartrans")[0] for p in DUMP_DIR.glob("*_fartrans.jsonl")}
    return sorted(names)


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def classify_run(run: str) -> dict:
    ft = read_jsonl(DUMP_DIR / f"{run}_fartrans.jsonl")
    fio = read_jsonl(DUMP_DIR / f"{run}_fileio.jsonl")

    entry_ds: Counter[int] = Counter()
    target_cs: Counter[int] = Counter()
    es_obs: Counter[int] = Counter()
    # per (cs,ip) dominant DS — the per-IP view
    per_ip: dict[tuple[int, int], Counter[int]] = defaultdict(Counter)

    for r in ft:
        target_cs[r["cs"]] += r["calls"] + r["jumps"]
        for h in r.get("ds", []):
            if h.get("seg") is not None:
                entry_ds[h["seg"]] += h["n"]
                per_ip[(r["cs"], r["ip"])][h["seg"]] += h["n"]
        for h in r.get("es", []):
            if h.get("seg") is not None:
                es_obs[h["seg"]] += h["n"]

    # heap blocks from INT 21h AH=48h events (new hook; empty on old runs)
    heap_blocks: dict[int, list[str]] = defaultdict(list)
    for e in fio:
        if e.get("ev") == "mcb_alloc" and e.get("ok") and e.get("seg"):
            heap_blocks[e["seg"]].append(e.get("site", "?"))

    # DGROUP hypothesis. BC large model anchors DS to DGROUP on entry to every
    # far-called function, so the true DGROUP appears as the entry DS of the
    # LARGEST NUMBER of distinct entry IPs. Ranking by raw observation count
    # instead is wrong: it picks whichever module ran most in that run, and
    # the two runs disagreed (27687 vs 18084) even though both cover the same
    # entry-IP set. Marked HYPOTHESIS until a dump-side DGROUP pointer check
    # confirms it.
    ips_per_ds: Counter[int] = Counter()
    for (cs, ip), cnt in per_ip.items():
        if cs in NON_CODE_CS:
            continue
        if not cnt:
            continue
        ips_per_ds[cnt.most_common(1)[0][0]] += 1
    total_ds = sum(entry_ds.values()) or 1
    dgroup = ips_per_ds.most_common(1)[0][0] if ips_per_ds else None
    dgroup_share = (entry_ds[dgroup] / total_ds) if dgroup else 0.0

    # resident base: PROVEN (finding 32/33), not derived from the trace
    resident_base = IMAGE_PARA

    # overlay pool: mined overlay_load_map. A pool segment is a segment that
    # received an EXE-tail read; its size is the largest read seen there.
    pool: list[int] = []
    pool_sizes: dict[int, int] = {}
    ovl_map = OUT_DIR / "overlay_load_map.json"
    if ovl_map.exists():
        xcorr = json.loads(ovl_map.read_text())
        for run_pool in xcorr.get("pool_by_run", {}).values():
            for e in run_pool:
                pool.append(e["seg"])
                if e["bytes_read"] > pool_sizes.get(e["seg"], 0):
                    pool_sizes[e["seg"]] = e["bytes_read"]
    pool = sorted(set(pool))

    seg_info: dict[int, dict] = {}

    # Precedence: overlay pool > heap > VGA > DGROUP > resident > runtime >
    # unknown. A segment can qualify for several (e.g. DGROUP is also a
    # resident segment), so classify in one pass by rank rather than calling
    # note() repeatedly — note() sets kind once and only merges evidence.
    rank = {"SEG_OVERLAY": 9, "SEG_HEAP_ALLOC": 8, "SEG_VGA_VRAM": 7,
            "SEG_DGROUP": 6, "SEG_STATIC": 5, "SEG_RUNTIME": 4,
            "SEG_DATA": 1, "SEG_UNKNOWN": 0}

    def rank_of(kind: str) -> int:
        return max((v for k, v in rank.items() if kind.startswith(k)), default=0)

    def note(seg: int, kind: str, alias: str | None = None, **ev):
        """Record a classification. A segment may carry SEVERAL kinds (a
        DS-anchored data segment can also sit inside an overlay pool block),
        so every distinct kind is kept in ``kinds`` with its own evidence.
        ``kind``/``alias`` hold the highest-rank kind for consumers that want
        a single label; ``kinds`` is the authoritative view.
        """
        e = seg_info.setdefault(seg, {"seg": seg, "kind": kind, "alias": alias,
                                      "kinds": [], "evidence": {}})
        if kind not in e["kinds"]:
            e["kinds"].append(kind)
        if rank_of(kind) > rank_of(e["kind"]):
            e["kind"] = kind
            e["alias"] = alias
        if alias and e["kind"] == kind:
            e["alias"] = alias
        e["evidence"].setdefault(kind, {}).update(ev)

    # Every segment seen either as a far-call target (code) or as an entry DS
    # (data) gets a record; the passes below layer on additional kinds.
    for seg in target_cs:
        note(seg, "SEG_UNKNOWN")
    for seg in entry_ds:
        note(seg, "SEG_DATA")

    # A read of size N at base B occupies paragraphs [B, B + N>>4), so segments
    # that land inside a pool block are overlay data. Segments above the pool
    # that no read explains (F000 = BIOS, etc.) are SEG_RUNTIME.
    pool_ranges: list[tuple[int, int, int]] = []  # (base, end_exclusive, pool_i)
    for i, seg in enumerate(pool):
        size = pool_sizes.get(seg, 0)
        pool_ranges.append((seg, seg + max(size >> 4, 1), i))

    def owning_pool(seg: int) -> int | None:
        for base, end, i in pool_ranges:
            if base <= seg < end:
                return i
        return None

    # Pool membership: exact base segments, then any segment carved out of one
    # of those blocks. (No gate — kinds accumulate.)
    for i, seg in enumerate(pool):
        note(seg, f"SEG_OVERLAY_ID({i})", alias=f"OVL_{i:02d}_{seg:04X}",
             bytes_read=pool_sizes.get(seg, 0))

    for seg in sorted(set(target_cs) | set(entry_ds)):
        if seg in NON_CODE_CS:
            continue
        i = owning_pool(seg)
        if i is not None:
            note(seg, f"SEG_OVERLAY_DATA({i})", alias=f"OVLD_{i:02d}_{seg:04X}",
                 pool_base=pool[i])
        elif seg >= RESIDENT_HI:
            note(seg, "SEG_RUNTIME", alias=f"RT_{seg:04X}")

    for seg, sites in heap_blocks.items():
        note(seg, "SEG_HEAP_ALLOC", alias=f"HEAP_{seg:04X}",
             alloc_sites=sorted(set(sites))[:8])

    for seg in es_obs:
        if VGA_LO <= seg <= VGA_HI:
            note(seg, "SEG_VGA_VRAM", alias=f"VGA_{seg:04X}",
                 es_observations=es_obs[seg])

    if dgroup is not None:
        note(dgroup, "SEG_DGROUP", alias="DGROUP",
             share=round(dgroup_share, 4), total_obs=total_ds)

    if resident_base is not None:
        for seg in sorted(set(target_cs) | set(entry_ds)):
            if seg in NON_CODE_CS:
                continue
            if RESIDENT_LO <= seg < RESIDENT_HI:
                note(seg, "SEG_STATIC", alias=f"IMG_{seg:04X}",
                     image_base=resident_base)

    # per-IP dominant DS (the detail needed for per-function DGROUP checks)
    ip_rows = []
    for (cs, ip), cnt in sorted(per_ip.items()):
        dom, n = cnt.most_common(1)[0]
        tot = sum(cnt.values())
        ip_rows.append({"cs": cs, "ip": ip, "dominant_ds": dom,
                        "share": round(n / tot, 4), "observations": tot})

    return {
        "run": run,
        "dgroup_hypothesis": {"seg": dgroup, "share": round(dgroup_share, 4),
                              "certainty": "HYPOTHESIS"},
        "resident_base": {"seg": resident_base, "certainty": "PROVEN",
                          "source": "finding 32/33 (entry bytes + MCB owner + "
                                    "30 RTLink records + 3 seg020 fns)"},
        "segments": [seg_info[s] for s in sorted(seg_info)],
        "heap_blocks_observed": len(heap_blocks),
        "per_ip": ip_rows,
    }


def cross_run(results: list[dict]) -> dict:
    """Agreement check: DGROUP/resident-base stable across runs?"""
    dg = {r["dgroup_hypothesis"]["seg"] for r in results}
    rb = {r["resident_base"]["seg"] for r in results}
    per_run_dgroup = {r["run"]: r["dgroup_hypothesis"] for r in results}
    per_run_base = {r["run"]: r["resident_base"] for r in results}
    return {
        "dgroup_agreement": {"segments": sorted(x for x in dg if x is not None),
                             "stable": len(dg) == 1,
                             "per_run": per_run_dgroup},
        "resident_base_agreement": {"segments": sorted(x for x in rb if x is not None),
                                    "stable": len(rb) == 1,
                                    "per_run": per_run_base},
    }


def main() -> int:
    runs = iter_runs()
    if not runs:
        print("no *_fartrans.jsonl in memdump/")
        return 1
    results = [classify_run(r) for r in runs]
    merged = cross_run(results)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "segment_classification.json").write_text(
        json.dumps({"runs": results, "cross_run": merged}, indent=1) + "\n")

    for r in results:
        dg = r["dgroup_hypothesis"]
        rb = r["resident_base"]
        # kinds are multi-valued; tally every kind, and count primary separately
        allk = Counter(k for s in r["segments"] for k in s.get("kinds", [s["kind"]]))
        primary = Counter(s["kind"] for s in r["segments"])
        print(f"== {r['run']} ==")
        print(f"  DGROUP? seg={dg['seg']} share={dg['share']} ({dg['certainty']})")
        print(f"  resident base seg={rb['seg']} ({rb['certainty']})")
        print(f"  heap blocks: {r['heap_blocks_observed']}")
        print(f"  segments: {len(r['segments'])} "
              f"(multi-kind: {dict(sorted(allk.items()))})")
        print(f"  primary kind: {dict(sorted(primary.items()))}")
        print(f"  per-IP rows: {len(r['per_ip'])}")
    x = merged
    print(f"cross-run DGROUP stable: {x['dgroup_agreement']['stable']} "
          f"{x['dgroup_agreement']['segments']}")
    print(f"cross-run resident base stable: {x['resident_base_agreement']['stable']} "
          f"{x['resident_base_agreement']['segments']}")
    print(f"wrote {OUT_DIR / 'segment_classification.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
