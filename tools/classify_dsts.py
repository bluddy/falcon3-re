"""Finding 58 (host, read-only): classify every unresolved call/jump
destination into

  (a) frameless ASM / a plausible unregistered 16-bit function
  (b) indirect pointer variable or register-indirect operand (IDA emitted the
      xref to a pointer word, not to code)
  (c) true anomaly / truncated tail / data

Inputs : analysis/ida_falconcd/dst_list.json (counts, srcs)
         analysis/ida_falconcd/dst_audit.json (IDA decode, flags, operands)
         git HEAD callgraph_refs.json (to flag which dsts finding 57 moved)

Usage: venv\\Scripts\\python tools/classify_dsts.py
"""
import json
import struct
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

IDA = Path("analysis/ida_falconcd")
O_REG, O_MEM, O_PHRASE, O_DISPL, O_IMM, O_FAR, O_NEAR = 1, 2, 3, 4, 5, 6, 7

lst = {r["ea"]: r for r in json.loads((IDA / "dst_list.json").read_text())}
aud = {r["ea"]: r for r in json.loads((IDA / "dst_audit.json").read_text())["targets"]}

# which sources did finding 57 retarget?  The baseline MUST be the commit
# before finding 57 (finding 57 committed the post-patch refs, so HEAD now
# equals the current state and would diff to zero).
BASELINE = "85b4fff"
r = subprocess.run(["git", "show",
                    BASELINE + ":analysis/ida_falconcd/callgraph_refs.json"],
                   capture_output=True, text=True)
hd = defaultdict(set)
for s, d, c in json.loads(r.stdout)["refs"]:
    hd[(s, c)].add(d)
cur = defaultdict(set)
for s, d, c in json.loads((IDA / "callgraph_refs.json").read_text())["refs"]:
    cur[(s, c)].add(d)
moved_srcs = {k for k in cur.keys() & hd.keys() if cur[k] != hd[k]}


def moved(ea):
    row = lst[ea]
    # srcs were recorded without the call/jmp bit, so re-derive loosely:
    # a dst counts as moved if ANY src key of a ref to it moved
    return any(any(s == k[0] for k in moved_srcs) for s in row["srcs"])


def printable(b):
    run = best = 0
    for x in b:
        if 0x20 <= x < 0x7F or x in (0x00,):
            run = run + 1 if x != 0 else run
            best = max(best, run)
        else:
            run = 0
    return best


rows = []
for ea, a in aud.items():
    row = lst[ea]
    dec = a["decode"]
    srcs = a["srcs"]
    op_types = {s["op_type"] for s in srcs}
    mnems = {s["mnem"] for s in srcs}
    direct = any(t in (O_FAR, O_NEAR) for t in op_types)
    ptr_var = any(t == O_MEM for t in op_types)      # call/jmp dword_XXXX (FF 1E/2E)
    reg_ind = any(t in (O_PHRASE, O_DISPL) for t in op_types)  # [reg+...] form
    b16 = bytes.fromhex(a["bytes16"] or "")
    dataish = printable(b16) >= 6

    if ptr_var or reg_ind:
        cls = "b_ptr_or_indirect"
    elif dec["ok"] and dec["term"] in ("retf", "retn", "ret", "iret", "jmp"):
        cls = "a_frameless_fn" if direct else "b_ptr_or_indirect"
    elif dec["ok"] and dec["term"]:
        cls = "c_anomaly"
    else:
        cls = "c_anomaly"

    rows.append({
        "ea": ea, "n": row["n"], "zone": row["zone"], "seg": a["seg"],
        "cls": cls, "direct": direct, "ptr_var": ptr_var, "moved": moved(ea),
        "first": dec["mnems"][0] if dec["mnems"] else "",
        "n_insns": len(dec["mnems"]), "bytes": dec["bytes"],
        "term": dec["term"] or "", "why": dec["why"],
        "prev": a.get("prev_mnem", ""), "prev_term": a.get("prev_is_term", False),
        "is_code": a["is_code"], "is_data": a["is_data"], "name": a.get("name", ""),
        "bytes16": a["bytes16"],
        "src_types": sorted(op_types), "src_mnems": sorted(mnems),
        "src_ops": ["%s|t%d" % (s["op0"], s["op_type"]) for s in srcs],
        "prev_end_eq": bool(a.get("prev_fn") and a["prev_fn"][2] == ea),
        "dataish": dataish, "prev_fn": a.get("prev_fn"), "next_fn": a.get("next_fn"),
    })

rows.sort(key=lambda r: (-r["n"], r["ea"]))
n = len(rows)
tot_refs = sum(r["n"] for r in rows)
print("== classification of %d unresolved destinations (%d refs) ==" % (n, tot_refs))
for cls, cnt in Counter(r["cls"] for r in rows).most_common():
    refs = sum(r["n"] for r in rows if r["cls"] == cls)
    print("   %-22s %3d dsts  %4d refs   (%.0f%% of refs)"
          % (cls, cnt, refs, 100.0 * refs / tot_refs))
mv = [r for r in rows if r["moved"]]
print("\n   of which finding 57 retargeted here (the '233' subset): %d dsts / %d refs"
      % (len(mv), sum(r["n"] for r in mv)))
for cls, cnt in Counter(r["cls"] for r in mv).most_common():
    print("      %-22s %3d" % (cls, cnt))

print("\n== class (a): prologue shapes (first canonical mnemonic) ==")
for m, c in Counter(r["first"] for r in rows if r["cls"] == "a_frameless_fn").most_common(14):
    print("   %-10s %3d" % (m, c))
a_rows = [r for r in rows if r["cls"] == "a_frameless_fn"]
print("   terminators :", dict(Counter(r["term"] for r in a_rows)))
print("   preceded by a terminator (strong entry signal): %d / %d"
      % (sum(1 for r in a_rows if r["prev_term"]), len(a_rows)))
print("   already an IDA code item: %d   has an IDA name: %d"
      % (sum(1 for r in a_rows if r["is_code"]), sum(1 for r in a_rows if r["name"])))
# would finding 55/56's prologue filters have taken these?
pro = 0
for r in a_rows:
    b = bytes.fromhex(r["bytes16"] or "")
    if b[:3] in (b"\x55\x8b\xec",) or b[:2] == b"\xc8" or b[:1] == b"\xc8":
        pro += 1
print("   start with `55 8B EC`/`C8` (the strict C-prologue): %d -> the rest were"
      " rejected as 'no prologue'" % pro)

# entry confidence: a real function entry is preceded by a terminator (or sits
# exactly at the previous function's end); a jmp-ending target is a trampoline
# / tail rather than a completed body
PRO = ("push", "pusha", "enter", "pop", "mov", "sub", "call", "xor", "cmp", "test")
strong = [r for r in a_rows if r["prev_term"] or r["prev_end_eq"]]
weak = [r for r in a_rows if not (r["prev_term"] or r["prev_end_eq"])]
pro_like = [r for r in weak if r["first"] in PRO]
print("   entry confidence:")
print("      strong (prev insn is a terminator, or prev fn ends here): %d" % len(strong))
print("      mid-body-looking start (no terminator before, but push/mov/sub/call...): %d"
      % len(pro_like))
print("      weak (starts on arithmetic / no entry signal): %d" % (len(weak) - len(pro_like)))
print("   ends in a tail `jmp` (trampoline / continuation): %d   in ret-like: %d"
      % (sum(1 for r in a_rows if r["term"] == "jmp"),
         sum(1 for r in a_rows if r["term"] in ("retf", "retn", "ret", "iret"))))
print("   IDA name prefixes:", dict(Counter((r["name"].split("_")[0] if r["name"] else "<none>")
                                            for r in a_rows).most_common(6)))
print("   IDA still flags it as DATA: %d" % sum(1 for r in a_rows if r["is_data"]))

print("\n== class (b): indirect (indexed) jump/call TABLE targets ==")
print("   (src operand text | IDA operand type: 2=o_mem direct memory, 3=o_phrase, 4=o_displ)")
print("   NOTE: none of these is a pointer VARIABLE -- each src is `jmp/call cs:off_X[bx]`")
print("   and IDA emits a code ref per table entry, so the dst is a dispatch case target.")
b_rows = [r for r in rows if r["cls"] == "b_ptr_or_indirect"]
print("   decode reaches a terminator: %d/%d   preceded by a terminator: %d/%d"
      % (sum(1 for r in b_rows if r["term"]), len(b_rows),
         sum(1 for r in b_rows if r["prev_term"]), len(b_rows)))
for r in b_rows[:6]:
    print("   0x%-7X n=%-3d %-6s ops=%-34s first=%-6s term=%-5s %s"
          % (r["ea"], r["n"], ",".join(r["src_mnems"]), ";".join(r["src_ops"])[:34],
             r["first"], r["term"] or "-", r["name"] or "-"))

print("\n== class (c): anomalies ==")
c_rows = [r for r in rows if r["cls"] == "c_anomaly"]


def why(r):
    w = r["why"]
    if w == "limit":
        return "code >512B, no terminator in window"
    if w.startswith("gap"):
        return "no IDA segment there"
    if w.startswith("undecodable"):
        return "first byte does not decode"
    return w or "?"


for k, c in Counter(why(r) for r in c_rows).most_common():
    grp = [r for r in c_rows if why(r) == k]
    print("   %-40s %3d dsts / %3d refs   (printable-looking bytes: %d, IDA data item: %d)"
          % (k, c, sum(r["n"] for r in grp),
             sum(1 for r in grp if r["dataish"]),
             sum(1 for r in grp if r["is_data"])))
print("   top anomaly addresses:")
for r in c_rows[:12]:
    print("      0x%-7X n=%-3d %-14s %-38s first=%-6s %s"
          % (r["ea"], r["n"], r["zone"][:14], why(r)[:38], r["first"] or "-",
             ("name=" + r["name"]) if r["name"] else ""))

print("\n== zone / range distribution ==")
for z, c in Counter(r["zone"].split(":")[0] for r in rows).most_common():
    print("   %-10s %d" % (z, c))
upper = [r for r in rows if 0x3ACAC <= r["ea"] < 0x669F0]
print("   in R05 upper half 0x3ACAC..0x669F0: %d dsts / %d refs"
      % (len(upper), sum(r["n"] for r in upper)))
print("   ...of which class (a): %d   (b): %d   (c): %d"
      % (sum(1 for r in upper if r["cls"] == "a_frameless_fn"),
         sum(1 for r in upper if r["cls"] == "b_ptr_or_indirect"),
         sum(1 for r in upper if r["cls"] == "c_anomaly")))

print("\n== TOP 20 by refs ==")
print("   %-8s %-4s %-10s %-8s %-7s %-6s %-14s %s"
      % ("ea", "n", "class", "first", "term", "prev-t", "src", "zone"))
for r in rows[:20]:
    print("   0x%-6X %-4d %-10s %-8s %-7s %-6s %-14s %s"
          % (r["ea"], r["n"], r["cls"][2:12], r["first"], r["term"],
             "TERM" if r["prev_term"] else "-", ",".join(r["src_mnems"])[:14],
             r["zone"][:18]))

json.dump(rows, open(IDA / "dst_classified.json", "w"))
print("\nwrote analysis/ida_falconcd/dst_classified.json")
