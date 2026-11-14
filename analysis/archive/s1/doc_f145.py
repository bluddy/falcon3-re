"""doc_f145.py: document finding 145 (P1 batch 1: 40 pure-split merges)."""
def edit(p, fn):
    s = open(p, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    s = fn(s)
    open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
    print("ok", p, crlf)


ROOT = r"C:\Users\ybarnoy\projects\falcon3"

LOG_ENTRY = """
## 2026-11-11 145 - P1 batch 1: split 40 pure-split merged functions (S1c-5a)

**What was wrong.**  After findings 123-144, 407 direct call targets land right after a ret/jmp inside the
owner function (merged functions).  The merged_split probe classified 394 of these as pure splits (no non-call
inner xref to the target, single-chunk owner) so the two halves are independent.

**Fix.**  New manifest block `split_funcs` and apply mode `SPLIT` (`sp_state` / `split_fn`): for each
`(owner, at)` pair, `set_func_end(owner, at)` shrinks the owner to `[owner, at)` and `add_func(at, end)`
registers a new unnamed function `[at, end)` with the same far flag.  Both halves are sha256-pinned in the
manifest.  `verify_rebuild.py` gained `load_split_funcs()` and an `is_expected_split()` check that validates
both sha256 halves before classifying the owner as SPLIT (falls back to auto-detection if unmatched).

**Batch 1 (40 splits)**: resident seg000 through early R05 overlays (owners at 0x100AF..0x37051), one split
per owner (lowest split point; remaining split points will appear in the new tail function and are handled in
later batches).  Owners with names kept their names; new tail functions are `sub_<at>`.

**Results.**
- Functions 3,590 -> 3,630 (+40 new tail functions).
- Ledger 2,034 (unchanged).
- Mid-body call targets: 529 / 1,299 sites -> 489 / 1,156 sites.
  - merged_fn: 407 / 1,031 -> 367 / 888 (40 targets / 143 sites removed by this batch).
  - Other classes unchanged (not_head 64/125, prologue fall-in 26/48, secondary 23/68, other 9/27).

**Applied.**  Plan (40 fresh, 92 applied), dry replay, backup `FALCONCD.EXE.i64.bak_split145`, apply.
Gates: integrity INTACT, `naming.py check` OK (2034), `verify_rebuild` faithful
(SPLIT 40 sha256-pinned + ADDED 40 + LOST 0 + CHANGED 0), idempotent replay (132 applied).

**Still open in P1:** 354 remaining pure-split targets in 115 owners (many have multiple split points that
will surface in later batches), 12 shared tails, 1 multi-chunk (`segment_clip_test` 0x25F93).
"""


def log(s):
    return s.rstrip("\n") + "\n" + LOG_ENTRY


STATUS_OLD = "   - **S1c-4s (finding 144):**"
STATUS_NEW = """   - **S1c-5a (finding 145):** P1 batch 1: 40 pure-split merged functions split (new SPLIT mode,
       split_funcs manifest block, sha256-pinned both halves); functions 3,590 -> 3,630; backup `.bak_split145`.
     - **S1c-4s (finding 144):**"""

NOW_OLD = "   - **Now (after finding 144, measured 2026-11-11):** 3,590 functions, ledger 2,034; 529 mid-body targets / 1,299 sites\n     (407 merged functions, 64 misdecodes, 26 + 23 fall-in entries, 9 other); 96 orphan code runs / 221 B, of which\n     92 are 1-2 B padding left on purpose.  Of the 407 merged targets, 394 are pure splits (978 sites), 12 are shared\n     tails (21 sites) and 1 is multi-chunk."
NOW_NEW = "   - **Now (after finding 145, measured 2026-11-11):** 3,630 functions, ledger 2,034; 489 mid-body targets / 1,156 sites\n     (367 merged, 64 misdecodes, 26 + 23 fall-in entries, 9 other); 96 orphan code runs / 221 B (92 are 1-2 B padding).\n     Of the 367 merged, 354 are pure splits (~835 sites remaining), 12 shared tails, 1 multi-chunk."

P0_OLD = "     - P0 commit S1c-4r / S1c-4s (findings 143, 144; applied and gated, not committed);\n"
P0_NEW = ""  # P0 is done; remove it

P1_OLD = "     - P1 split the 394 pure-split merged functions (new `SPLIT` mode, batches of ~40);"
P1_NEW = "     - P1 split merged functions (in progress, batch 1 of ~10 done in finding 145; 354 pure-split targets remain);"


def status(s):
    assert s.count(STATUS_OLD) == 1, "STATUS_OLD not found"
    s = s.replace(STATUS_OLD, STATUS_NEW)
    assert s.count(NOW_OLD) == 1, "NOW_OLD not found"
    s = s.replace(NOW_OLD, NOW_NEW)
    if s.count(P0_OLD) == 1:
        s = s.replace(P0_OLD, P0_NEW)
    assert s.count(P1_OLD) == 1, "P1_OLD not found"
    s = s.replace(P1_OLD, P1_NEW)
    s = s.replace("**Last updated**: 2026-11-11 (session 55 cont.", "**Last updated**: 2026-11-11 (session 55 cont.")
    return s


RB_OLD = "and two functions repaired by gluing misdecoded chunks (finding 144)"
RB_NEW = "and two functions repaired by gluing misdecoded chunks (finding 144), and 40 pure-split merged functions split (finding 145 batch 1)"


def rb(s):
    assert s.count(RB_OLD) == 1, "RB_OLD not found"
    return s.replace(RB_OLD, RB_NEW)


edit(ROOT + r"\docs\findings_log.md", log)
edit(ROOT + r"\status.md", status)
edit(ROOT + r"\docs\workflow\idb_regeneration.md", rb)
