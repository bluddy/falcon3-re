P = r"C:\Users\ybarnoy\projects\falcon3"
FIND = """
## 2026-11-10 132 - two fl_F fragments resolved by rebase: r17_ui_event_loop and r6e_heap_layout_finish (S1c-4g)

Seven fl_F fragments (a function chunk reached only by fall-through from a stray head) were classified on probe copies.
Two are the same defect as finding 130: a user-named function whose real entry is a few bytes in front of its start.

**0x6EF30 (r17_ui_event_loop, 0x6EF31 -> 0x6EF30, 669 -> 670 B, far).**  The bytes `C8 02 00 00` are `enter 2,0`; the old
start was the middle of it (`db 0C8h` left as 0x6EF30 `unk_6EF30`).  `call far ptr unk_6EF30` at 0x6EEB6 enters at 0x6EF30.
**0x69720 (r6e_heap_layout_finish, 0x69723 -> 0x69720, 931 -> 934 B, near).**  `push 0 / push 0 / push 6 / call far
op_dispatch_far_entry / add sp,0Ah` precede the old start; the misdecode left `db 6Ah` at 0x69722, and r30_state_push_6e14f
(0x69705..0x69720) falls through into the real entry.

`create_insn` had failed at both stray `db` heads in the finding-130-style trial descents.  The rebase flow
(`del_func` of the old function first, then clear and descend) succeeds, so the earlier failure was the old function
boundary, not the bytes.  `REBASE` gained an optional 6th element `clear_hi` (manifest key `clear_hi`): only
[new, clear_hi) is cleared and redecoded, so a 670-B body is not wiped to reach a 9-B prefix; the head check and
descent stop at `clear_hi`.  Both names are carried over (user names); original heads that stop being heads: 0x6EF31,
0x6EF33, 0x6EF37 and 0x69723, none referenced from outside.

**Gates.**  `verify_rebuild` counted the two as CHANGED because the keep_fns of ovl_R30_569F and ovl_R17_5E8F pin the
pre-rebase (ea, size); the register check now reads a rebased start back at its pre-rebase ea and size (the rebase itself
is verified by the REBASE category, which pins both sha256).  Result: REBASE 2, CHANGED 0, faithful; integrity INTACT;
`naming.py check` OK; `function_bytes.json` has 6 changed lines (ea/size of the two keys, keys r17_e07 and sub_69723 kept);
dry replay of the manifest: 29 applied, 0 mismatched.  Functions stay at 3,557.  Backup `FALCONCD.EXE.i64.bak_frag`.

**Still open fl_F fragments (analysis only, nothing applied).**  They need a deleted-function path in the gates, which
`verify_rebuild` does not have (a deletion is LOST):
- 0x6EF1F (`r17_entry_partial`, 3 B) and 0x6EC17 (`data_fragment_6ec14`, 3 B): heads of word key tables, data not code;
- 0x2E1E8 (sub_2E1C2, 38 B): a data table, code resumes at 0x2E20A;
- 0x167449 (`r38_data_fragment`, 9 B, 0x167440..0x167449): a misdecode inside function 166F80; real code at 0x16743E is
  `mov ax,7894h / mov es,ax / cmp byte ptr es:[19C2h],0 / jz loc_167450 / call far ...`, so 166F80's chunks
  (166F80-1673D0, 16740F-16743E, 167450-16781A, 167827-167AFF) must be restructured;
- 0x22C8B: fixed_vec3_read (0x22C62..0x22C8B) is code `mov ax,cs:22C71 / mov bx,cs:22C73 / mov cx,cs:22C75 / retf`
  followed by data words; the fragment after them is junk;
- 0x67F77: sub_67F59 / sub_67F7B are twin mid-instruction entries of the same `7894h` / record-walk code.
Also open: 0x105DA9..0x105EB5 junk run, 0x12C4F2 / 0x12C9D0 / 0x12CB27, the no-xref runs.
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
    ("     - Left open (findings 126-131): 7 tiny/misdecoded fl_F fragments, 0x105DA9 junk run, 0x12C4F2 / 0x12C9D0, no-xref runs.",
     "     - **S1c-4g (finding 132):** two fl_F fragments were mid-instruction function starts: r17_ui_event_loop rebased to\n"
     "       0x6EF30 and r6e_heap_layout_finish to 0x69720 (`REBASE` gained `clear_hi`; `verify_rebuild` reads a rebased\n"
     "       start back through the register manifests); functions stay 3,557; backup `.bak_frag`.\n"
     "     - Left open (findings 126-132): 5 fl_F fragments (data tables / function removal needs a gate path: 0x6EC17,\n"
     "       0x6EF1F, 0x2E1E8, 0x167449, 0x22C8B, 0x67F77), 0x105DA9 junk run, 0x12C4F2 / 0x12C9D0, no-xref runs."),
    ("     - commit S1c-4f;\n", "     - commit S1c-4g;\n"),
])
edit(P + r"\docs\workflow\idb_regeneration.md", [
    ("and the jmp-reached tails (finding 131: a two-chunk function added, one start rebased)",
     "and the jmp-reached tails (finding 131: a two-chunk function added, one start rebased) and two more mid-instruction starts (finding 132: rebased with a narrow clear_hi)"),
])
print("ok")
