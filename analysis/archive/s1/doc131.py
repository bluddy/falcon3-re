P = r"C:\Users\ybarnoy\projects\falcon3"
FIND = """
## 2026-11-10 131 - jmp-reached tails: a two-chunk function around sub_100D01, sub_4335A rebased (S1c-4f)

The two jmp-reached tails left by finding 130 were decoded on a copy and applied.

**0x100CA8 (a far callback, 88 B + a 236 B tail chunk).**  `push bp / mov bp,sp / push si / push di`, loads the
`les si,[bp+6]` argument block, stores it at ds:9A3Eh, calls the handler through `call dword ptr es:[si+12h]`, and
returns the status in AX through the shared epilogue `pop di / pop si / pop bp / retf 0Ch` at 0x100DF4..0x100DF9.
Nothing calls it: the only reference is `mov ax,0CA8h` at 0x100D05 inside sub_100D01 (`r02_farptr_pair_call_entry`,
0x100D01..0x100D0D), which pushes the far pointer 2CF6h:0CA8h for sub_10007F.  The body is split by that 12 B wrapper,
which really is a separate function (it is jumped to from 0x2BFC6), so the function is two chunks:

- main chunk 0x100CA8..0x100D00 (88 B), ending `mov ax,3 / jmp loc_100DF4`;
- tail chunk 0x100D0E..0x100DFA (236 B), reached by the `ja short loc_100D0E` at 0x100CF8 and ending `retf 0Ch`.

The bytes were all `db` before.  `db 0EAh` at 0x100D00 and 0x100DFA and `db 0C7h` at 0x100D0D are padding that no flow
reaches; the stray `db 81h` at 0x100DEC (between `jmp short loc_100DF4` and `sub ax,ax`) is also unreached and is left as data
inside the tail chunk.  The `call sub_100DFB` at 0x100DDF is now inside a function.  Left unnamed (`sub_100CA8`): after the indirect call, AX <= 4 returns 3
through the epilogue and AX > 4 continues at 0x100D0E, which copies fields of the es:[si+221Eh] record.  Naming is
for the DAG pass.

**0x4334E (sub_4335A rebased, 59 B -> 71 B).**  `mov al,3 / call sub_40E38 / mov cl,ah / xor ch,ch / mov ax,19h` falls
into the old start at 0x4335A (`mov bl,28h`), whose only reference was the `fl_F` flow from 0x43357.  The entry is
`jmp loc_4334E` at 0x42F6A inside sub_42F5B.  The function was unnamed, so the rebase carries no name (the rebase code
now uses a user-name test and skips `set_name` for dummy names).  Original code heads that stop being heads: none.

**Applied.**  `tools/apply_orphan_funcs.py` gained `TAILS` (an add with a second chunk: `clears`, `seeds`, `tails`,
`tails_sha256`, `pad`; `add_func` for the main chunk, `append_func_tail` for the rest, descent per chunk, terminator
and no-non-code-head check per chunk) and unnamed rebases.  Plan, dry replay (2 fresh, 25 applied, 0 mismatched),
backup `FALCONCD.EXE.i64.bak_tails`, apply.  Functions 3,556 -> 3,557.  Gates: integrity INTACT, `naming.py check`
OK (2038 ledger entries), `verify_rebuild` faithful (ADDED 1 = sub_100CA8, REBASE 1, CHANGED 0), idempotent replay
(27 applied).  `function_bytes.json` records the main chunk only, so sub_100CA8 shows as 88 B.

**Still open:** the fl_F fragments (0x6EC17, 0x6EF1F, 0x2E1E8, 0x22C8B, 0x67F77, 0x69720, 0x167449), the 268 B
`add al,0D0h` junk after sub_105DA7 (0x105DA9..0x105EB5), 0x12C4F2 / 0x12C9D0 / 0x12CB27, and the no-xref runs.
"""
p = P + r"\docs\findings_log.md"
s = open(p, newline="", encoding="utf-8").read()
s = s.rstrip("\r\n") + "\r\n" + FIND.replace("\n", "\r\n")
open(p, "w", newline="", encoding="utf-8").write(s)

p = P + r"\status.md"
s = open(p, newline="", encoding="utf-8").read()
a = """     - Left open (findings 126-130): 7 tiny/misdecoded fl_F fragments, 0x105DA9 and the 0x100CC0..0x100DFA
       data-decoded body, remaining jmp-reached tails, no-xref runs."""
b = """     - **S1c-4f (finding 131):** the jmp-reached tails: 0x100CA8 added as a two-chunk far function (88 B + 236 B tail around
       sub_100D01), sub_4335A rebased to 0x4334E (59 -> 71 B, unnamed); functions 3,556 -> 3,557; backup `.bak_tails`.
       The apply tool gained `TAILS` and unnamed rebases.
     - Left open (findings 126-131): 7 tiny/misdecoded fl_F fragments, 0x105DA9 junk run, 0x12C4F2 / 0x12C9D0, no-xref runs."""
assert a in s
s = s.replace(a, b).replace("     - commit S1c-4e;\n", "     - commit S1c-4f;\n")
open(p, "w", newline="", encoding="utf-8").write(s)

p = P + r"\docs\workflow\idb_regeneration.md"
s = open(p, newline="", encoding="utf-8").read()
a = "(finding 130: three function starts rebased, four orphans added)"
assert s.count(a) == 1
s = s.replace(a, "(finding 130: three function starts rebased, four orphans added) and the jmp-reached tails (finding 131: a two-chunk function added, one start rebased)")
open(p, "w", newline="", encoding="utf-8").write(s)
print("ok")
