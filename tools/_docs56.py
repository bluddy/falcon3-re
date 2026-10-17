"""Record finding 56 in time_log.yaml (CRLF), status.md and open_items.md.

Idempotent + line-ending preserving.
"""
import io

ROW = ("| 2026-10-17 (session 17v) | ~4 h | **Finding 56: built the "
       "Resident->Thunk->Overlay bridge (8 -> 213 crossing edges) and explained "
       "the +0x1540 anchor.** Step 1: `THUNK=0x1EBAF` was **53 entries into** "
       "the 303-entry table (0x1E99D; patch_thunks.log calls 0x2BFAF `Thunk "
       "#053`) -- fixed in prep_overlay_entries / parse_thunks / "
       "solve_thunk_assignment / validate_record_bases; overlay_entries 248 -> "
       "**301 rows covering all 303 slots**, with `covered_seg` recorded "
       "instead of silently dropping the 3 their own row does not reach. "
       "Step 2: **registered 254 free slots @8B**, split `sub_2BFCD` 210B -> "
       "**21x10B** and `sub_2BE83` 20B -> **2x10B** (10B ONLY so verify_rebuild's "
       "SPLIT tiles exactly; 8B would leave 2B holes = CHANGED); slot #053 was a "
       "foreign chunk of `start` -> remove_func_tail, **xref kept**; **slot #302 "
       "is impossible** (straddles loader boundary seg021 0x2AA30..0x2C970 | "
       "seg022 0x2C970..0x2CF60, add_func refuses cross-segment - finding 37's "
       "constraint; **0 refs in or out**) -> **302/303 accepted**. **Decode bug:** "
       "the register loop advanced with next_head(slot,slot+8), which finds no "
       "head after the 3-byte `call`, so the `jmp far` at slot+3 was never "
       "created -- decode_thunk_jmps.py walks by instruction SIZE: 276 insns "
       "created, `last_mnem=jmp` **58 -> 334**. export_epilogues was reading the "
       "DERIVED classification.json so new fns would have been classed DATA "
       "(finding 49) -> now reads function_bytes. Ledger: overlay_tail_bridge_b's "
       "'rest is resident-tail data' disproven (21/21 are E8+EA+rec thunks), "
       "notes rewritten, class DATA -> ASM. Step 3: register_bridge_targets.py "
       "624 candidates -> 617 on written bytes, 7 in no segment; rejections "
       "no-prologue 274 (65%) / no-terminator 106 / already 27; **120 registered, "
       "final run 0 left** (criteria exhausted). Step 4 **CONFIRMED**: "
       "absolute = `(seg-w0)*16 + off`; dominant R05_1E10 anchor `0x1F64 = "
       "w0+0x154` = **+0x1540 -> IDA 0x2F640** (reproduces 0x2106-0x1FB2=0x154). "
       "word-ok **100%** for every non-zero anchor (1442/1442, 571/571, 394/394, "
       "387/387) vs 57-71% for base=off; all non-zero anchors 3488 vs 2042; FAR "
       "cross-check 10094 vs 5926 (R05: 125 -> 2463/2798 = 88%, chance ~43). "
       "**Not a fixup base offset but a multi-sub-block split: 24 distinct "
       "paragraph anchors in R05_1E10**, and the anchor begins with a real name "
       "table `0600 1100 1b00` + `global.amo/local.amo/harpoon.dat`; first fixup "
       "at +0xA7, **0 of 1442 inside it**; no IDA segment split, no fn boundary "
       "at 0x2F640. **Fixup correction NOT applied** (12,118 fixups -> mass "
       "CHANGED -> needs a finding-53-style manifest + own gate cycle). "
       "Effect: fns 1284->1678, static 1764->2493, unresolved 1257->**702**, "
       "overlay fns 255->359, **res->ovl edges 8->213, ovl reached from resident "
       "5->73**, refs into thunk table 228/204-unres -> **230/0**, slots emitting "
       "JMP FAR 27 -> **296/303**, orphans 232 -> 228 (pre-existing orphans "
       "largely untouched). Residual: **346 distinct destinations remain and NONE "
       "passes the guards** -> diagnosis problem, not registration. Gates: check "
       "OK 267, verify_rebuild ADDED 120 / SPLIT 2 / CHANGED 0 / LOST 0, verify_idb "
       "INTACT 1678, read-back 265/265+2/2. |")

STATUS_PARA = (
    "**The Resident -> Thunk -> Overlay bridge now exists (finding 56):** crossing "
    "edges **8 -> 213**, distinct overlay functions reachable from resident "
    "**5 -> 73**, refs INTO the thunk table **204 unresolved -> 0 of 230**, slots "
    "exporting their JMP FAR **27/303 -> 296/303**, functions **1,284 -> 1,678**, "
    "static edges **1,764 -> 2,493**, `static_unresolved` **1,257 -> 702**. Both "
    "causes were mechanical: the thunk table was read **53 entries late** "
    "(`0x1EBAF` vs the real `0x1E99D`, i.e. `Thunk #053` not `#000`) and the "
    "registration decode stopped one instruction short of the `jmp far` at "
    "`slot+3`. **Slot #302 (`0x2C969`) can never be a function** -- it straddles "
    "the loader boundary `seg021 0x2AA30..0x2C970 | seg022 0x2C970..0x2CF60` and "
    "`add_func` refuses cross-segment ranges (finding 37); it has **0 refs** in or "
    "out, so 302/303 is accepted. **The `+0x1540` mystery is solved**: the fixup "
    "`seg` field names a paragraph anchor, so `abs = (seg-w0)*16 + off` "
    "(`0x1F64 = w0+0x154` -> IDA `0x2F640`), giving 100% word-ok for every "
    "non-zero anchor; `R05_1E10` is a **24-sub-block split**, and the anchor "
    "begins with a name table (`global.amo`/`local.amo`/`harpoon.dat`), not a "
    "fixup base. The 12,118-fixup correction is **verified but deliberately not "
    "applied** (it would mass-CHANGE overlay bytes and needs a manifest)."
)

OPEN_NEW = [
    "   **(i) and (ii) below are now FIXED -- finding 56 built the bridge:**",
    "   crossing Resident->Overlay edges **8 -> 213**, overlay fns reachable from",
    "   resident **5 -> 73**, refs into the thunk table **0 unresolved of 230**",
    "   (254 slots registered, `sub_2BFCD` 210B split 21x10B, `sub_2BE83` 20B",
    "   split 2x10B, slot #053 detached from `start` with its xref kept).",
    "   **Remaining:** (a) **346 distinct destinations stay unregistered and NONE",
    "   passes the prologue/terminator guards** (274 have no 16-bit prologue, 106",
    "   no reachable terminator) -- the residual `static_unresolved = 702` is now a",
    "   *diagnosis* problem, not a registration one; (b) overlay orphans only",
    "   232 -> 228, because the pre-existing orphans are functions nothing CALLS;",
    "   (c) slot #302 (`0x2C969`) is permanently un-registerable -- it straddles",
    "   the loader segment boundary `seg021 0x2AA30..0x2C970 | seg022 0x2C970`",
    "   and has 0 refs either side; (d) **staged, not run:** the `+0x1540` fixup",
    "   correction (`abs = (seg-w0)*16 + off`, verified 100% word-ok per anchor)",
    "   would add 12,118 fixups -> mass CHANGED -> needs a finding-53-style",
    "   exact-match manifest and its own backup/gate cycle.",
]


def load(p):
    return io.open(p, encoding="utf-8", newline="").read()


def save(p, t):
    io.open(p, "w", encoding="utf-8", newline="").write(t)


# ---- time_log.yaml (CRLF) ----
p = "docs/time_log.yaml"
raw = load(p)
if "session 17v" in raw:
    print("time_log: 17v already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 17" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 17v after line %d" % (idx + 1))

# ---- status.md (CRLF) ----
p = "status.md"
raw = load(p)
if "bridge now exists (finding 56)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted before %r" % a)

# ---- docs/open_items.md (CRLF) ----
p = "docs/open_items.md"
raw = load(p)
if "are now FIXED -- finding 56" in raw:
    print("open_items: already updated")
else:
    lines = raw.split("\n")
    start = next(i for i, l in enumerate(lines)
                 if "Finding 55 triaged the 1,257" in l)
    end = next(i for i in range(start, len(lines))
               if "re-triage the 408 fixable far-op rels" in lines[i])
    assert "433 of them in `R05_1E10`" in lines[end + 1], lines[end + 1]
    cr = "\r" if lines[start].endswith("\r") else ""
    lines[start:end + 2] = [x + cr for x in OPEN_NEW]
    save(p, "\n".join(lines))
    print("open_items: replaced lines %d..%d with %d" % (start + 1, end + 2, len(OPEN_NEW)))
