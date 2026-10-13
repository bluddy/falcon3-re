"""Gap sweep: find resident-image regions not covered by any known function.

Technique proven by sub_19D65 (finding 26) and the keyboard-unit tail gaps
(finding 28): IDA's auto-analysis sometimes leaves code uncovered. A gap is
"code-like" if it disassembles linearly from a standard prologue
(enter N,0 / push bp) through to a retf/ret before running off the end.

Usage: venv\\Scripts\\python tools\\gap_sweep.py [--start 0x10000] [--end 0x2F000]
Output: analysis/ida_falconcd/gap_candidates.json
"""
import argparse
import json
import struct

FB = "analysis/ida_falconcd/function_bytes.json"
EXE = "game/FALCONCD.EXE"
HDR = 0x2C00  # header paragraphs x 16 (pipeline.md)
OUT = "analysis/ida_falconcd/gap_candidates.json"

PROLOGUES = bytes.fromhex("c8")   # enter (C-class, finding 22)
FRAME = bytes.fromhex("558bec")   # push bp; mov bp,sp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=lambda x: int(x, 0), default=0x10000)
    ap.add_argument("--end", type=lambda x: int(x, 0), default=0x2F000)
    ap.add_argument("--minsize", type=int, default=8)
    args = ap.parse_args()

    fb = json.load(open(FB))
    covered = []  # (start, end, name)
    for k, v in fb.items():
        covered.append((v["ea"], v["ea"] + v["size"], k))
    covered.sort()

    raw = open(EXE, "rb").read()

    # merge coverage
    merged = []
    for s, e, n in covered:
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])

    # gaps within requested window
    gaps = []
    cur = args.start
    for s, e in merged:
        if e <= cur:
            continue
        if s > cur:
            gaps.append((cur, min(s, args.end)))
        cur = max(cur, e)
        if cur >= args.end:
            break
    if cur < args.end:
        gaps.append((cur, args.end))

    from capstone import Cs, CS_ARCH_X86, CS_MODE_16
    md = Cs(CS_ARCH_X86, CS_MODE_16)
    md.detail = False

    results = []
    for gs, ge in gaps:
        if ge - gs < args.minsize:
            continue
        file_off = HDR + (gs - 0x10000)
        blob = raw[file_off:file_off + (ge - gs)]
        if len(blob) < args.minsize:
            continue
        # prologue check
        if not (blob.startswith(PROLOGUES) or blob.startswith(FRAME)
                or blob[:2] in (b"\x55\x8b", b"\xc8\x00") or blob[0] == 0x55):
            results.append({"start": gs, "end": ge, "size": ge - gs,
                            "kind": "gap-noprologue", "head": blob[:12].hex()})
            continue
        # linear disasm: does it reach a retf/ret cleanly?
        last = None
        ok = False
        n = 0
        for i in md.disasm(blob, gs):
            last = i
            n += 1
            if i.mnemonic in ("retf", "ret", "retn"):
                ok = True
                break
        results.append({"start": gs, "end": ge, "size": ge - gs,
                        "kind": "gap-code" if ok else "gap-unclear",
                        "ret_at": (last.address + last.size) if ok else None,
                        "prologue": blob[:3].hex(), "insns": n})

    json.dump(results, open(OUT, "w"), indent=1)
    code = [r for r in results if r["kind"] == "gap-code"]
    print("gaps >= %dB in 0x%X..0x%X: %d total, %d code-like"
          % (args.minsize, args.start, args.end, len(results), len(code)))
    for r in results:
        print("  0x%05X..0x%05X %4dB %-14s %s"
              % (r["start"], r["end"], r["size"], r["kind"],
                 r.get("head", r.get("prologue", ""))))
    print("written:", OUT)


if __name__ == "__main__":
    main()