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
## 2026-11-10 138 - r38_data_fragment absorbed into sub_166F80 (S1c-4m)

**What.**  `sub_166F80` (0x166F80, a jump-table dispatcher) had four chunks: 166F80-1673D0, 16740F-16743E, 167450-16781A,
167827-167AFF.  The first chunk ended mid-flow at 0x1673D0, which the second function `r38_data_fragment` (`r38_e131`,
0x167440) claimed as its own tail chunk (1673D0-16740F), and the real code between the chunks was undecoded:
`b8 94 78 8e c0 26 80 3e c2 19 00 74 05 9a f5 0f 9f 66` at 0x16743E, i.e. `mov ax,7894h / mov es,ax / cmp
es:byte_7A302,0 / jz loc_167450 / call far loc_679E5`.  It is the same test as at 0x1673D0 (the branch for the other
case).  IDA had decoded the first byte as `db 0B8h`, the next as `js` and the rest as `shl` / `sbb` garbage
(`r38_data_fragment`, 9 B, class DATA, "undecodable shl/sbb bytes" in the ledger).

**Fix.**  New manifest block `absorb_funcs` and apply mode `ABSORB` (`ab_state` / `absorb`): the fragment function is deleted
and unnamed, `[0x16743E, 0x167450)` is redecoded (5 instructions, ends exactly at 0x167450), the owner's tail chunks inside
`[0x1673D0, 0x16781A)` are dropped and the main chunk is extended to 0x16781A.  `sub_166F80` is now two chunks,
166F80-16781A and 167827-167AFF; its main-chunk size goes 1104 -> 2202 B.  The apply refuses if a jump or call enters
a stale head from outside the redecoded range.  Pinned in the manifest: the fragment's name, chunks and sha256, and the
sha256 of the bytes the owner gains.

**verify_rebuild.**  No new category: the owner's growth is checked as an EXTEND (old bytes a prefix of the new ones,
appended-bytes sha256) and the fragment's missing key as a REMOVE (exact ea, size, name, sha256).  Both manifests are
folded in from `absorb_funcs` by `load_extends` / `load_removes`.

**Ledger.**  The fragment's entries are removed (naming.yaml `r38_e131`, routines.yaml ea 1471552): 2036 -> 2035 entries.

**Applied.**  Plan, dry replay (1 fresh, 39 applied), backup `FALCONCD.EXE.i64.bak_abs138`, apply.  `function_bytes.json`
3,556 -> 3,555.  Gates: integrity INTACT, `naming.py check` OK (2035), `verify_rebuild` faithful (EXTEND 1, REMOVE 1,
everything else 0), idempotent replay (40 applied).

**Still open:** the 34 free and 110 adjacent no-xref runs, and the R30 menu state machine.
"""


def log(s):
    return s.rstrip("\n") + "\n" + ENTRY


def status(s):
    a = "     - Left open (findings 126-137): 0x167449 (inside 166F80), no-xref runs, and the R30 menu"
    assert s.count(a) == 1
    s = s.replace(a, """     - **S1c-4m (finding 138):** `r38_data_fragment` (0x167440) deleted and the undecoded code at 0x16743E redecoded;
       `sub_166F80` now runs 166F80-16781A (`absorb_funcs` manifest block, `ABSORB` apply mode); two ledger entries
       dropped (2035); functions 3,556 -> 3,555; backup `.bak_abs138`.
     - Left open (findings 126-138): no-xref runs and the R30 menu""")
    assert s.count("     - commit S1c-4l;\n") == 1
    return s.replace("     - commit S1c-4l;\n", "     - commit S1c-4m;\n")


def rb(s):
    a = "(finding 137: a function trimmed, one added)"
    assert s.count(a) == 1
    return s.replace(a, a + " and a fragment function absorbed into its owner (finding 138)")


edit(LOG, log)
edit(ST, status)
edit(RB, rb)
