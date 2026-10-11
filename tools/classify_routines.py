#!/usr/bin/env python3
"""Classify all IDA functions: C-compiled vs hand-ASM vs data/unknown.

Inputs:
  analysis/ida_falconcd/function_bytes.json  (per-function bytes, IDA ground truth)
  analysis/ida_falconcd/survey.json          (flags: is_far, is_thunk)

Output:
  analysis/ida_falconcd/classification.json  {name: {class, confidence, reason}}
  summary printed to stdout

Classes:
  C          - C-compiled (ENTER prologue, or frame + LEAVE epilogue)
  ASM        - hand-written (manual frame with non-LEAVE epilogue, or no frame + INT/segment-override soup)
  LEAF       - leaf, no frame (too small to classify; could be C or ASM) -> candidates for portcheck
  THUNK      - overlay thunk stub
  DATA       - no return, no frame: likely data/continuation
  UNKNOWN    - nothing decisive
"""
import json
import os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FB_PATH = os.path.join(ROOT, "analysis", "ida_falconcd", "function_bytes.json")
SURVEY_PATH = os.path.join(ROOT, "analysis", "ida_falconcd", "survey.json")
OUT_PATH = os.path.join(ROOT, "analysis", "ida_falconcd", "classification.json")

INT_OPCODES = {"cd"}  # INT imm8


def classify(name, info, survey_flags):
    b = info.get("bytes")
    if not b:
        return "DATA", "low", "no bytes in IDB"
    if survey_flags.get("is_thunk"):
        return "THUNK", "high", "IDA thunk flag"

    size = info["size"]
    has_ret = b.endswith("cb") or b.endswith("c3")
    has_enter = b.startswith("c8")
    has_frame = b.startswith("558bec")
    has_leave = "c9cb" in b or "c9c3" in b or b[-4:-2] == "c9"

    if has_enter:
        return "C", "high", "ENTER prologue (MSC 5.1 C signature)"
    if has_frame:
        if has_leave:
            return "C", "high", "push bp;mov bp,sp ... LEAVE epilogue"
        return "ASM", "medium", "manual frame, no LEAVE (variable register saves)"

    # Frameless families (dissected 2026-10-11, findings log 14)
    if has_ret and size <= 16:
        if b.startswith("b8"):
            return "LEAF", "high", "ret const -> C-portable (findings 08)"
        if b.startswith("e80100") and size == 4:
            return "NEARTHUNK", "high", "far stub: call next-near-func; retf (structural, not C)"
        if b.startswith("2eff1e"):
            return "ASM", "high", "lcall cs:[table]; retf (indirect far dispatch stub)"
        if b[:4] in ("2ea0", "2ea1", "2ea2", "2ea3", "2e88", "2e89"):
            return "ASM", "high", "CS-relative data access (near data in code segment)"
        if b.startswith("31c0") or b.startswith("33c0"):
            return "LEAF", "high", "ret 0 -> C-portable"
        return "LEAF", "low", "frameless leaf, family unclassified"
    if has_ret:
        return "ASM", "low", "frameless, ret present, size %d" % size
    # no return anywhere
    if size <= 8:
        return "DATA", "low", "no ret, tiny - data/continuation?"
    return "DATA", "low", "no ret in %d bytes" % size


def main():
    fb = json.load(open(FB_PATH))
    # survey flags are stale for rebuilt overlay funcs -> prefer function_bytes
    try:
        survey = json.load(open(SURVEY_PATH))
        flags = {f["name"]: {"is_far": f.get("is_far"), "is_thunk": f.get("is_thunk")}
                 for f in survey["functions"]}
    except Exception:
        flags = {}
    for name, info in fb.items():
        flags.setdefault(name, {})
        flags[name]["is_far"] = info.get("is_far", flags[name].get("is_far"))
        if "is_thunk" not in flags[name]:
            flags[name]["is_thunk"] = False

    out = {}
    counts = Counter()
    for name, info in sorted(fb.items()):
        cls, conf, reason = classify(name, info, flags.get(name, {}))
        out[name] = {
            "ea": info["ea"],
            "size": info["size"],
            "far": info.get("is_far"),
            "overlay": info.get("overlay", info["ea"] >= 0x2CF60),
            "class": cls,
            "confidence": conf,
            "reason": reason,
        }
        counts[cls] += 1

    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=1)

    total = sum(counts.values())
    print(f"Classified {total} functions -> {OUT_PATH}")
    for cls, n in counts.most_common():
        print(f"  {cls:8s} {n:4d}  ({100*n//total}%)")

    # Top portcheck candidates: LEAF, far, size 4..10 (family detail matters)
    fams = {}
    for k, v in out.items():
        if v["class"] in ("LEAF", "NEARTHUNK"):
            fams.setdefault(v["reason"], []).append(k)
    print("\nFrameless families:")
    for fam, names in sorted(fams.items(), key=lambda x: -len(x[1])):
        print("  %3d  %s" % (len(names), fam))

    cands = [(v["size"], k) for k, v in out.items()
             if v["class"] == "LEAF" and v["far"] and 4 <= v["size"] <= 10
             and v["confidence"] == "high"]
    cands.sort()
    print("\nC-portable LEAF candidates: %d" % len(cands))
    for s, k in cands[:40]:
        print("  %-12s %s  ea=%s" % (k, fb[k]["bytes"], hex(fb[k]["ea"])))

    # C class sorted by size: the real decompile+port work queue
    cfs = sorted((v["size"], k) for k, v in out.items() if v["class"] == "C")
    print("\nC-compiled (ENTER) smallest 15 for first real port targets:")
    for s, k in cfs[:15]:
        print("  %-12s %4dB ea=%s %s" % (k, s, hex(fb[k]["ea"]), fb[k]["bytes"][:60]))


if __name__ == "__main__":
    main()
