"""doc_f147.py: document finding 147 (P1 batch 3: 40 more pure-split merges)."""
def edit(p, fn):
    s = open(p, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    s = fn(s)
    open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
    print("ok", p, crlf)

ROOT = r"C:\Users\ybarnoy\projects\falcon3"

LOG_ENTRY = """
## 2026-11-11 147 - P1 batch 3: split 40 more pure-split merged functions (S1c-5c)

**What was done.**  40 more `(owner, at)` pairs: second-level tails of batch-2 owners (sub_12320,
sub_22436, sub_30610, etc.) plus new R05_2B83 suite (farobj_view_project_step, farobj_angle_distance_gate,
hud_data_panel_slot_mgr, farobj_class_table_entry, farobj_state_flag_set, farobj_range_slot_init,
farobj_flag_or_set, farobj_index_state_swap, hud_object_text_format, farobj_selection_window_step,
mode_phase_apply_state, farobj_thrust_burn_step, farobj_fuel_apply_step, farobj_matrix_project_copy).

**Bug fixed.**  `reg_validate` expansion in `verify_rebuild.py` was using `sp["end"]-sp["ea"] == sz2` to
detect splits, which failed for tails added to `to_expand` (their sz2 is the CURRENT size, smaller than
original). Fixed to look up the owner's current size from `now` and always follow the tail when
`split_funcs` has an entry for the ea AND the tail function exists in `now`.  This makes the cascade
correct for arbitrarily deep split chains.

**Results.** Functions 3,670 -> 3,710. Ledger 2,034 (unchanged).

**Applied.**  Plan, dry replay (40 fresh, 172 applied), backup `.bak_split147`, apply.  Idempotent replay
(212 applied, nothing to do).  Gates: integrity INTACT, naming OK (2034), verify_rebuild faithful
(SPLIT 78 sha256-pinned + ADDED 120 + LOST 0 + CHANGED 0 + REGISTER 166 applied).
"""

def log(s):
    return s.rstrip("\n") + "\n" + LOG_ENTRY

STATUS_OLD = "   - **S1c-5b (finding 146):**"
STATUS_NEW = """   - **S1c-5c (finding 147):** P1 batch 3: 40 more pure-split merges; fixed reg_validate cascade for multi-level splits; functions 3,670 -> 3,710; backup `.bak_split147`.
     - **S1c-5b (finding 146):**"""

NOW_OLD = "   - **Now (after finding 146, measured 2026-11-11):** 3,670 functions"
NOW_NEW = "   - **Now (after finding 147, measured 2026-11-11):** 3,710 functions"

def status(s):
    assert s.count(STATUS_OLD) == 1
    s = s.replace(STATUS_OLD, STATUS_NEW)
    assert s.count(NOW_OLD) == 1
    return s.replace(NOW_OLD, NOW_NEW)

RB_OLD = "and 80 pure-split merged functions split in two batches (findings 145-146)"
RB_NEW = "and 120 pure-split merged functions split in three batches (findings 145-147)"

def rb(s):
    assert s.count(RB_OLD) == 1
    return s.replace(RB_OLD, RB_NEW)

edit(ROOT + r"\docs\findings_log.md", log)
edit(ROOT + r"\status.md", status)
edit(ROOT + r"\docs\workflow\idb_regeneration.md", rb)
