#!/usr/bin/env python3
"""First-pass inventory of the raw 1 MB conventional-RAM dumps in ./memdump.

Produces analysis/memdump/inventory.json (committed summary; the dumps
themselves stay local). Steps implemented here follow advice.md
("Snapshot Splicing" sections 1-2):

  * md5/size per dump
  * paragraph-level (16-byte) diffs between dump pairs -> resident vs
    overlay-pool regions (identical paragraphs = resident code)
  * IVT scan: vectors pointing into conventional game RAM
  * heuristic MCB-chain scan ('M' headers) to separate the EXE image from
    heap/overlay allocations

Certainty of every derived claim is only as good as the dump provenance
(docs/memdump.md: provenance UNKNOWN) — re-dump with the instrumented
dosbox-staging build to make these ground truth.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DUMP_DIR = ROOT / "memdump"
OUT_PATH = ROOT / "analysis" / "memdump" / "inventory.json"

PARA = 16
PARAS = 0x100000 // PARA
# DOSBox loads the game low (observed PSP at para 0x118 in the menu dump),
# so "above the DOS kernel" is a better filter than a fixed game range.
IVT_CS_MIN = 0x0100
# All dumps are diffed against this baseline (plus the legacy trio pairwise).
BASELINE = "MEMDUMP2_main_menu.BIN"
LEGACY_PAIRS = [
    ("MEMDUMP_menu.BIN", "MEMDUMP_sim.BIN"),
    ("MEMDUMP_menu.BIN", "MEMDUMP_mission.BIN"),
    ("MEMDUMP_sim.BIN", "MEMDUMP_mission.BIN"),
]


def md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def para_ranges(diff_mask: list[bool], cap: int = 400) -> list[list[int]]:
    """Merge differing paragraphs into [start_para, end_para_exclusive] ranges."""
    ranges: list[list[int]] = []
    start = None
    for i, differs in enumerate(diff_mask):
        if differs and start is None:
            start = i
        elif not differs and start is not None:
            ranges.append([start, i])
            start = None
    if start is not None:
        ranges.append([start, PARAS])
    if len(ranges) > cap:
        last = ranges[-1]
        return ranges[: cap - 1] + [
            [last[0], last[1], f"truncated: {len(ranges)} ranges total"]
        ]
    return ranges


def diff_pair(a: bytes, b: bytes) -> dict:
    diff_mask = []
    same = 0
    for p in range(PARAS):
        off = p * PARA
        eq = a[off : off + PARA] == b[off : off + PARA]
        diff_mask.append(not eq)
        if eq:
            same += 1
    return {
        "same_paras": same,
        "diff_paras": PARAS - same,
        "same_bytes": same * PARA,
        "diff_ranges_paras": para_ranges(diff_mask),
    }


def ivt_summary(mem: bytes) -> dict:
    above_kernel = []
    for vec in range(256):
        off = vec * 4
        ip = int.from_bytes(mem[off : off + 2], "little")
        cs = int.from_bytes(mem[off + 2 : off + 4], "little")
        if cs >= IVT_CS_MIN:
            above_kernel.append({"vec": vec, "cs": cs, "ip": ip})
    return {"total": 256, "in_game_range": above_kernel}


def mcb_scan(mem: bytes) -> dict:
    """Heuristic MCB chain discovery using the DOSBox sMCB layout
    (dos.h: type(1) psp_segment(2) size(2) unused[3] filename[8]).
    The next MCB is at cur + size + 1 — there is no next-pointer field.
    """
    heads = {}  # para -> (owner, size, type)
    for p in range(0x0060, 0x9F00):
        off = p * PARA
        t = mem[off]
        if t != 0x4D and t != 0x5A:  # 'M' or 'Z' (last block)
            continue
        owner = int.from_bytes(mem[off + 1 : off + 3], "little")
        size = int.from_bytes(mem[off + 3 : off + 5], "little")
        if size == 0 or size > 0xA000:
            continue
        if owner != 0 and owner != 8 and not (0x0040 <= owner <= 0x9FFF):
            continue
        heads[p] = (owner, size, t)

    chains = []
    for p, (owner, size, t) in sorted(heads.items()):
        # start only at a paragraph whose previous para is not also a head
        if (p - 1) in heads:
            continue
        chain = []
        cur = p
        while cur in heads and len(chain) < 512:
            owner, size, t = heads[cur]
            chain.append({"para": cur, "owner": owner, "size_paras": size})
            if t == 0x5A:  # 'Z' = last block
                break
            cur = cur + size + 1
        if len(chain) >= 3:
            total = sum(c["size_paras"] for c in chain)
            chains.append(
                {
                    "start_para": chain[0]["para"],
                    "blocks": len(chain),
                    "total_paras": total,
                    "total_bytes": total * PARA,
                    "first_owners": [c["owner"] for c in chain[:10]],
                }
            )
    chains.sort(key=lambda c: -c["total_paras"])
    return {"candidate_heads": len(heads), "chains_ge3": chains[:20]}


def main() -> int:
    names = sorted(p.name for p in DUMP_DIR.glob("*.BIN"))
    if not names:
        print(f"no *.BIN dumps in {DUMP_DIR}", file=sys.stderr)
        return 1

    data: dict[str, bytes] = {}
    for name in names:
        path = DUMP_DIR / name
        data[name] = path.read_bytes()
        if len(data[name]) != 0x100000:
            print(f"WARNING: {name} is {len(data[name])} bytes, expected 1 MB")

    inv: dict = {"dumps": {}, "pairwise_diff": {}, "per_dump": {}}
    for name, blob in data.items():
        inv["dumps"][name] = {"size": len(blob), "md5": md5(blob)}

    pairs: list[tuple[str, str]] = []
    baseline = BASELINE if BASELINE in data else names[0]
    for name in names:
        if name != baseline:
            pairs.append((baseline, name))
    for pair in LEGACY_PAIRS:
        if pair[0] in data and pair[1] in data and pair not in pairs:
            pairs.append(pair)

    for a, b in pairs:
        key = f"{a[:-4]}__vs__{b[:-4]}"
        inv["pairwise_diff"][key] = diff_pair(data[a], data[b])

    for name, blob in data.items():
        inv["per_dump"][name] = {
            "ivt": ivt_summary(blob),
            "mcb": mcb_scan(blob),
        }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(inv, indent=1) + "\n", encoding="utf-8")

    for name, meta in inv["dumps"].items():
        print(f"{name}: {meta['size']} B md5={meta['md5']}")
    for key, d in inv["pairwise_diff"].items():
        pct = 100.0 * d["diff_paras"] / PARAS
        print(f"{key}: {d['same_paras']} same / {d['diff_paras']} diff paras ({pct:.1f}% differ)")
    for name, d in inv["per_dump"].items():
        mcb = d["mcb"]
        print(f"{name}: IVT->above-kernel {len(d['ivt']['in_game_range'])} vectors; "
              f"MCB heads {mcb['candidate_heads']}, chains>=3: {len(mcb['chains_ge3'])}")
    print(f"wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
