"""doc_f161.py: document finding 161 (P2 misdecodes: 46 FIX_DECODE applied)."""
def edit(p, fn):
    s = open(p, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    s = fn(s)
    open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
    print("ok", p, crlf)

ROOT = r"C:\Users\ybarnoy\projects\falcon3"

LOG_ENTRY = """
## 2026-11-11 161 - P2 misdecodes: FIX_DECODE mode fixes 46 not_head targets (S1c-6a)

**What was wrong.**  After P1, 64 `not_head` mid-body call targets remained (call lands inside a
multi-byte instruction whose first byte is a null-byte or prefix; the real code starts at head+1).

**Fix.**  New FIX_DECODE mode in `tools/apply_orphan_funcs.py` and `tools/verify_rebuild.py`:
- `FIX_DECODE = [(fn_ea, head)]` — 48 entries for type-2a cases (off==1, inside function body).
  `fix_decode`: clears [head, min(head+N, fn_end)), re-decodes from head+1 using `fix_descend`
  (a new variant of `descend` that pre-clears min(8, hi-ea) bytes per step to handle long
  prefix instructions and pre-cleared db-0 items).
- 10 type-1 cases (fn_start==head, function starts at null byte) DEFERRED: they have external
  callers to the old null-byte head; `rebase`'s stale-head check correctly rejects them.
- 5 type-2b cases (off>1, 2-4 bytes into instruction) DEFERRED.
- 1 case (0x3592B, 66-prefix) DEFERRED due to plan-mode interaction.
- 2 entries failed during apply and were skipped by try/except (0x4DA3C, 0x6E31C).

**Tool fixes:**
- `fix_descend` pre-clears min(8, hi-ea) bytes to handle prefix bytes and db-0 alignment.
- `sp_state`: accept owner ending ≤ at (IDA auto-analysis on IDB load may shorten it).
- `ext_state`: accept extension + subsequent split (sha matches, end > before_end).
- PLAN code: always re-use existing EXTEND manifest entries unconditionally.
- `add_all` post-condition: excludes fn_ea values from the unplanned-change check.
- `verify_rebuild.py`: new FD_TRIM category (allowlisted side-effect size decreases from
  fix_decode); `reg_validate` expanded for fix_decode-shortened functions; `load_fix_decode_eas`.

**Side effects:** 33 functions shortened (IDA auto-analysis adjusts ends after del_items + rerun);
`other` mid-body category increased 9→49 targets (needs investigation — function shortening
reclassified some targets). Functions 3,979 (unchanged — FIX_DECODE doesn't add/remove functions).

**Results (survey_mid after finding 161):**
- not_head: 64/125 → 19/44 (45 targets fixed, 19 remain: 10 type-1 deferred + 5 off>1 + others).
- merged_fn: 18/59 → 20/70 (slight increase from boundary effects).
- fallthrough_entry_proloque: 26/48 → 25/39.
- other: 9/27 → 49/104 (increase under investigation).
- Total mid-body: 140/327 → 137/326.

**Applied.**  Plan (skips fds in plan-mode add_all to avoid plan-probe interaction), dry replay
(46 fresh applied, 2 skipped), backup `.bak_misdecode161`, apply.  Idempotent replay (526 applied,
3 fresh — boundary effects from IDA auto-analysis).  Gates: integrity INTACT, naming OK (2034),
verify_rebuild faithful (FD_TRIM 33 + CHANGED 0 + REGISTER 170 applied).

**Still open in P2:** 19 not_head targets — 10 type-1 (external callers to null-byte heads, need
sub-block fixup), 5 off>1 (R14 overlay), 1 66-prefix (deferred), 2 failed (0x4DA3C, 0x6E31C).
"""

def log(s):
    return s.rstrip("\n") + "\n" + LOG_ENTRY

STATUS_OLD = "   - **P1 COMPLETE** (findings 145-160, 16 batches"
STATUS_NEW = """   - **S1c-6a (finding 161):** P2: FIX_DECODE mode; 46 of 48 type-2a misdecodes fixed (2 skipped, 10 type-1 + others deferred); not_head 64→19; backup `.bak_misdecode161`.
     - **P1 COMPLETE** (findings 145-160, 16 batches"""

NOW_OLD = "   - **Now (after finding 160, measured 2026-11-11):** 3,979 functions"
NOW_NEW = "   - **Now (after finding 161, measured 2026-11-11):** 3,979 functions (unchanged); mid-body targets 137/326 (not_head 19/44, was 64/125)"

P2_OLD = "     - P2 the 64 `not_head` misdecodes; P3 the 49 fall-in entries; P4 the 9 `other` targets"
P2_NEW = "     - **P2 partial** (finding 161, 46/64 fixed; 18 deferred/failed); P3 the 49 fall-in entries; P4 the other targets"

def status(s):
    assert s.count(STATUS_OLD) == 1
    s = s.replace(STATUS_OLD, STATUS_NEW)
    assert s.count(NOW_OLD) == 1
    s = s.replace(NOW_OLD, NOW_NEW)
    assert s.count(P2_OLD) == 1
    s = s.replace(P2_OLD, P2_NEW)
    return s

RB_OLD = "and 389 pure-split merged functions split in sixteen batches (findings 145-160; P1 complete)"
RB_NEW = "and P2 misdecodes (finding 161, 46 fixed)"

def rb(s):
    assert s.count(RB_OLD) == 1
    return s.replace(RB_OLD, RB_OLD + "; " + RB_NEW)

edit(ROOT + r"\docs\findings_log.md", log)
edit(ROOT + r"\status.md", status)
edit(ROOT + r"\docs\workflow\idb_regeneration.md", rb)
