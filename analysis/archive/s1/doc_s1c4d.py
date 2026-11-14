import io
ROOT = r"C:\Users\ybarnoy\projects\falcon3"


def rd(p):
    return io.open(ROOT + "\\" + p, "r", newline="", encoding="utf-8").read()


def wr(p, s):
    io.open(ROOT + "\\" + p, "w", newline="", encoding="utf-8").write(s)


def eol(s):
    return "\r\n" if "\r\n" in s else "\n"


def sub(s, old, new):
    assert s.count(old) == 1, old
    return s.replace(old, new)


p = "docs\\workflow\\idb_regeneration.md"
s = rd(p)
s = sub(s, "the 0x12C5xx cluster (finding 128: two function ends extended, three added)",
        "the 0x12C5xx cluster (finding 128: two function ends extended, three added) and five fall-through continuations (finding 129: five functions extended)")
wr(p, s)

p = "status.md"
s = rd(p)
e = eol(s)
old = "     - Left open (findings 126-128): 6 refused call targets, fl_F continuations, remaining jmp-reached tails, no-xref runs." + e
new = e.join([
    "     - **S1c-4d (finding 129):** five fall-through continuations joined to their owners (r27_state_buffer_init_entry,",
    "       stack_switch_7a32, sub_3F6A9, farobj_record_step as a tail chunk, flag_block_scan_nonzero); functions stay 3,552;",
    "       backup `.bak_cont`. The manifest now records run, chunk lists before/after and the run's sha256.",
    "     - Left open (findings 126-129): 6 refused call targets, 7 tiny/misdecoded fl_F fragments, 0x105DA9 and the",
    "       0x100CC0..0x100DFA data-decoded body, remaining jmp-reached tails, no-xref runs.",
]) + e
s = sub(s, old, new)
s = sub(s, "     - commit S1c-4;" + e, "     - commit S1c-4d;" + e)
wr(p, s)

p = "docs\\findings_log.md"
s = rd(p)
e = eol(s)
f = [
    "",
    "## 2026-11-10 129 - fall-through continuations joined to their owners (S1c-4d)",
    "",
    "Five orphan code runs are entered only by falling through from the end of an existing function, so they are the",
    "rest of that function, not new ones.  Each was decoded as clean code with no non-code head inside, and no other",
    "function owned any byte of it:",
    "",
    "- `r27_state_buffer_init_entry` 0x10CC60 (46 B) + 0x10CC8E..0x10CE05 (375 B, ends `retf`) -> 0x10CC60..0x10CE05.",
    "  The following function 0x10CE05 is called from 0x10CDF7, inside this body (and from 0x10CC1E, before it).",
    "- `stack_switch_7a32` 0x2D31A + 0x2D353..0x2D375 (SETBLOCK, `call far alloc_read_mscdex`, then `mov ax,4C00h / int 21h`",
    "  process exit, which ends the run without a `retn`) -> 0x2D31A..0x2D375.",
    "- `sub_3F6A9` 0x3F6A9 + 0x3F6C7..0x3F6D6 (the `jmp short loc_3F6AD` at 0x3F6C5 is the loop back edge; 0x3F6CE and",
    "  0x3F6D1 are targets of branches inside 0x3F6A9) -> 0x3F6A9..0x3F6D6.",
    "- `farobj_record_step` 0x2142E has two chunks (0x2142E..0x215B7 and 0x215C1..0x215FE); the run 0x215FE..0x21631",
    "  (`cmp ax,7FFFh / jz loc_215E7` loop, ends `retn`) continues the second chunk, so it was appended as a tail chunk",
    "  (`append_func_tail`): main end stays 0x215B7, tail becomes 0x215C1..0x21631.",
    "- `flag_block_scan_nonzero` 0x2520B (21 B) + 0x25220..0x25224 (`sub ax,ax / jmp short loc_25242`) + its own tail",
    "  0x25224..0x25247: the `loop` at 0x2521E falls into the run, whose `jmp short loc_25242` lands in the existing tail;",
    "  `jnz loc_25224` skips the run.  `set_func_end` to 0x25247 turns the two chunks into one contiguous function of 60 B.",
    "",
    "**Applied.** `tools/apply_orphan_funcs.py` gained `EXTEND_RUNS` (func, run_lo, run_hi): `set_func_end` when the run",
    "starts at the main-chunk end, `append_func_tail` otherwise.  A manifest entry now records the run, its sha256, the",
    "sorted chunk lists before and after, and `before_end`/`end` of the main chunk; the old finding-128 entries are",
    "normalised on load.  The post-check still requires every other function to be unchanged and names to be kept.",
    "Plan, dry replay (5 fresh, 13 already applied, 0 mismatched), backup `FALCONCD.EXE.i64.bak_cont`, apply.  Functions",
    "stay at 3,552.  Gates: integrity INTACT (after the re-extract), `naming.py check` OK, `verify_rebuild` faithful",
    "(EXTEND 4, CHANGED 0).  Two gate adjustments: (1) `function_bytes.json` is re-extracted from the live IDB, since",
    "the span check compares live sizes (4 spans differ until then: sub_2520B 21->60, r01_e01 57->91, sub_3F6A9 30->45,",
    "r27_e62 46->421); (2) `verify_rebuild.py` compares a register entry against the PRE-extension size of an allowlisted",
    "EXTEND (`res_2520B` pins sub_2520B at 21 B), the extension itself being checked by the appended-bytes sha256.  Because",
    "`function_bytes.json` only records the main chunk, `farobj_record_step` (tail chunk only) produces no byte-level",
    "change and is therefore not in the EXTEND count; the manifest still pins its tail.",
    "",
    "**Not done on purpose.**  The remaining fl_F fragments (`0x6EC17`, `0x6EF1F`, `0x2E1E8`, `0x22C8B`, `0x67F77`,",
    "`0x69720`, `0x167449`, 2-12 B each) read as junk or as the tail of an instruction the owner decoded differently",
    "(e.g. `add [di+0],al` / `in ax,5` after a `retf`, `push 0` cut before a `db 6Ah`), and `0x105DA9..0x105EB5` is a",
    "268 B run of `add al,0D0h` noise after `sub_105DA7`.  They look like misdecodes, so they need a re-decode of the",
    "surrounding bytes, not an extension.  The jmp-reached tails stay open too: 0x4334E (`mov al,3 / call sub_40E38 ...`)",
    "is entered by a `jnz` at 0x42F6A from another function, and 0x100DED..0x100DFA is the epilogue (`retf 0Ch`) of an",
    "unowned body that runs from 0x100D0D (the visible function at 0x100D01 ends at its `retf`) and is preceded by",
    "bytes 0x100CC0..0x100D00 that are still `db`; that body needs its own re-decode round.",
    "",
]
if not s.endswith(e):
    s += e
s += e.join(f)
wr(p, s)
print("ok")
