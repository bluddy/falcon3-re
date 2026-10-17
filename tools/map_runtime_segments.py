"""Finding 60 step P1 (host, read-only): build the runtime-CS -> IDA map that
finding 51 called missing.

Rule proven across findings 32/56/57/60:
    runtime CS = link-time seg + IMAGE_PARA (0x1F5)
    record bases confirm it   (w0 + 0x1F5  == observed load segments)
    anchors confirm it       (link seg 0x1F64 -> IDA 0x2F640 = w0's record)
so for any target CS:  link_seg = cs - 0x1F5, and for every record whose link
arena [w0, w0+span) contains that paragraph:

    ida_ea = record.ida_ea + (link_seg - w0) * 16 + ip

Two records can claim the same paragraph (mutually exclusive variants of one
module -- R05_1E10 vs R29_1E10s both start at w0=0x1E10), and the loaded copy
changes with the scenario, so candidates are DISAMBIGUATED by content: does a
ret-like instruction END exactly at the target (checking `ret imm16` too)?
That is the same terminator evidence finding 59 used for boundaries.

Writes analysis/traces/runtime_seg_map.json:
  {"<cs>": {"link_seg": .., "events": N, "ips": [...],
            "candidates": [{idx, seg_name, base, hits, total}...]}}
and prints the resolution table.  Existing resident mapping is untouched.

Usage: venv\\Scripts\\python tools\\map_runtime_segments.py
"""
import glob
import json
import struct
from collections import Counter, defaultdict
from pathlib import Path

EXE = Path("game/FALCONCD.EXE").read_bytes()
IDA = Path("analysis/ida_falconcd")
OUT = Path("analysis/traces/runtime_seg_map.json")
DIR = 0x1E24F
IMAGE_PARA = 0x1F5
TERM1 = {0xC3, 0xCB, 0xCF}          # retn / retf / iret
TERM2 = {0xE9, 0xEB, 0xEA}          # jmp near / short / far
RES_LO, RES_HI = IMAGE_PARA, IMAGE_PARA + (0x1CF51 >> 4)

place = {p["idx"]: p for p in json.loads((IDA / "overlay_placement.json").read_text())}


def link_span(idx):
    o = DIR + idx * 18
    if o + 18 > len(EXE):
        return None
    w0, _a, _w2, _b, span, _n, _c, _d, _e = struct.unpack_from("<9H", EXE, o)
    return w0, span


def read_ida(ea, n=8):
    """Bytes at an IDA address (resident = file + 0xD400; overlays = placement)."""
    if 0x10000 <= ea < 0x2CF60:
        o = ea - 0xD400
        return EXE[o:o + n] if o >= 0 else None
    for p in place.values():
        if (p.get("ida_ea") is not None and p.get("ida_len")
                and p["ida_ea"] <= ea < p["ida_ea"] + p["ida_len"]):
            o = p["data_file"] + (ea - p["ida_ea"])
            return EXE[o:o + n]
    return None


def entry_before(t):
    """True if a ret-like or unconditional-jump instruction ENDS exactly at t.
    Covers the 1-byte forms (retn/retf/iret/short jmp), the 3-byte
    `ret imm16` / `jmp near` forms and the 5-byte far jmp."""
    raw = read_ida(t - 5, 5)
    if not raw:
        return False
    if len(raw) < 5:
        raw = b"\x00" * (5 - len(raw)) + raw
    b = raw
    if b[4] in (0xC3, 0xCB, 0xCF, 0xEB):
        return True
    if b[2] in (0xC2, 0xCA, 0xE9, 0xEA):
        return True
    if b[0] == 0xEA:
        return True
    return False


def main():
    # ---- gather every target CS:IP from all dumps (trace_* AND debug_test) ----
    pairs = Counter()
    for f in glob.glob("memdump/*_fileio.jsonl"):
        for line in open(f, encoding="utf-8", errors="replace"):
            if "indirect_far" not in line:
                continue
            e = json.loads(line)
            try:
                cs, ip = (int(x, 16) for x in e["target"].split(":"))
            except Exception:
                continue
            pairs[(cs, ip)] += 1
    tot_events = sum(pairs.values())

    spans = {}
    for idx in place:
        s = link_span(idx)
        if s:
            spans[idx] = s

    # read-evidence: which record's payload was observed being read into a CS
    # (mine_traces).  Used as a tie-break when content cannot decide alone.
    read_ev = defaultdict(set)
    try:
        rt = json.loads(Path("analysis/traces/rtlink_loads.json").read_text())
        for r in rt.get("records", []):
            for s in r.get("segments", []):
                read_ev[s].add(r["record_idx"])
    except Exception:
        pass

    out = {}
    resolved_events = 0
    resident_events = 0
    rows = []
    for cs in sorted({c for c, _ in pairs}):
        ips = sorted({ip for c, ip in pairs if c == cs})
        ev = sum(n for (c, ip), n in pairs.items() if c == cs)
        if RES_LO <= cs < RES_HI:
            resident_events += ev
            rows.append((cs, ev, "resident", len(ips), None))
            continue
        link_seg = cs - IMAGE_PARA
        cands = []
        for idx, (w0, span) in spans.items():
            p = place[idx]
            if p.get("ida_ea") is None or not p.get("ida_len"):
                continue
            if not (w0 <= link_seg < w0 + max(1, span)):
                continue
            base = p["ida_ea"] + (link_seg - w0) * 16
            if base < p["ida_ea"] or base + max(ips) >= p["ida_ea"] + p["ida_len"]:
                continue
            hits = sum(1 for i in ips if entry_before(base + i))
            cands.append({"idx": idx, "seg_name": p["seg_name"], "base": base,
                          "hits": hits, "total": len(ips),
                          "read_evidence": idx in read_ev.get(cs, set())})
        chosen = None
        if cands:
            # content first (finding 59's doctrine), loader read-evidence as
            # tie-break, and never pick on zero signal from both
            cands.sort(key=lambda c: (-c["hits"], -int(c["read_evidence"]),
                                      c["idx"]))
            best = cands[0]
            if best["hits"] > 0:
                chosen = best
            elif best["read_evidence"] and not (
                    len(cands) > 1 and cands[1]["read_evidence"]):
                chosen = best
        if chosen:
            resolved_events += ev
            rows.append((cs, ev, "overlay:" + chosen["seg_name"], len(ips),
                         "base=0x%X hits=%d/%d%s" % (
                             chosen["base"], chosen["hits"], chosen["total"],
                             " read" if chosen["read_evidence"] else "")))
        else:
            rows.append((cs, ev, "UNRESOLVED", len(ips),
                         "candidates=%d" % len(cands)))
        out[str(cs)] = {"link_seg": link_seg, "events": ev, "ips": ips,
                        "candidates": cands,
                        "chosen": (chosen["idx"], chosen["base"]) if chosen else None}

    print("== runtime CS -> IDA map (finding 60 P1) ==")
    print("   indirect_far events        : %d" % tot_events)
    print("   resident (unchanged rule)  : %d" % resident_events)
    print("   overlay resolved by formula: %d" % resolved_events)
    print("   %-8s %-8s %-22s %-5s %s" % ("cs", "events", "verdict", "ips", "detail"))
    for cs, ev, verdict, nips, det in sorted(rows, key=lambda r: -r[1]):
        if verdict == "resident":
            continue
        print("   0x%-6X %-8d %-22s %-5d %s"
              % (cs, ev, verdict, nips, det or ""))
    unres = sum(ev for _c, ev, v, _i, _d in rows if v == "UNRESOLVED")
    print("   UNRESOLVED events          : %d" % unres)

    OUT.write_text(json.dumps({
        "image_para": IMAGE_PARA, "total_events": tot_events,
        "resident_events": resident_events,
        "overlay_resolved_events": resolved_events,
        "unresolved_events": unres, "map": out}, indent=1))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
