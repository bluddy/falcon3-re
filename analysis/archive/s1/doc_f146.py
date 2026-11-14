"""doc_f146.py: document finding 146 (P1 batch 2: 40 more pure-split merges)."""
def edit(p, fn):
    s = open(p, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    s = fn(s)
    open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
    print("ok", p, crlf)


ROOT = r"C:\Users\ybarnoy\projects\falcon3"

LOG_ENTRY = """
## 2026-11-11 146 - P1 batch 2: split 40 more pure-split merged functions (S1c-5b)

**What was wrong.**  After finding 145, 354 pure-split targets remained in 133 owners.  Batch 2 takes the
next 40 by address: second splits of batch-1 tail functions (sub_100C1, sub_22846, etc.) plus new owners
from R05_1F64 and R05_2ACF (sprite_project_screen_y, pos_move_angle_step, pos_step_chain_engine,
tile_quad_classify, farobj_* suite).

**Fix.**  40 more `(owner, at)` pairs appended to `SPLIT` in finding 146 batch block.  Three bugs found and
fixed in the process:

1. **sp_state was too strict on the applied check**: required `get_func(at).end_ea == end`, but tails from
   earlier batches get split further by later batches.  Fixed to only require a function starts at `at`.

2. **verify_rebuild.py is_expected_split was too strict on the tail sha256**: required the tail function's
   exact size to match.  Fixed to just check that some function starts at `x["at"]`.

3. **reg_validate in verify_rebuild.py became stale**: batch 2 split functions that were in REGISTER
   manifests, invalidating their exact (key, ea, size) tuples.  Fixed `reg_validate` to recursively
   expand split owners in `want` using `split_funcs` before comparing to `have`; tiling check is skipped
   when expansion occurred (tiling is implied by `have == expanded_want`).  This fix applies to all future
   batches automatically.

**Results.**
- Functions 3,630 -> 3,670 (+40 new tail functions).
- Ledger 2,034 (unchanged).
- Survey_mid not re-run (finding 145 numbers still approximately correct for the whole batch 1+2 picture;
  will re-run before documenting batch 3).

**Applied.**  Plan (40 fresh, 132 applied), dry replay (40 fresh, 132 applied — concurrent with plan,
ran against updated manifest), backup `.bak_split146`, apply.  Fixed sp_state + is_expected_split + reg_validate.
Idempotent replay (172 applied, 0 fresh — after sp_state fix).  Gates: integrity INTACT, naming OK (2034),
verify_rebuild faithful (SPLIT 62 + ADDED 80 + LOST 0 + CHANGED 0 + REGISTER 166 applied).
"""


def log(s):
    return s.rstrip("\n") + "\n" + LOG_ENTRY


STATUS_OLD = "   - **S1c-5a (finding 145):**"
STATUS_NEW = """   - **S1c-5b (finding 146):** P1 batch 2: 40 more pure-split merged functions; fixed sp_state,
       is_expected_split, and reg_validate for multi-batch splits; functions 3,630 -> 3,670; backup `.bak_split146`.
     - **S1c-5a (finding 145):**"""

NOW_OLD = "   - **Now (after finding 145, measured 2026-11-11):** 3,630 functions"
NOW_NEW = "   - **Now (after finding 146, measured 2026-11-11):** 3,670 functions"


def status(s):
    assert s.count(STATUS_OLD) == 1, "STATUS_OLD"
    s = s.replace(STATUS_OLD, STATUS_NEW)
    assert s.count(NOW_OLD) == 1, "NOW_OLD"
    return s.replace(NOW_OLD, NOW_NEW)


RB_OLD = "and 40 pure-split merged functions split (finding 145 batch 1)"
RB_NEW = "and 80 pure-split merged functions split in two batches (findings 145-146)"


def rb(s):
    assert s.count(RB_OLD) == 1, "RB_OLD"
    return s.replace(RB_OLD, RB_NEW)


edit(ROOT + r"\docs\findings_log.md", log)
edit(ROOT + r"\status.md", status)
edit(ROOT + r"\docs\workflow\idb_regeneration.md", rb)
