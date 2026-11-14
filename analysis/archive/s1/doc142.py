def edit(p, fn):
    s = open(p, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    s = fn(s)
    open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
    print("ok", p, crlf)


R = r"C:\Users\ybarnoy\projects\falcon3"
ENTRY = """
## 2026-11-11 142 - four functions behind dispatch tables at 0x12BF96 and 0x155F18 registered (S1c-4q)

**0x12BF89 (88 B).**  The run is not one function.  The word table at 0x12BF7C..0x12BF96 (`off_12BF7C`, 13 offsets from
0x12B1F0, most of them the `retn` at 0x12BFA7) had its last bytes decoded as instructions, so IDA lost the 6-byte code stub
that follows it.  The words at 0x12BF88..0x12BF94 are table entries (all 0x0DB7 = `locret_12BFA7`, plus 0x1002 for
0x12C1F2); the real code starts at 0x12BF96: `add [bp+si+35Ch],cl` was in fact `06 00 8a 5c 03` = `push es / ... mov bl,[si+3]`
(`xor bh,bh / shl bx,1 / cmp bx,0Ch / ja / call cs:off_12BF2A[bx] / retn`), an 18-byte dispatcher that ends at the `retn`
0x12BFA7.  Behind it, 0x12BFA8..0x12BFE1 (57 B) is a second function (`mov ax,709Fh / mov es,ax / cmp es:word_709F0,0 / jz`,
three near calls, a block of `es:` stores, `retn`).  Both are orphan code with no xref in; the second is reached by the
`jz` fall-through of nothing, so it too is an entry nothing calls directly.  `sub_12BFE1` (the `lodsb` dispatcher that follows)
is unchanged.  Registered as `sub_12BF96` (18 B) and `sub_12BFA8` (57 B).  The table words 0x12BF88..0x12BF96 are made words
again by a new `ADD_WORDS` item (the clear covers 0x12BF88..0x12BF99, then 0x12BF88..0x12BF95 are re-created as words and the
code is redecoded from 0x12BF96).

**0x155F1A (50 B).**  `unk_155F18` is called from 0x155D10 (in `sub_155CE4`) and 0x155DC1 (in `sub_155D8A`) with `bx` = state
number.  The table of far pointers behind 0x155F00 left the last two bytes of table (`32 ff`, the end of a word) just before
the code; the real entry is 0x155F18 (`xor bh,bh` = `32 ff`, then `cmp bx,6 / jge / shl bx,1 / shl bx,1 / jmp dword ptr
cs:[bx+1240h]`, `retn`).  So the function starts two bytes earlier than the orphan run.  Registered as `sub_155F18`
(18 B, ends at the second `retn` 0x155F29), with ADD_CLEAR over 0x155F18..0x155F1A only.  The 34 bytes behind it
(0x155F2A..0x155F4C, `mov ah,cs:byte_155D83 / call sub_156013 / cmp ah,cs:byte_1553F6 / jnz nullsub_27 / ... inc cs:word_155EF9/B / retn`)
form a function of their own, `sub_155F2A`.  It ends in a `retn` at 0x155F4B, no call into it exists, and it is registered as
a plain ADD (the `FALL` set records that the end 0x155F4C is `nullsub_27`, not a terminator inside the run).

**Applied.**  Plan (3,587 -> 3,591, 4 functions, no other function changed), dry replay (4 fresh, 73 applied), backup
`FALCONCD.EXE.i64.bak_tbl142`, apply.  Gates: integrity INTACT, `naming.py check` OK (2035), `verify_rebuild` faithful (ADDED 4,
everything else 0), idempotent replay (77 applied).

**Still open:** 0x6E7C7 (the 0x6E696..0x6E8B7 handler cluster whose seven retf handlers sit under a misdecoded end of
`r69_pending_session_step`, with base-relative jump-table entries and variable addresses in the same range; it belongs with the
R30 menu state machine), 0x1982F, 0x1277CC, 0x6EA3B, 0x5DA68 and the padding runs.
"""


def log(s):
    return s.rstrip("\n") + "\n" + ENTRY


def status(s):
    a = "     - Left open (findings 126-141): the longer pieces 0x6E7C7, 0x12BF89 and 0x155F1A, the padding runs and the R30 menu state machine"
    assert s.count(a) == 1
    s = s.replace(a, """     - **S1c-4q (finding 142):** four functions behind dispatch tables registered: `sub_12BF96`, `sub_12BFA8`, `sub_155F18`,
       `sub_155F2A` (the table words are made words again first); functions 3,587 -> 3,591; backup `.bak_tbl142`.
     - Left open (findings 126-142): the 0x6E696..0x6E8B7 handler cluster (with the R30 menu state machine), a few runs of 5-20 bytes and the padding runs""")
    b = "     - commit S1c-4p;\n"
    assert s.count(b) == 1
    return s.replace(b, "     - commit S1c-4q;\n")


def rb(s):
    a = "and a two-chunk switch function added (finding 141)"
    assert s.count(a) == 1
    return s.replace(a, a + " and four dispatcher functions behind word tables added (finding 142)")


edit(R + r"\docs\findings_log.md", log)
edit(R + r"\status.md", status)
edit(R + r"\docs\workflow\idb_regeneration.md", rb)
