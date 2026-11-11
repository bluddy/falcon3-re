"""doc_f148.py: document finding 148 (P1 batch 4)."""
def edit(p, fn):
    s = open(p, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    s = fn(s)
    open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
    print("ok", p, crlf)

ROOT = r"C:\Users\ybarnoy\projects\falcon3"

LOG_ENTRY = """
## 2026-11-11 148 - P1 batch 4: split 40 more pure-split merged functions (S1c-5d)

**What was done.**  40 more `(owner, at)` pairs: continued multi-split chains (control_axes_read,
dgroup_state_cycle_step, farobj_* chains) plus new large owners (hud_track_distance_draw,
ui_slot_filter_predicate, farobj_entity_*, hud_state_rowtable_step, game_setup_staged_init,
viewport_strip_row_draw, hud_readout_timer_render, hud_track_strip_pipeline, sprite_delta_project_47686,
r32_hud_phase_dispatch, hud_rowlist_timer_step, hud_panel_transform_step, record_script_coord_entry,
viewport_bounds_setup, target_cycle_scan, tile_grid_scan_step, aircraft_record_load_step,
store_fall_sim_step).

**Results.** Functions 3,710 -> 3,750. Ledger 2,034 (unchanged).

**Applied.**  Plan, dry replay (40 fresh, 212 applied), backup `.bak_split148`, apply.  Idempotent replay
(252 applied, nothing to do).  Gates: integrity INTACT, naming OK (2034), verify_rebuild faithful
(SPLIT 97 sha256-pinned + ADDED 160 + LOST 0 + CHANGED 0 + REGISTER 168 applied).
"""

def log(s):
    return s.rstrip("\n") + "\n" + LOG_ENTRY

STATUS_OLD = "   - **S1c-5c (finding 147):**"
STATUS_NEW = """   - **S1c-5d (finding 148):** P1 batch 4: 40 more pure-split merges; functions 3,710 -> 3,750; backup `.bak_split148`.
     - **S1c-5c (finding 147):**"""

NOW_OLD = "   - **Now (after finding 147, measured 2026-11-11):** 3,710 functions"
NOW_NEW = "   - **Now (after finding 148, measured 2026-11-11):** 3,750 functions"

def status(s):
    assert s.count(STATUS_OLD) == 1
    s = s.replace(STATUS_OLD, STATUS_NEW)
    assert s.count(NOW_OLD) == 1
    return s.replace(NOW_OLD, NOW_NEW)

RB_OLD = "and 120 pure-split merged functions split in three batches (findings 145-147)"
RB_NEW = "and 160 pure-split merged functions split in four batches (findings 145-148)"

def rb(s):
    assert s.count(RB_OLD) == 1
    return s.replace(RB_OLD, RB_NEW)

edit(ROOT + r"\docs\findings_log.md", log)
edit(ROOT + r"\status.md", status)
edit(ROOT + r"\docs\workflow\idb_regeneration.md", rb)
