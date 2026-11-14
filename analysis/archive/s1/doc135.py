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


F135 = """## 2026-11-10 135 - the 0x105D90 offset table and message text were code; two fake functions deleted (S1c-4j)

Finding 134 left sub_105DA7 (2 B) and sub_105D9D (10 B) alone because their xrefs looked like a function-pointer table.
Decoding the tables settled it: they are not functions.  This **supersedes the "Not removed, on purpose" paragraph of
finding 134.**

- **0x105D90..0x105DE6** is a 43-word table of offsets (relative to 0x105D90) into the text behind it, and
  **0x105DE6..0x105EB5** is that text (the in-game modem / network messages: WAITING TO SYNCHRONIZE, DISCONNECTING,
  SET UP ERROR ...).  Both had been decoded as code, which produced the two bogus functions.
- **The wrong xrefs came from 0x1069B4.**  The IDB had a 12-byte item `dw offset sub_106961` there and `dw offset sub_105DA7+1`
  / `dw offset sub_105D9D` at 0x1069C0 / 0x1069C2.  Only the five words at 0x1069B4..0x1069BC are function offsets (base
  0x105D90, indexed by `call cs:funcs_106A17[bx]`): sub_106961, sub_106B27, sub_106664, sub_1066D0, sub_106976.  The five words
  at 0x1069BE..0x1069C6 (`17 00 18 00 0D 00 0B 00 17 00`) are plain constants (the `mov cx, cs:[bx+0C2Eh]` deltas).

The manifest gained a `table_fix` block and the apply tool a `TABLEFIX` mode: `tf_state` / `tablefix` delete the listed
functions and drop their names, rebuild the five offset words (`op_plain_offset` to base 0x105D90) and the five plain words,
clear `[0x105D90, 0x105EB5)` and remake 0x105D90..0x105DE6 as words and the rest as bytes, then refuse to finish while any
code or data xref from outside still points into the cleared range.  sha256 of the cleared range and of both tables is
pinned in the manifest; `verify_rebuild` takes the deleted functions as REMOVE entries.

**Applied.**  Plan, dry replay (1 fresh, 35 applied), backup `FALCONCD.EXE.i64.bak_tab135`, apply: functions 3,557 -> 3,555.
Gates: integrity INTACT, `naming.py check` OK (2036; neither function had a ledger entry), `verify_rebuild` faithful
(REMOVE 2, LOST 0, CHANGED 0), idempotent replay (36 applied).  Only 0x105D90..0x105EB5 was cleared; the text may continue
to 0x10626E and is not yet retyped as strings.

**Still open:** the rest of the text up to the function at 0x10626E, 0x167449 (inside 166F80), 0x22C8B, 0x67F77, and the
no-xref runs.
"""

edit(P + r"\docs\findings_log.md", [], append=F135)

edit(P + r"\status.md", [
    ("""     - Left open (findings 126-134): 0x167449 (inside 166F80), 0x22C8B, 0x67F77, the 0x105D90 table / sub_105DA7, no-xref runs.""",
     """     - **S1c-4j (finding 135):** the 0x105D90 offset table and its message text were code; `table_fix` manifest block and
       `TABLEFIX` apply mode; sub_105D9D and sub_105DA7 deleted, the 0x1069B4 tables retyped; functions 3,557 -> 3,555;
       backup `.bak_tab135`.
     - Left open (findings 126-135): 0x105EB5..0x10626E message text, 0x167449 (inside 166F80), 0x22C8B, 0x67F77, no-xref runs."""),
    ("     - commit S1c-4i;\n", "     - commit S1c-4j;\n"),
])

edit(P + r"\docs\workflow\idb_regeneration.md", [
    ("and three word-table heads removed as functions (finding 134)",
     "and three word-table heads removed as functions (finding 134) and the 0x105D90 offset table / message text remade as data with two fake functions deleted (finding 135)"),
])
print("ok")
