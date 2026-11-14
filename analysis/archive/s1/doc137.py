def edit(p, fn):
    s = open(p, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    s = fn(s)
    open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
    print("ok", p, crlf)


LOG = r"C:\Users\ybarnoy\projects\falcon3\docs\findings_log.md"
ST = r"C:\Users\ybarnoy\projects\falcon3\status.md"
RB = r"C:\Users\ybarnoy\projects\falcon3\docs\workflow\idb_regeneration.md"

ENTRY = """
## 2026-11-10 137 - fixed_vec3_read shortened: its tail was the constants of the accumulators (S1c-4l)

**What.**  `fixed_vec3_read` (0x22C62) was a 41-byte function ending at 0x22C8B.  Only its first 15 bytes are code
(`mov ax,cs:22C71 / mov bx,cs:22C73 / mov cx,cs:22C75 / retf`).  Behind it are the three state words 0x22C71/73/75 (shared
with `pit_channel0_latch_read` and `fixed_vec3_write`) and nine constant words 0x22C77..0x22C88 that
`fixed_vec3_accumulate_a` (0x22C91) and `_b` (0x22CD5) use as operands (`mul/div word ptr cs:loc_22C7C+1`, `+3`,
`loc_22C80+1`, `+3`, `loc_22C84+1`, `loc_22C87`).  IDA had decoded them as instructions (`in ax,1Ch / pop es / jnb /
add ... / jo`) and run the function over them; the last bytes 0x22C89..0x22C90 (`48 00 90 8b c1 ... cb`) were an
orphan (`0e e8 48 00 90 8b c1 cb`: `push cs / call near +48h / nop / mov ax,cx / retf`), and the ~150 far calls to
0x22C89 were all flagged as calls into the middle of another function.

**Real layout.**  0x22C71..0x22C88 is data: 12 words (3 state, 9 constants).  0x22C89..0x22C90 is a real 8-byte far entry
ending in `retf`, reached by the type-16 call xrefs, so it becomes its own function (`sub_22C89`, 8 B).

**Fix.**  New manifest block `trim_funcs` and apply mode `TRIM` (`trim_state` / `trim`): `set_func_end` moves the end
up to 0x22C71, `[0x22C71, 0x22C91)` is cleared, `[0x22C71, 0x22C89)` is remade as words, and the pre-existing `ADD` entry for
0x22C89 (with `ADD_CLEAR`) registers the 8-byte function.  `trim` refuses if any jump or call enters a trimmed code head from
outside the cleared range.  The manifest pins the name, the sha256 of the whole span and of the kept 15 bytes.

**verify_rebuild.**  New category `TRIM`: accepted only when the new bytes are a prefix of the old ones, the sizes are
`old_end - ea` and `end - ea`, and the kept bytes hash as recorded.  The one new function is a plain ADDED.

**Applied.**  Plan, dry replay (2 fresh, 37 applied), backup `FALCONCD.EXE.i64.bak_vec137`, apply.  `function_bytes.json`
3,555 -> 3,556 functions (`sub_22C62` 41 -> 15 B, `sub_22C89` added, 8 B).  Gates: integrity INTACT, `naming.py check` OK
(2036), `verify_rebuild` faithful (TRIM 1, ADDED 1, everything else 0), idempotent replay (39 applied).

**Still open:** 0x167449 (inside 166F80) and the no-xref runs.
"""


def log(s):
    return s.rstrip("\n") + "\n" + ENTRY


def status(s):
    a = "     - Left open (findings 126-136): 0x167449 (inside 166F80), 0x22C8B, no-xref runs, and the R30 menu"
    assert s.count(a) == 1
    s = s.replace(a, """     - **S1c-4l (finding 137):** `fixed_vec3_read` (0x22C62) cut from 41 B to its 15 real bytes, the constants behind it
       remade as words and the 8-byte far entry 0x22C89 registered (`trim_funcs` manifest block, `TRIM` apply mode,
       `TRIM` category in verify_rebuild); functions 3,555 -> 3,556; backup `.bak_vec137`.
     - Left open (findings 126-137): 0x167449 (inside 166F80), no-xref runs, and the R30 menu""")
    assert s.count("     - commit S1c-4k;\n") == 1
    return s.replace("     - commit S1c-4k;\n", "     - commit S1c-4l;\n")


def rb(s):
    a = "and the message text behind it typed as strings (finding 136)"
    assert s.count(a) == 1
    return s.replace(a, a + " and the constants behind fixed_vec3_read split off its tail (finding 137: a function trimmed, one added)")


edit(LOG, log)
edit(ST, status)
edit(RB, rb)
