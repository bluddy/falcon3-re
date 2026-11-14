import io
ROOT = r"C:\Users\ybarnoy\projects\falcon3"


def rd(p):
    return io.open(ROOT + "\\" + p, "r", newline="", encoding="utf-8").read()


def wr(p, s):
    io.open(ROOT + "\\" + p, "w", newline="", encoding="utf-8").write(s)


def eol(s):
    return "\r\n" if "\r\n" in s else "\n"


def sub(s, old, new, count=1):
    assert s.count(old) >= 1, old
    return s.replace(old, new, count)


# ---- runbook
p = "docs\\workflow\\idb_regeneration.md"
s = rd(p)
e = eol(s)
s = s.replace("3,541", "3,547")
step = e.join([
    "# 6g. S1c-4 call-reached orphan code registered as functions (finding 126)",
    "#     (manifest registry/orphan_funcs_expected.json; OFMODE=plan on a COPY regenerates it, OFDRY=1 checks without saving)",
    "cmd /c \"tools\\run_idat.bat tools\\apply_orphan_funcs.py\"",
    "",
    "# 7. Verify IDB integrity",
])
s = sub(s, "# 7. Verify IDB integrity", step)
wr(p, s)

# ---- status
p = "status.md"
s = rd(p)
e = eol(s)
old = "   - **Now:** 524 mid-body targets / 1,409 sites, mostly R05/resident." + e
new = e.join([
    "   - **S1c-4 ✅ (finding 126): call-reached orphan code.**",
    "     - 6 code runs that are called but belonged to no function registered; functions 3,541 -> 3,547.",
    "     - No existing function changed; integrity INTACT; backup `.bak_orphan`. Manifest `registry/orphan_funcs_expected.json`.",
    "     - Left open (finding 126): 8 refused call targets, jmp-reached R20/R21 entries, fl_F continuations, no-xref runs.",
]) + e
s = sub(s, old, new + old)
s = sub(s, "     - commit S1c-3;" + e, "     - commit S1c-4;" + e)
wr(p, s)

# ---- findings
p = "docs\\findings_log.md"
s = rd(p)
e = eol(s)
f = [
    "",
    "### Finding 126 — S1c-4: call-reached orphan code registered as functions",
    "",
    "**Scan.** 182 runs of code heads (6,355 B) belong to no function. Classified by how they are entered: ",
    "call from code (tier 1), jmp from code, fl_F continuation of an adjacent function, no xref at all.",
    "",
    "**Applied (tier 1, safe subset).** `tools/apply_orphan_funcs.py` + `registry/orphan_funcs_expected.json` (plan on a copy,",
    "replay checks bytes by sha256, add_func with an explicit end, post-check that every pre-existing function is",
    "identical in start/end/name/chunks and that only the planned functions were added). Each run starts at a call",
    "target and ends in a ret/retf or an unconditional jmp:",
    "",
    "| range | callers | last insn |",
    "|---|---|---|",
    "| 0x1617C..0x162DF | 1 | retn |",
    "| 0x162DF..0x163AD | 3 | retn |",
    "| 0x16284E..0x162878 | 1 | retf |",
    "| 0x12C970..0x12C9D0 | 1 | retn |",
    "| 0x12CA0D..0x12CAEF | 1 | retn |",
    "| 0x12CAEF..0x12CB27 | 0 (adjacent) | retn |",
    "",
    "Functions 3,541 -> 3,547. Integrity INTACT, `verify_rebuild` faithful (ADDED 6, no LOST/SPLIT/CHANGED),",
    "`naming.py check` OK. Backup `FALCONCD.EXE.i64.bak_orphan`. 0x1617C and 0x162DF are near-duplicates with a",
    "self-modified `mov si,0ABCDh` / `mov bp,0ABCDh` (RTFIX); 0x1617C has an interior `loc_162CC+1` target.",
    "",
    "**Deliberately not registered.** 0x12BF89 is a jump table decoded as code (registering it would make the bare",
    "`retn` at 0x12BFA7 a function). `add_func(ea)` refused 10 call targets; with explicit ends 8 are workable but",
    "need review first (0x129F7, 0x6DFF0 a 1-byte popf with an RTFIX comment, 0x6E16E starts `add [si-66FBh],cl`,",
    "0x106EE2, 0x108430, 0x10931E, 0x109445, 0x10CE30).",
    "",
    "**Open.**",
    "- jmp-reached R20/R21 entries 0x10B380 / 0x10B720 (`enter 2,0 ... jmp`, entered from thunks 0x2C2A0 / 0x2C2E6) and their tails 0x10B4EB / 0x10B88B, 0x10B6A4 / 0x10BA40;",
    "- fl_F continuations: 0x10CC8E..0x10CE05 (375 B), 0x105DA9..0x105EB5 (268 B, likely misdecode), 0x215FE, 0x2D353 (int 21h quit), 0x6EC17, 0x6EF1F, 0x2E1E8, 0x167449, 0x22C8B, 0x25220, 0x67F77, 0x69720;",
    "- jmp-reached tails 0x12C532..0x12C66A, 0x3F6C7, 0x100DED, 0x4334E, 0x1093A6;",
    "- 34 free no-xref runs (0x12A2F 227 B, 0x100D0E 222 B, 0x100505 153 B ...) and 110 adjacent no-xref runs (likely padding or misdecode).",
    "",
]
if not s.endswith(e):
    s += e
s += e.join(f)
wr(p, s)
print("ok")
