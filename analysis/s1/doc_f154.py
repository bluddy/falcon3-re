"""doc_f154.py: document finding 154 (P1 batch 10: 17 splits)."""
def edit(p, fn):
    s = open(p, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    s = fn(s)
    open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
    print("ok", p, crlf)

ROOT = r"C:\Users\ybarnoy\projects\falcon3"

LOG_ENTRY = """
## 2026-11-11 154 - P1 batch 10: split 17 pure-split merged functions (S1c-5j)

**What was done.**  17 more `(owner, at)` pairs: continued multi-split chains (mode_record_field_lookup
7 more, farobj_pos_move_angle_step 6 more, farobj_move_accumulate_step 5 more, ems_entity_slot_script
5 more) plus remaining tails (record_script_coord_entry, tile_grid_scan_step, ui_aircraft_slot_step,
tile_object_interpreter, view_wrap_projection_entry, ems_stream_pointer_step, entity_record_table_ops,
angle_fixed_rotate_apply, ui_slot_count_tally, r06_ui_dispatch_block, r06_mode_dispatch_bx8,
viewport_strip_row_draw, hud_track_strip_pipeline).

**Results.** Functions 3,937 -> 3,954 (+17). Ledger 2,034 (unchanged).

**Applied.**  Plan, dry replay (17 fresh, 439 applied), backup `.bak_split154`, apply.  Idempotent replay
(456 applied, nothing to do).  Gates: integrity INTACT, naming OK (2034), verify_rebuild faithful
(SPLIT 151 sha256-pinned + ADDED 364 + LOST 0 + CHANGED 0 + REGISTER 170 applied).

**Still open in P1:** last batch probe shows ~30 more splits in ~17 owners (deepest part of the
mode_record_field_lookup and farobj_pos_move_angle_step chains).  Proceeding to batch 11.
"""

def log(s):
    return s.rstrip("\n") + "\n" + LOG_ENTRY

STATUS_OLD = "   - **S1c-5i (finding 153):**"
STATUS_NEW = """   - **S1c-5j (finding 154):** P1 batch 10: 17 splits; functions 3,937 -> 3,954; backup `.bak_split154`.
     - **S1c-5i (finding 153):**"""

NOW_OLD = "   - **Now (after finding 153, measured 2026-11-11):** 3,937 functions"
NOW_NEW = "   - **Now (after finding 154, measured 2026-11-11):** 3,954 functions"

def status(s):
    assert s.count(STATUS_OLD) == 1
    s = s.replace(STATUS_OLD, STATUS_NEW)
    assert s.count(NOW_OLD) == 1
    return s.replace(NOW_OLD, NOW_NEW)

RB_OLD = "and 347 pure-split merged functions split in nine batches (findings 145-153)"
RB_NEW = "and 364 pure-split merged functions split in ten batches (findings 145-154)"

def rb(s):
    assert s.count(RB_OLD) == 1
    return s.replace(RB_OLD, RB_NEW)

edit(ROOT + r"\docs\findings_log.md", log)
edit(ROOT + r"\status.md", status)
edit(ROOT + r"\docs\workflow\idb_regeneration.md", rb)
