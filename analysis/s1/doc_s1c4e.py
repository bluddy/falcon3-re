import io
def edit(path, pairs, append=None):
    s = open(path, newline="", encoding="utf-8").read()
    for a, b in pairs:
        a = a.replace("\n", "\r\n"); b = b.replace("\n", "\r\n")
        assert s.count(a) == 1, (path, a[:60], s.count(a))
        s = s.replace(a, b)
    if append:
        s += append.replace("\n", "\r\n")
    open(path, "w", newline="", encoding="utf-8").write(s)

F130 = """
## 2026-11-10 130 - refused call targets: three starts rebased, four orphans added (S1c-4e)

Six of the call targets finding 126 refused were examined again by decoding the cleared bytes on a copy.  Three were
not orphans but the true entries of existing, user-named functions whose start had been cut inside an instruction (a
single `db 0BAh` / `db 0B8h` left by the misdecode, which `create_insn` cannot turn back into code on its own because
the real instruction is three bytes long):

- `r12_state36_reset_stub` 0x106EEC (78 B) -> **0x106EE2 (88 B)**: `xor ax,ax / mov ds:36h,ax / mov bx,3Ch /
  mov dx,8000h`, then the state tests, ending `retf` at 0x106F39.  0x106EEC and 0x106EF1 stop being instruction heads
  (no jump or call reached them).  Call-reached from 0x106F73.
- `r15_op_init_sequence` 0x10843D (105 B) -> **0x108430 (118 B)**: `push ds / push es / mov ax,cs / mov ds,ax /
  mov ax,0 / mov bx,6 / mov dx,5B3h` then the old body.  Only 0x10843D stops being a head.  Called from 0x108718.
- `r27_table_copy_far_entry` 0x10CFA6 (70 B) -> **0x10CE30 (444 B)**.  This one is a merge, not a shift: the 373 B body
  at 0x10CE30 (`push bp / mov bp,sp / push si / push di`, copies the 31F0h words into 7A32h, runs the
  `op_dispatch_far_entry` sequences) falls through `mov word ptr es:0AE96h,0` into `mov ax,31F0h` at 0x10CFA5, which is
  the "table copy" the old 70 B function started one byte too late.  It is one 444 B far function entered by the
  call at 0x10CE1C and ending `retf` at 0x10CFEB; the old name stays on the whole.  Because the name described only
  the tail, treat it as provisional.

Four were genuine orphans and were added: `0x10931E` (138 B; a 32 B hole 0x109388..0x1093A6 was re-decoded first and
the run shares the `pop ds / retn` at 0x1093A7 with the function after it, so the end is 0x1093A8), `0x109445`
(212 B, `call loc_109445` from inside sub_1093A8), `0x129F7` (283 B, far-called from 0x109670/0x109685) and `0x12B12`
(80 B, far-called from 0x109690).  All four decode with no gaps to a `retn` / `retf`.

**Applied.** `tools/apply_orphan_funcs.py` gained `REBASE` (manifest key `rebase_funcs`) and `ADD_CLEAR`:
a rebase does `del_func(old)`, drops the old name, `del_items` over `[clear_lo, end)`, recursive descent from the new
start, `add_func(new, end)`, then restores name and far flag; for 0x106EE2 the DS range (0x706E) is split down to the new
start so the three new bytes keep the function's DS.  It refuses unless every original head that stopped being a head
is unreached by any call/jump from outside the function and matches the `lost_heads` list in the manifest.  Each
entry pins the old and new sha256 and the sha256 of the prefix.  `ADD_CLEAR` is the same clear-and-redescend for the
four orphans.  Plan, dry replay (7 fresh, 18 applied, 0 mismatched), backup `FALCONCD.EXE.i64.bak_rebase3`, apply.
Functions 3,552 -> 3,556.  Gates: integrity INTACT, `naming.py check` OK, `verify_rebuild` faithful (LOST 0, ADDED 4,
REBASE 3, CHANGED 0).

Gate changes: (1) `extract_ida_bytes.py` carries a key across a rebase (old ea -> new ea from the manifest), so
`r12_e35`, `r15_e16` and `r27_e64` stay the ledger keys; (2) `verify_rebuild.py` has a REBASE category that accepts a
changed ea/size only when the old key's sha256 and the new sha256 both match the manifest, the end is unchanged and
the name is unchanged.  Registry text updated per the live-IDB-canonical rule: `routines.yaml` `ea`/`seg`/`ofs`/`size`
and the sig/notes of the three entries (naming.yaml sig/notes likewise).  `registry/ds_expected.json` still has the DS
point at 1076972, which lies inside the range the rebase re-split, so `apply_default_ds.py` and the rebase manifest
agree on the replay order (default DS first, orphan funcs after); the split at 0x106EE2 is created by the rebase.

**Still open from finding 126:** nothing in the refused call-target list.  The remaining orphans are the fl_F
fragments, the jmp-reached tails (0x4334E, 0x100DED), and the no-xref runs.
"""

edit("docs/findings_log.md", [], F130)
edit("status.md", [
 ("""     - Left open (findings 126-129): 6 refused call targets, 7 tiny/misdecoded fl_F fragments, 0x105DA9 and the
       0x100CC0..0x100DFA data-decoded body, remaining jmp-reached tails, no-xref runs.""",
  """     - **S1c-4e (finding 130):** the refused call targets: r12_state36_reset_stub / r15_op_init_sequence starts rebased
       to 0x106EE2 / 0x108430, r27_table_copy_far_entry merged with the 0x10CE30 body (444 B), 0x10931E / 0x109445 /
       0x129F7 / 0x12B12 added; functions 3,552 -> 3,556; backup `.bak_rebase3`. New gate category REBASE.
     - Left open (findings 126-130): 7 tiny/misdecoded fl_F fragments, 0x105DA9 and the 0x100CC0..0x100DFA
       data-decoded body, remaining jmp-reached tails, no-xref runs."""),
 ("     - commit S1c-4d;\n", "     - commit S1c-4e;\n"),
])
edit("docs/workflow/idb_regeneration.md", [
 ("and five fall-through continuations (finding 129: five functions extended)\n",
  "and five fall-through continuations (finding 129: five functions extended) and the refused call targets (finding 130: three function starts rebased, four orphans added)\n"),
])
