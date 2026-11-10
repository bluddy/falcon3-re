import io
ROOT = r"C:\Users\ybarnoy\projects\falcon3"


def rd(p):
    return io.open(ROOT + "\\" + p, "r", newline="", encoding="utf-8").read()


def wr(p, s):
    io.open(ROOT + "\\" + p, "w", newline="", encoding="utf-8").write(s)


def eol(s):
    return "\r\n" if "\r\n" in s else "\n"


def sub(s, old, new):
    assert s.count(old) == 1, old
    return s.replace(old, new)


p = "docs\\workflow\\idb_regeneration.md"
s = rd(p)
s = s.replace("3,549", "3,552")
s = sub(s, "and the two R20/R21 menu bodies (finding 127)",
        "the two R20/R21 menu bodies (finding 127) and the 0x12C5xx cluster (finding 128: two function ends extended, three added)")
wr(p, s)

p = "status.md"
s = rd(p)
e = eol(s)
old = "     - Left open (findings 126/127): 8 refused call targets, fl_F continuations, jmp-reached tails, no-xref runs." + e
new = e.join([
    "     - **S1c-4c (finding 128):** the 0x12C5xx cluster: sub_12C518 and sub_12C7C6 extended over their jcc/jmp",
    "       continuations, 0x12C683 / 0x12C951 / 0x12CCE9 added; functions 3,549 -> 3,552; backup `.bak_cluster`.",
    "       `verify_rebuild.py` gained an EXTEND category (exact appended-bytes sha256).",
    "     - Left open (findings 126-128): 6 refused call targets, fl_F continuations, remaining jmp-reached tails, no-xref runs.",
]) + e
s = sub(s, old, new)
wr(p, s)

p = "docs\\findings_log.md"
s = rd(p)
e = eol(s)
f = [
    "",
    "## 2026-11-10 128 - 0x12C5xx cluster: function ends extended over jmp-reached orphan code (S1c-4c)",
    "",
    "**Layout.** 0x12C4F0..0x12CEA0 interleaves existing functions with 6 orphan code runs.  Four of them are the",
    "bodies of existing functions that IDA cut at an unconditional jump or a `retn` in the middle of the routine:",
    "",
    "- sub_12C518 (26 B) ends at `jmp loc_12C661` but its `jl loc_12C532` falls into 0x12C532..0x12C66A (312 B, ends in",
    "  `retf`; 0x12C661 is the shared epilogue).  Extended to 0x12C66A (338 B).",
    "- sub_12C7C6 (96 B) branches out with `jnb`/`jz` at 0x12C800 / 0x12C80D (to 0x12C826) and `jmp loc_12C90B` at",
    "  0x12C823; 0x12C826..0x12C951 ends in `pop ds / retn` at 0x12C94F.  Extended to 0x12C951 (395 B).",
    "- 0x12C683..0x12C7C6 (323 B; called from 0x12C59F, ends `retn`), 0x12C951..0x12C970 (31 B, a BIOS-tick wait on",
    "  0040:006C called from 0x12C5B3 and three sites in 0x12C683) and 0x12CCE9..0x12CE9D (436 B, called from",
    "  0x12C683, ends `retn`) are real call targets and became functions.",
    "",
    "**Applied.** `tools/apply_orphan_funcs.py` now also has `EXTEND` (set_func_end; the manifest records",
    "`before_end`, `end` and the sha256 of the appended bytes, the post-check requires the extended function to keep",
    "its name and be a single chunk, and nothing else may change).  `tools/verify_rebuild.py` has a new EXTEND category:",
    "a changed function is accepted only when its old bytes are a prefix of the new ones and the appended bytes hash as",
    "the manifest says.  Functions 3,549 -> 3,552.  Integrity INTACT, `verify_rebuild` faithful (ADDED 3, EXTEND 2, no",
    "LOST/CHANGED), `naming.py check` OK.  Backup `FALCONCD.EXE.i64.bak_cluster`.",
    "",
    "**Not done on purpose.** 0x12C4F2..0x12C504 is the first half of a `creat` + `write` + `close` routine whose second half",
    "is the existing `fwrite` at 0x12C504 (entered by `jnb` from 0x12C500); it needs fwrite's start moved up, not a new",
    "function.  0x12C9D0..0x12C9DF is a far wrapper (`push bx / push bp ... call overlay_undecoded_body_12bd16 ... retf`)",
    "with no xref at all, left with the no-xref runs.  0x12CB27 (`push ds / pop ds / retn`, 3 B, no xref) is padding.",
    "",
]
if not s.endswith(e):
    s += e
s += e.join(f)
wr(p, s)
print("ok")
