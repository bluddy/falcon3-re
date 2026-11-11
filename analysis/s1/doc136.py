P = r"C:\Users\ybarnoy\projects\falcon3"


def edit(path, pairs, append=None):
    s = open(path, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    for a, b in pairs:
        assert s.count(a) == 1, (path, a[:50], s.count(a))
        s = s.replace(a, b)
    if append:
        s = s.rstrip("\n") + "\n\n" + append
    open(path, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)


F136 = """## 2026-11-10 136 - the modem/network message text typed as strings (S1c-4k)

Finding 135 cleared 0x105D90..0x105EB5 to data but left the text behind it (0x105EB5..0x10626E, still undefined bytes)
and did not set the offsets of the 43-word table.  Both are done now.

- **Layout** (parsed from the bytes, read-only probe): 0x105DE6..0x10626E is a sequence of NUL-terminated ASCII strings, each
  optionally preceded by a one-byte layout code (1..6, probably a column/row or colour selector), 114 items by that rule.
  All 43 table words (base 0x105D90) land on an item start except entry 40 (0x1061BB); the strict parse gives 118 items
  once the exception below is split, and 0x1061BB is then a start.  Entries 12-17, 30 and 37 all point at
  0x106260 ("SET UP ERROR").
- **0x10614A** is not text: `mov cs:byte_10614A, cl` at 0x1073F2 patches the digit of "PLAYER #2 HAS" at run time, so it
  stays a one-byte item and the strings around it are split there.
- The manifest gained a `text_fix` block (`TEXTFIX` / `xt_state` / `textfix`): `op_plain_offset` on every table word, then
  each text item re-typed as a C string or a single byte; sha256 of the table and the text pinned.  No function-table
  change, so `function_bytes.json` and `verify_rebuild` are untouched (all categories 0).

**Applied.**  Plan, dry replay (1 fresh, 36 applied), backup `FALCONCD.EXE.i64.bak_txt136`, apply.  Gates: integrity INTACT,
`naming.py check` OK (2036), `verify_rebuild` faithful (all categories 0), idempotent replay (37 applied).

**Still open:** 0x167449 (inside 166F80), 0x22C8B, 0x67F77, and the no-xref runs.
"""

edit(P + r"\docs\findings_log.md", [], append=F136)

edit(P + r"\status.md", [
    ("""     - Left open (findings 126-135): 0x105EB5..0x10626E message text, 0x167449 (inside 166F80), 0x22C8B, 0x67F77, no-xref runs.""",
     """     - **S1c-4k (finding 136):** the 0x105DE6..0x10626E message text typed as strings and the 43-word table made offsets
       (`text_fix` manifest block, `TEXTFIX`); no function-table change; backup `.bak_txt136`.
     - Left open (findings 126-136): 0x167449 (inside 166F80), 0x22C8B, 0x67F77, no-xref runs."""),
    ("     - commit S1c-4j;\n", "     - commit S1c-4k;\n"),
])

edit(P + r"\docs\workflow\idb_regeneration.md", [
    ("(finding 135)", "(finding 135) and the message text behind it typed as strings (finding 136)"),
])
print("ok")
