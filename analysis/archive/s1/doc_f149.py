"""doc_f149.py: document finding 149 (P1 batch 5)."""
def edit(p, fn):
    s = open(p, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    s = fn(s)
    open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
    print("ok", p, crlf)

ROOT = r"C:\Users\ybarnoy\projects\falcon3"

LOG_ENTRY = """
## 2026-11-11 149 - P1 batch 5: split 40 more pure-split merged functions (S1c-5e)

**What was done.**  40 more `(owner, at)` pairs: continued multi-split chains plus new large owners
(entity_spawn_from_tile, mode_record_field_lookup (12 splits!), ui_aircraft_slot_step, farobj_pos_move_angle_step
(11 splits), sprite_step_clip_project_body, pos_state_block_read, tile_object_interpreter, farobj_tile_key_cache,
farobj_table_init_69ff, farobj_queue_drain_dispatch, farobj_record_flag_ops).

**Results.** Functions 3,750 -> 3,790. Ledger 2,034 (unchanged).

**Applied.**  Plan, dry replay (40 fresh, 252 applied), backup `.bak_split149`, apply.  Idempotent replay
(292 applied, nothing to do).  Gates: integrity INTACT, naming OK (2034), verify_rebuild faithful
(SPLIT 108 sha256-pinned + ADDED 200 + LOST 0 + CHANGED 0 + REGISTER 168 applied).
"""

def log(s):
    return s.rstrip("\n") + "\n" + LOG_ENTRY

STATUS_OLD = "   - **S1c-5d (finding 148):**"
STATUS_NEW = """   - **S1c-5e (finding 149):** P1 batch 5: 40 more pure-split merges; functions 3,750 -> 3,790; backup `.bak_split149`.
     - **S1c-5d (finding 148):**"""

NOW_OLD = "   - **Now (after finding 148, measured 2026-11-11):** 3,750 functions"
NOW_NEW = "   - **Now (after finding 149, measured 2026-11-11):** 3,790 functions"

def status(s):
    assert s.count(STATUS_OLD) == 1
    s = s.replace(STATUS_OLD, STATUS_NEW)
    assert s.count(NOW_OLD) == 1
    return s.replace(NOW_OLD, NOW_NEW)

RB_OLD = "and 160 pure-split merged functions split in four batches (findings 145-148)"
RB_NEW = "and 200 pure-split merged functions split in five batches (findings 145-149)"

def rb(s):
    assert s.count(RB_OLD) == 1
    return s.replace(RB_OLD, RB_NEW)

edit(ROOT + r"\docs\findings_log.md", log)
edit(ROOT + r"\status.md", status)
edit(ROOT + r"\docs\workflow\idb_regeneration.md", rb)
