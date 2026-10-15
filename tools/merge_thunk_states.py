"""Thunk-state merge across all memdump snapshots.

advice.md "Fixing the Live Thunk Trap": thunks for *loaded* overlays hold a
live RAM target, while thunks for *swapped-out* overlays still point at the
disk loader. By merging every snapshot we learn, per thunk, which segment it
resolves to in which state — and can then patch the static table to the
resolved target.

Thunk = 10 bytes: `E8 disp16` (call loader) `EA off seg` (ljmp) `word rec_id`.
The live target is the `EA` operand; `rec_id` joins to the static
overlay_entries.json record ids.

Input : memdump/*.BIN, analysis/ida_falconcd/overlay_entries.json
Output: analysis/traces/thunk_states.json
"""
from __future__ import annotations

import json
import struct
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DUMP_DIR = ROOT / "memdump"
OUT = ROOT / "analysis" / "traces" / "thunk_states.json"
STATIC = ROOT / "analysis" / "ida_falconcd" / "overlay_entries.json"

THUNK_LEN = 10


def find_thunk_table(dump: bytes, min_run: int = 20) -> int | None:
    """Locate the thunk table by its E8..EA stride signature."""
    best = None
    for start in range(0, len(dump) - THUNK_LEN * min_run):
        if dump[start] != 0xE8 or dump[start + 3] != 0xEA:
            continue
        n = 0
        while start + (n + 1) * THUNK_LEN + 4 <= len(dump):
            b = start + n * THUNK_LEN
            if dump[b] == 0xE8 and dump[b + 3] == 0xEA:
                n += 1
            else:
                break
        if n >= min_run and (best is None or n > best[1]):
            best = (start, n)
    return best[0] if best else None


def read_thunks(dump: bytes, base: int) -> list[dict]:
    out = []
    for i in range((len(dump) - base) // THUNK_LEN):
        b = base + i * THUNK_LEN
        if dump[b] != 0xE8 or dump[b + 3] != 0xEA:
            break
        disp = struct.unpack_from("<h", dump, b + 1)[0]
        lo, seg, rec = struct.unpack_from("<HHH", dump, b + 4)
        out.append({"idx": i, "disp": disp, "ljmp_seg": seg, "ljmp_off": lo,
                    "rec_id": rec})
    return out


def main() -> int:
    static = json.loads(STATIC.read_text())
    static_by_row: dict[int, list[dict]] = defaultdict(list)
    for e in static:
        static_by_row[e["thunk_word"]].append(e)

    snapshots = sorted(DUMP_DIR.glob("*.BIN"))
    if not snapshots:
        print(f"no *.BIN in {DUMP_DIR}")
        return 1

    # Pass 1: locate every thunk table and record its base offset.
    table_info: dict[str, dict] = {}
    parsed: dict[str, list[dict]] = {}
    for p in snapshots:
        dump = p.read_bytes()
        base = find_thunk_table(dump)
        if base is None:
            print(f"  {p.name}: no thunk table found")
            continue
        thunks = read_thunks(dump, base)
        table_info[p.name] = {"base": base, "count": len(thunks)}
        parsed[p.name] = thunks
        print(f"  {p.name}: table @0x{base:X}, {len(thunks)} thunks")

    # Snapshots come from two sessions with different DOS load bases (the
    # thunk tables sit at 0x1D7BD vs 0x1DCED), so an absolute seg:off target
    # is not comparable across sessions: the whole image shifts by the table
    # delta while relative layout stays fixed. Normalise every target by
    # subtracting that dump's table delta from the reference (lowest-base)
    # dump, then group on the normalised value. This is the load-base-
    # independent form of advice.md's live-thunk resolution.
    if not table_info:
        print("no thunk tables parsed")
        return 1
    ref_base = min(t["base"] for t in table_info.values())

    # per rec_id -> normalised target -> snapshots where observed
    per_rec: dict[int, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for name, thunks in parsed.items():
        delta = table_info[name]["base"] - ref_base
        for t in thunks:
            norm_seg = t["ljmp_seg"] - (delta >> 4)
            norm = f"{norm_seg:04X}:{t['ljmp_off']:04X}"
            per_rec[t["rec_id"]][norm].add(name)

    # A target seen in every snapshot = stable (resolved everywhere);
    # anything seen in only some snapshots = transient (load-state dependent).
    n_snaps = len(table_info)
    records = []
    for rec_id in sorted(per_rec):
        targets = per_rec[rec_id]
        resolved = [t for t, s in targets.items() if len(s) == n_snaps]
        transient = [t for t, s in targets.items() if len(s) < n_snaps]
        records.append({
            "rec_id": rec_id,
            "snapshots": n_snaps,
            "resolved_targets": sorted(resolved),
            "transient_targets": sorted(transient),
            "stable": bool(resolved),
            "static_rows": sorted({e["seg_name"]
                                   for e in static_by_row.get(rec_id, [])}),
        })

    out = {
        "reference_base": ref_base,
        "thunk_tables": table_info,
        "n_records": len(records),
        "n_stable": sum(1 for r in records if r["stable"]),
        "n_transient": sum(1 for r in records if r["transient_targets"]),
        "records": records,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1) + "\n")

    print(f"\nrecords: {len(records)} | stable in all dumps: {out['n_stable']}"
          f" | transient: {out['n_transient']}")
    print(f"reference base: 0x{ref_base:X} ({n_snaps} snapshots)")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())