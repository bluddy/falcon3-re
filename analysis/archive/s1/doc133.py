P = r"C:\Users\ybarnoy\projects\falcon3"
FIND = """
## 2026-11-10 133 - three no-xref orphans registered: fwrite entry, a far wrapper, a padding stub (S1c-4h)

Three code runs that no function owned and nothing references were registered as plain adds (no clear, no tails):

- **0x12C4F2..0x12C504 (18 B).**  The create-file half of the file helper pair: `push ds / mov ax,cs / mov ds,ax / mov dx,3Bh /
  mov ah,3Ch / xor cx,cx / int 21h / jnb fwrite / pop ds / retn`.  Its `jnb` targets 0x12C504 (`fwrite`: write 24h bytes,
  close), so the 18 B is the entry that precedes it and the tail chunk of the open helper at 0x12C4CB is its mirror
  (`mov ax,3D00h` opens, `mov ah,3Fh` reads).  Added as its own function ending at the `retn`; 0x12C504 stays the separate
  function it was.  The earlier plan to move fwrite's start up was dropped: the entry has its own `retn`.
- **0x12C9D0..0x12C9DF (15 B).**  A far wrapper: `push bx / push bp / mov bp,sp / mov bx,[bp+8] / call
  overlay_undecoded_body_12bd16 / pop bp / pop bx / retf`.  No xref (reached through a dispatch table or a far pointer).
- **0x12CB27..0x12CB2A (3 B).**  `push ds / pop ds / retn`, a no-op stub between sub_12CAEF and sub_12CB2A.

All three are unnamed (`sub_12C4F2`, `sub_12C9D0`, `sub_12CB27`).  The 0x105DA9 run is NOT code: 0x105D90..0x105EB5
is a word offset table (`01 D0 04 D0 04 ...`) that sub_105DA7 (2 B, `add ax,dx`) happens to decode into, so it belongs with
the data-table fragments below and is left alone.

**Applied.**  Plan, dry replay (3 fresh, 29 applied), backup `FALCONCD.EXE.i64.bak_orph133`, apply: functions 3,557 -> 3,560.
Gates: integrity INTACT, `naming.py check` OK (2038), `verify_rebuild` faithful (ADDED 3, LOST 0, CHANGED 0), idempotent
replay (32 applied).

**Still open:** the six fl_F fragments of finding 132 plus sub_105DA7 / the 0x105DA9 table (all need a function-removal path
in `verify_rebuild`), and the no-xref runs (34 free, 110 adjacent).
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
    ("     - Left open (findings 126-132): 6 fl_F fragments (data tables / function removal needs a gate path: 0x6EC17,\n"
     "       0x6EF1F, 0x2E1E8, 0x167449, 0x22C8B, 0x67F77), 0x105DA9 junk run, 0x12C4F2 / 0x12C9D0, no-xref runs.",
     "     - **S1c-4h (finding 133):** 0x12C4F2 (create-file entry), 0x12C9D0 (far wrapper) and 0x12CB27 (3 B stub) added;\n"
     "       functions 3,557 -> 3,560; backup `.bak_orph133`. 0x105DA9 is a data table, not code.\n"
     "     - Left open (findings 126-133): 6 fl_F fragments + sub_105DA7 (data tables / function removal needs a gate path:\n"
     "       0x6EC17, 0x6EF1F, 0x2E1E8, 0x167449, 0x22C8B, 0x67F77, 0x105DA7), no-xref runs."),
    ("     - commit S1c-4g;\n", "     - commit S1c-4h;\n"),
])
edit(P + r"\docs\workflow\idb_regeneration.md", [
    ("and two more mid-instruction starts (finding 132: rebased with a narrow clear_hi)",
     "and two more mid-instruction starts (finding 132: rebased with a narrow clear_hi) and three no-xref orphans (finding 133)"),
])
print("ok")
