"""doc_f152.py: document finding 152 (P1 batch 8: 45 splits, with skips and bug fixes)."""
def edit(p, fn):
    s = open(p, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    s = fn(s)
    open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
    print("ok", p, crlf)

ROOT = r"C:\Users\ybarnoy\projects\falcon3"

LOG_ENTRY = """
## 2026-11-11 152 - P1 batch 8: split 45 pure-split merged functions (S1c-5h)

**What was done.**  48 owners attempted; 45 splits applied.  Three entries were skipped:

- `(0x683C5, 0x6940B)`: `ui_loadout_menu_enter` tail is only 3 bytes and belongs to the deferred P5 handler
  cluster (0x6E696..0x6E8B7); `add_func 0x6940B..0x6940E` fails.
- `(0x6E32A, 0x6E36F)` and `(0x6E3D0, 0x6E404)`: R14 overlay entries; `add_func` fails at tails.
- `(0x12C683, 0x12C764)`: `sub_12C683` is also in the ADD list (finding 128); SPLIT after ADD
  creates a "mismatch" in the ADD state check.

Three bugs found and fixed:

1. **SPLIT ran before EXTEND in `add_all`**: caused `ext_state` to fail for the extended function at
   0x12C7C6 (in EXTEND_RUNS) which we're also splitting in this batch.  Fixed by moving the SPLIT loop
   to run AFTER EXTEND in `add_all`.  Also cleaned up a doubled SPLIT loop and a wrong `trim_state` on
   the REBASE loop, introduced by an earlier edit.

2. **`ext_state` was too strict after extension + split**: required `f.end_ea == x["end"]` but the
   function's end shrinks when split further.  Fixed to also return "applied" when the bytes of the
   extended run are unchanged and `f.end_ea > run_lo` (the extension happened, possibly followed by a
   split).

**Results.** Functions 3,870 -> 3,915 (+45 tail functions). Ledger 2,034 (unchanged).

**Applied.**  Plan (45 fresh), dry replay, backup `.bak_split152`, apply.  Idempotent replay (417 applied,
nothing to do — after ext_state fix).  Gates: integrity INTACT, naming OK (2034), verify_rebuild faithful
(SPLIT 151 sha256-pinned + ADDED 325 + LOST 0 + CHANGED 0 + REGISTER 170 applied).

**Still open in P1:** ~65 pure-split targets in ~25 owners remain (the R14 and 0x683C5 cases are deferred).
"""

def log(s):
    return s.rstrip("\n") + "\n" + LOG_ENTRY

STATUS_OLD = "   - **S1c-5g (finding 151):**"
STATUS_NEW = """   - **S1c-5h (finding 152):** P1 batch 8: 45 splits (3 skipped: deferred P5/R14 cases + ADD conflict); fixed add_all ordering and ext_state; functions 3,870 -> 3,915; backup `.bak_split152`.
     - **S1c-5g (finding 151):**"""

NOW_OLD = "   - **Now (after finding 151, measured 2026-11-11):** 3,870 functions"
NOW_NEW = "   - **Now (after finding 152, measured 2026-11-11):** 3,915 functions"

def status(s):
    assert s.count(STATUS_OLD) == 1
    s = s.replace(STATUS_OLD, STATUS_NEW)
    assert s.count(NOW_OLD) == 1
    return s.replace(NOW_OLD, NOW_NEW)

RB_OLD = "and 280 pure-split merged functions split in seven batches (findings 145-151)"
RB_NEW = "and 325 pure-split merged functions split in eight batches (findings 145-152)"

def rb(s):
    assert s.count(RB_OLD) == 1
    return s.replace(RB_OLD, RB_NEW)

edit(ROOT + r"\docs\findings_log.md", log)
edit(ROOT + r"\status.md", status)
edit(ROOT + r"\docs\workflow\idb_regeneration.md", rb)
