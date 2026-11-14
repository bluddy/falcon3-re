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


# ---- runbook
p = "docs\\workflow\\idb_regeneration.md"
s = rd(p)
e = eol(s)
s = s.replace("3,547", "3,549")
s = sub(s, "# 6g. S1c-4 call-reached orphan code registered as functions (finding 126)",
        "# 6g. S1c-4 orphan code registered as functions: call-reached runs (finding 126) and the two R20/R21 menu bodies (finding 127)")
wr(p, s)

# ---- status
p = "status.md"
s = rd(p)
e = eol(s)
old = "     - Left open (finding 126): 8 refused call targets, jmp-reached R20/R21 entries, fl_F continuations, no-xref runs." + e
new = e.join([
    "     - **S1c-4b (finding 127):** the two jmp-reached R20/R21 menu bodies 0x10B380 / 0x10B720 registered",
    "       (their damaged `call far` re-decoded, all 6 key handlers decoded); functions 3,547 -> 3,549; backup `.bak_menus`.",
    "     - Left open (findings 126/127): 8 refused call targets, fl_F continuations, jmp-reached tails, no-xref runs.",
]) + e
s = sub(s, old, new)
wr(p, s)

# ---- findings
p = "docs\\findings_log.md"
s = rd(p)
e = eol(s)
f = [
    "",
    "## 2026-11-10 127 - R20/R21 menu bodies registered as functions (S1c-4b)",
    "",
    "**What they are.** 0x10B380 and 0x10B720 are entered only by a jmp from the RTLink thunks 0x2C2A0 / 0x2C2E6",
    "(`enter 2,0`, `mouse_gate_far_entry`, four `call far loc_6DFF0` button draws, then a keyboard dispatch).  They",
    "were orphan code in two pieces each, joined by a loop-back `jmp` and a damaged `call far`:",
    "",
    "- the `call far flag_table_pop_far_thunk` at 0x10B4E8 / 0x10B888 was three `db` bytes plus an `insb` (the fixup",
    "  bytes 9Ah, 03h, 5Bh were decoded off by one); re-decoding it as a 5-byte call joins the loop-back to the",
    "  tail 0x10B4EB / 0x10B88B;",
    "- the key dispatch is `mov cx,n; mov bx,tab; cmp ax,[bp-2]; loop; jmp word ptr cs:[bx+16h]`: an n-entry key",
    "  table (n = 11 for R20, 12 for R21) followed by n handler offsets relative to the body base.  Each distinct",
    "  handler (5 per body) was undecoded bytes; decoding them by recursive descent leaves no data inside the body.",
    "",
    "**Applied.** `tools/apply_orphan_funcs.py` now also carries `MENUS`: plan mode derives the handler seeds from the",
    "table, the manifest records `redecode` and `seeds`, replay re-decodes, decodes the seeds, `add_func(base, end)`,",
    "and requires one chunk, only code heads, and no change to any existing function.  0x10B380..0x10B6DF (863 B) and",
    "0x10B720..0x10BA7B (859 B) are now functions; 3,547 -> 3,549.  Integrity INTACT, `verify_rebuild` faithful",
    "(ADDED 2), `naming.py check` OK.  Backup `FALCONCD.EXE.i64.bak_menus`.",
    "",
    "**Why the other refused targets stay open.** Walking the flow without changing the IDB showed that most of",
    "them are not clean function bodies: 0x106EE2 / 0x108430 start 3-4 bytes before an existing function",
    "(0x106EEC `r12_state36_reset_stub`, 0x10843D `r15_op_init_sequence`) around a stray `db 0BAh` (the entry",
    "bytes are inside a `mov dx,imm` operand, i.e. a misdecode, not an entry); 0x109445 is a self-modified `mov ax,0ABCDh`",
    "block that runs into the existing 0x109519; 0x10CE30 runs 373 B into the existing 0x10CFA6.  These need the",
    "existing function moved or its start re-decoded (a rebase), not an add.  0x129F7 and 0x10931E are the",
    "candidates for a later round.",
    "",
]
if not s.endswith(e):
    s += e
s += e.join(f)
wr(p, s)
print("ok")
