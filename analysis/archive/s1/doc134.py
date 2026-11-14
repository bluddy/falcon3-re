P = r"C:\Users\ybarnoy\projects\falcon3"
FIND = """
## 2026-11-10 134 - function-removal path; three word-table "functions" deleted (S1c-4i)

`verify_rebuild` had no way to accept a deleted function (a missing key is LOST), which blocked every fl_F fragment that is
data.  The orphan manifest gained `remove_funcs` and the apply tool a `REMOVE` mode:

- `REMOVE = [(ea, fn_end, data_end)]`: `rm_state` / `remove`.  Refuses if a jump or call from outside the span reaches a
  code head that is cleared; then `del_func`, drop the name, `del_items [ea, data_end)`, and `create_word` over the
  range.  The manifest pins `fn_sha256` (the function's bytes), `data_sha256` (the whole table head), name and far flag.
- `verify_rebuild`: a key missing from `now` is accepted only when the committed entry matches the manifest on (ea, size,
  name, bytes sha256) and no live function starts inside the table.  New REMOVE category; the register check drops the
  removed function from the expected set (its range still tiles through the other functions and holes).

Applied to the three clear word-table heads (each is the first 2-3 B of a table that a misdecode made into a function; the
bytes after it were already data, and the `fl_F` flow was the decoder running into the next table row):

- **0x6EC14..0x6EC2C** (`data_fragment_6ec14`, 3 B): `1B 00 41 00 45 00 50 00 51 00 52 00 06 03 ...`, the key/handler table
  that precedes r17_router_event_loop (0x6EC2C).
- **0x6EF1C..0x6EF30** (`r17_entry_partial`, 3 B): `1B 00 44 00 4B 00 4D 00 52 00 E5 05 56 05 E5 05 E5 05 98 05`, the same
  kind of table in front of r17_ui_event_loop (0x6EF30, finding 132).
- **0x2E1C2..0x2E20A** (unnamed, 38 B): a byte-pair table; sprite_clip_bounds_check starts at 0x2E20A.

The ledger entries were removed too: naming.yaml `sub_6EF1C`, `sub_6EC14`, and the routines.yaml entries for ea 454428 /
453652 (2038 -> 2036 ledger entries).

**Applied.**  Plan, dry replay (3 fresh, 32 applied), backup `FALCONCD.EXE.i64.bak_rm134`, apply: functions 3,560 -> 3,557.
Gates: integrity INTACT, `naming.py check` OK (2036), `verify_rebuild` faithful (REMOVE 3, LOST 0, CHANGED 0), idempotent
replay (35 applied).

**Not removed, on purpose.**  sub_105DA7 (2 B, `01 D0`): it is the tail of the word table at 0x105D90.. , but it has three
code xrefs (`call cs:funcs_106A17[bx]` at 0x106A4C / 0x106A7E are indirect calls through a table whose 0x105D9D / 0x105DA7
entries resolved to it, and sub_105D9D before it is similar), so the whole 0x105D90..0x105EB5 region needs a table-versus-
code decision of its own.

**Still open:** 0x167449 (data fragment inside function 166F80, needs chunk restructuring), 0x22C8B, 0x67F77, sub_105DA7 and
sub_105D9D, and the no-xref runs.
"""
p = P + r"\docs\findings_log.md"
s = open(p, newline="", encoding="utf-8").read()
s = s.rstrip("\r\n") + "\r\n" + FIND.replace("\n", "\r\n")
open(p, "w", newline="", encoding="utf-8").write(s)


def edit(path, pairs):
    s = open(path, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    for a, b in pairs:
        assert s.count(a) == 1, (path, a[:50], s.count(a))
        s = s.replace(a, b)
    open(path, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)


edit(P + r"\status.md", [
    ("     - Left open (findings 126-133): 6 fl_F fragments + sub_105DA7 (data tables / function removal needs a gate path:\n"
     "       0x6EC17, 0x6EF1F, 0x2E1E8, 0x167449, 0x22C8B, 0x67F77, 0x105DA7), no-xref runs.",
     "     - **S1c-4i (finding 134):** a function-removal path (`remove_funcs` manifest, `REMOVE` apply mode, REMOVE category in\n"
     "       `verify_rebuild`); three word-table heads deleted (0x6EC14, 0x6EF1C, 0x2E1C2), ledger entries removed; functions\n"
     "       3,560 -> 3,557; backup `.bak_rm134`.\n"
     "     - Left open (findings 126-134): 0x167449 (inside 166F80), 0x22C8B, 0x67F77, the 0x105D90 table / sub_105DA7, no-xref runs."),
    ("     - commit S1c-4h;\n", "     - commit S1c-4i;\n"),
])
edit(P + r"\docs\workflow\idb_regeneration.md", [
    ("and three no-xref orphans (finding 133)",
     "and three no-xref orphans (finding 133) and three word-table heads removed as functions (finding 134)"),
])
print("ok")
