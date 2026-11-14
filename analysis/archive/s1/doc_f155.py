"""doc_f155.py: document finding 155 (P1 batch 11: 10 splits)."""
def edit(p, fn):
    s = open(p, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    s = fn(s)
    open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
    print("ok", p, crlf)

ROOT = r"C:\Users\ybarnoy\projects\falcon3"

LOG_ENTRY = """
## 2026-11-11 155 - P1 batch 11: split 10 pure-split merged functions (S1c-5k)

**What was done.**  10 more `(owner, at)` pairs: continued the four remaining deep chains
(mode_record_field_lookup, farobj_pos_move_angle_step, farobj_move_accumulate_step,
ems_entity_slot_script) plus single-split remainders
(viewport_strip_row_draw, hud_track_strip_pipeline, view_wrap_projection_entry,
ems_stream_pointer_step, entity_record_table_ops, r06_mode_dispatch_bx8).

**Results.** Functions 3,954 -> 3,964 (+10). Ledger 2,034 (unchanged).

**Applied.**  Plan, dry replay (10 fresh, 456 applied), backup `.bak_split155`, apply.  Idempotent replay
(466 applied, nothing to do).  Gates: integrity INTACT, naming OK (2034), verify_rebuild faithful
(SPLIT 151 sha256-pinned + ADDED 374 + LOST 0 + CHANGED 0 + REGISTER 170 applied).

**Still open in P1:** ~20 pure-split targets in ~10 owners remain (deepest tails of mode_record_field_lookup
and farobj_pos_move_angle_step chains).  Proceeding to batch 12.
"""

def log(s):
    return s.rstrip("\n") + "\n" + LOG_ENTRY

STATUS_OLD = "   - **S1c-5j (finding 154):**"
STATUS_NEW = """   - **S1c-5k (finding 155):** P1 batch 11: 10 splits; functions 3,954 -> 3,964; backup `.bak_split155`.
     - **S1c-5j (finding 154):**"""

NOW_OLD = "   - **Now (after finding 154, measured 2026-11-11):** 3,954 functions"
NOW_NEW = "   - **Now (after finding 155, measured 2026-11-11):** 3,964 functions"

def status(s):
    assert s.count(STATUS_OLD) == 1
    s = s.replace(STATUS_OLD, STATUS_NEW)
    assert s.count(NOW_OLD) == 1
    return s.replace(NOW_OLD, NOW_NEW)

RB_OLD = "and 364 pure-split merged functions split in ten batches (findings 145-154)"
RB_NEW = "and 374 pure-split merged functions split in eleven batches (findings 145-155)"

def rb(s):
    assert s.count(RB_OLD) == 1
    return s.replace(RB_OLD, RB_NEW)

edit(ROOT + r"\docs\findings_log.md", log)
edit(ROOT + r"\status.md", status)
edit(ROOT + r"\docs\workflow\idb_regeneration.md", rb)
