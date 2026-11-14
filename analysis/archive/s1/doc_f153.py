"""doc_f153.py: document finding 153 (P1 batch 9: 22 splits)."""
def edit(p, fn):
    s = open(p, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    s = fn(s)
    open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
    print("ok", p, crlf)

ROOT = r"C:\Users\ybarnoy\projects\falcon3"

LOG_ENTRY = """
## 2026-11-11 153 - P1 batch 9: split 22 pure-split merged functions (S1c-5i)

**What was done.**  22 more `(owner, at)` pairs: continued multi-split chains plus new owners
(nullsub_36 at 0x4EC42 — 1-byte stub split into 1 B + ems_entity_slot_script deep chain, R30 overlays:
ui_loadout_menu_enter excluded/deferred, r06 overlay entries, distance_tier_classify_entry).  Skipped
entries 0x683C5/0x6E32A/0x6E3D0/0x12C683 carried forward from batch 8.

Three more bugs found and fixed in `tools/apply_orphan_funcs.py` and `tools/verify_rebuild.py`:

1. **PLAN mode regenerated EXTEND entry after SPLIT**: when function 0x12C7C6 was split in batch 8, its
   end changed from 0x12C951 to 0x12C912.  The PLAN code for `EXTEND` items checked `f.end_ea == end`
   before re-using the manifest entry; since it now failed, a NEW entry was created with `before_end =
   0x12C912`, causing `extend` to call `set_func_end(0x12C7C6, 0x12C951)` on a probe that already had
   the split.  Fixed by always re-using the manifest entry when `ea in oldx` (regardless of `f.end_ea`).

2. **`ext_state` fresh/mismatch after EXTEND + SPLIT**: The standard `chunks_before / before_end`
   "fresh" check in `ext_state` used `f.end_ea == lo` where lo was the original `before_end`.  After
   SPLIT at some `at > lo`, `f.end_ea == at ≠ lo`, so "fresh" was not recognised and "mismatch" was
   returned.  Fixed (in finding 152's idempotent fix) by adding a preliminary "applied" branch:
   `sha(lo, hi) == run_sha256 and f.end_ea > lo`.

3. **register `expand_registered_splits` used planned post-split size for unapplied splits**: when the
   manifest contains a future split (batch N+1) but function_bytes.json is at batch N, the expansion
   set `want = (key, ea, sp["at"]-sp["ea"])` which doesn't match `now`.  Fixed to keep the original
   `sz2` when the tail function doesn't yet exist in `now`.

**Results.** Functions 3,915 -> 3,937 (+22). Ledger 2,034 (unchanged).

**Applied.**  Plan, dry replay (22 fresh, 417 applied), backup `.bak_split153`, apply.  Idempotent replay
(439 applied, nothing to do).  Gates: integrity INTACT, naming OK (2034), verify_rebuild faithful
(SPLIT 151 sha256-pinned + ADDED 347 + LOST 0 + CHANGED 0 + REGISTER 170 applied).

**Still open in P1:** ~47 pure-split targets remain (the probe found 26 owners / 69 splits, minus the
4 skipped = 65 splits, but each batch 9 owner has remaining tails from the split chains).  Next probe
will show the accurate remaining count.
"""

def log(s):
    return s.rstrip("\n") + "\n" + LOG_ENTRY

STATUS_OLD = "   - **S1c-5h (finding 152):**"
STATUS_NEW = """   - **S1c-5i (finding 153):** P1 batch 9: 22 splits (3 bugs fixed in tools); functions 3,915 -> 3,937; backup `.bak_split153`.
     - **S1c-5h (finding 152):**"""

NOW_OLD = "   - **Now (after finding 152, measured 2026-11-11):** 3,915 functions"
NOW_NEW = "   - **Now (after finding 153, measured 2026-11-11):** 3,937 functions"

def status(s):
    assert s.count(STATUS_OLD) == 1
    s = s.replace(STATUS_OLD, STATUS_NEW)
    assert s.count(NOW_OLD) == 1
    return s.replace(NOW_OLD, NOW_NEW)

RB_OLD = "and 325 pure-split merged functions split in eight batches (findings 145-152)"
RB_NEW = "and 347 pure-split merged functions split in nine batches (findings 145-153)"

def rb(s):
    assert s.count(RB_OLD) == 1
    return s.replace(RB_OLD, RB_NEW)

edit(ROOT + r"\docs\findings_log.md", log)
edit(ROOT + r"\status.md", status)
edit(ROOT + r"\docs\workflow\idb_regeneration.md", rb)
