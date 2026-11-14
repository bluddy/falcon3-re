def edit(p, fn):
    s = open(p, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    s = fn(s)
    open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
    print("ok", p, crlf)


R = r"C:\Users\ybarnoy\projects\falcon3"
ENTRY = """
## 2026-11-11 144 - misdecoded pieces glued back onto two functions (S1c-4s)

**What was wrong.**  Two existing functions each had a stretch of their own body misdecoded, so IDA split it off:

- `sprite_clip_bounds_check` (0x2E20A): the `jz` at 0x2E22D jumps to 0x2E236, one byte into the `mov bl,9 / mov di,9 / jmp` that
  starts at 0x2E22F; IDA had decoded `or dh,[bp+di-40F8h]` from 0x2E235 and left 0x2E22F..0x2E23D outside the function.  The
  2-instruction pair `mov bx,cs:[di+3Ch] / mov cx,cs:[di+3Eh]` at 0x2E281..0x2E28F had the same problem (a stray `2E` prefix
  byte at 0x2E285 made the second `mov` start one byte late).  Both are real code: `mov bl,9 / mov di,9 / jmp loc_2E240`
  (the 0x2E22F path, plus the `mov bl,8 / mov di,8` entry at 0x2E236) and the cs-relative loads before `call loc_2E34A`.
- `sub_166F80`: finding 138 absorbed the 0x167440 fragment but left 0x16781A..0x167827 broken.  The bytes are `26 80 3e c2 19 00 74 05 9a f5 0f 9f 66`:
  `cmp es:word_7A276` ended at 0x16781A with the `es:` prefix and its operand decoded as `retn 19h` (`r38_retn19_stub`, a bogus
  4-byte "function" at 0x16781C, ledger key `r38_e149`) and a `call far` at 0x167822 that nothing reaches.  The real code is
  `cmp byte ptr es:[...], ...; jz loc_167827` and the `call far ptr loc_679E5` it skips.

**Fix.**  New manifest block `glue_funcs` and apply mode `GLUE` (`gl_state` / `glue`): optional bogus fragment functions are
deleted and unnamed, each run is cleared, redecoded by `descend` from its seeds and appended with `append_func_tail` (IDA merges it
with an adjacent chunk).  The apply refuses if a jump or call from outside enters a stale head.  Entries: 0x2E20A with runs
0x2E22F..0x2E23D (seeds 0x2E22F, 0x2E236) and 0x2E281..0x2E28F; 0x166F80 with run 0x16781A..0x167827 and fragment 0x16781C.
`verify_rebuild.py` folds `glue_funcs` into its EXTEND (the main chunk grows over the glued bytes, appended-bytes sha256 pinned) and
REMOVE (the fragment) allowlists.  The `ab_state` check was loosened to accept a later chunk merge (the absorbed range
must lie inside one chunk of the owner).

**Ledger.**  The fragment's entries are removed (naming.yaml `r38_e149`, routines.yaml ea 1472540): 2035 -> 2034 entries.

**Results.**  `function_bytes.json` 3,591 -> 3,590: `sub_2E20A` main chunk 37 -> 95 B, `sub_166F80` 2,202 -> 2,943 B (one chunk
166F80-167AFF now), `r38_e149` gone.

**Applied.**  Plan (2 fresh, 90 applied), dry replay, backup `FALCONCD.EXE.i64.bak_glue144`, apply.  Gates: integrity INTACT,
`naming.py check` OK (2034), `verify_rebuild` faithful (EXTEND 2, REMOVE 1, everything else 0), idempotent replay (92 applied).

**Still open:** 0x6E7C7 / 0x6E8BC (the 0x6E696..0x6E8B7 handler cluster with the R30 state machine), 0x6E16E (data with two far-call
xrefs), 0x67BA3 (R30 switch default `jmp`) and the 92 padding runs.
"""


def log(s):
    return s.rstrip("\n") + "\n" + ENTRY


def status(s):
    a = "     - Left open (findings 126-143): the 0x6E696..0x6E8B7 handler cluster (with the R30 menu state machine), two fragments of existing functions and the padding runs"
    assert s.count(a) == 1
    s = s.replace(a, """     - **S1c-4s (finding 144):** misdecoded pieces glued back onto `sub_2E20A` (two chunks) and `sub_166F80` (the bogus
       `r38_retn19_stub` fragment removed; new `GLUE` mode); functions 3,591 -> 3,590; ledger 2035 -> 2034; backup `.bak_glue144`.
     - Left open (findings 126-144): the 0x6E696..0x6E8B7 handler cluster (with the R30 menu state machine), 0x6E16E, 0x67BA3 and the padding runs""")
    b = "     - commit S1c-4r;\n"
    assert s.count(b) == 1
    return s.replace(b, "     - commit S1c-4s;\n")


def rb(s):
    a = "and 13 table-data runs remade as data (finding 143)"
    assert s.count(a) == 1
    return s.replace(a, a + " and two functions repaired by gluing misdecoded chunks (finding 144)")


edit(R + r"\docs\findings_log.md", log)
edit(R + r"\status.md", status)
edit(R + r"\docs\workflow\idb_regeneration.md", rb)
