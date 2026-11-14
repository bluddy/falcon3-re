def edit(p, fn):
    s = open(p, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    s = fn(s)
    open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
    print("ok", p, crlf)


R = r"C:\Users\ybarnoy\projects\falcon3"
ENTRY = """
## 2026-11-11 143 - thirteen orphan "code" runs that are table data remade as data (S1c-4r)

**Inventory.**  A re-scan of the unowned code heads after finding 142 gives 112 runs (368 B); 92 are 1-2 B padding.  Of the 20
runs of 3 B or more, 13 are not code at all but the tails of word tables, jump tables or record bytes that IDA decoded as
instructions.  Each one sits in a data stretch (neighbours are `dw offset ...`, `db 0` or other table words) and has no
code xref; the data xrefs on its heads are fl_F fall-throughs from the bogus decoding itself:

- Jump / dispatch tables (words): 0x1982F..0x19843 (20 B; 10 words after `sub_197EA`, the `cs:[bx+0Ah]` switch keys), 0x1277CC..0x1277DA
  (14 B; the default-case table behind `sub_1274CF`), 0x1B4E0..0x1B4E8 (8 B; four `0x0D8A` entries of a jump table whose head is already
  `dw offset`), 0x2E190..0x2E194 (4 B), 0x5CDFA..0x5CDFD (3 B, one word and an odd byte) and 0x6EA3A..0x6EA4A (16 B, eight words
  `FFFF 0043 0046 004F 00F4 00E4 00DC 00EC` between `r17_event_main_loop` and `r17_menu_event_loop`).
- Record bytes: 0x1F75F..0x1F769 (`b2 6b 6a 69 68 67 6d 67 b3 b3`, bytes), 0x5CDA8..0x5CDB2 (`aa aa aa aa aa f2 45 44 44 4d`),
  and the repeated record `64 00 00 01 00 00 84 40 00 00 ff ff 00` in the zero-filled area at 0x5D1E6, 0x5D2E5, 0x5D5AB, 0x5D91B and 0x5DA68.

**Fix.**  New manifest block `data_fix` and apply mode `DATAFIX` (`df_state` / `datafix`): `[lo, hi)` is cleared and re-made as words
(an odd last byte stays a byte) or bytes.  It refuses if a call or jump from outside the range enters it, or if a function owns any of the bytes.  The runs
are pinned by sha256.  `function_bytes.json` is unchanged (the runs were not in any function).

**Applied.**  Plan (13 fresh, 77 applied), dry replay, backup `FALCONCD.EXE.i64.bak_dat144`, apply.  Gates: integrity INTACT,
`naming.py check` OK (2035), `verify_rebuild` faithful (everything 0), idempotent replay (90 applied).

**Still open:** 0x167822 and 0x2E235 / 0x2E286 (orphan fragments of two existing functions, next finding), 0x6E7C7 / 0x6E8BC (the 0x6E696
handler cluster), 0x6E16E (data with two far-call xrefs), 0x67BA3 (R30 switch default `jmp`) and the padding runs.
"""


def log(s):
    return s.rstrip("\n") + "\n" + ENTRY


def status(s):
    a = "     - Left open (findings 126-142): the 0x6E696..0x6E8B7 handler cluster (with the R30 menu state machine), a few runs of 5-20 bytes and the padding runs"
    assert s.count(a) == 1
    s = s.replace(a, """     - **S1c-4r (finding 143):** 13 orphan "code" runs that are word-table or record data remade as data (new `DATAFIX` mode);
       no function change; backup `.bak_dat144`.
     - Left open (findings 126-143): the 0x6E696..0x6E8B7 handler cluster (with the R30 menu state machine), two fragments of existing functions and the padding runs""")
    b = "     - commit S1c-4q;\n"
    b = "     - commit S1c-4q;\n".replace("\n", "\n")
    assert s.count(b) == 1
    return s.replace(b, "     - commit S1c-4r;\n")


def rb(s):
    a = "and four dispatcher functions behind word tables added (finding 142)"
    assert s.count(a) == 1
    return s.replace(a, a + " and 13 table-data runs remade as data (finding 143)")


edit(R + r"\docs\findings_log.md", log)
edit(R + r"\status.md", status)
edit(R + r"\docs\workflow\idb_regeneration.md", rb)
