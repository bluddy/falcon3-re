"""doc_f150.py: document finding 150 (P1 batch 6)."""
def edit(p, fn):
    s = open(p, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    s = fn(s)
    open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
    print("ok", p, crlf)

ROOT = r"C:\Users\ybarnoy\projects\falcon3"

LOG_ENTRY = """
## 2026-11-11 150 - P1 batch 6: split 40 more pure-split merged functions (S1c-5f)

**What was done.**  40 more `(owner, at)` pairs: continued multi-split chains plus new owners
(farobj_move_accumulate_step (9 splits), farobj_flag_dispatch_step, farobj_class16_record_ops,
farobj_slot_step_spawn, view_wrap_projection_entry (6 splits), ems_opstream_buffer_append,
overlay_teardown_restore_state, ems_stream_pointer_step (6 splits), farobj_slot_create_status,
farobj_cfg_step_control, store_cmd_interpreter).

**Results.** Functions 3,790 -> 3,830. Ledger 2,034 (unchanged).

**Applied.**  Plan, dry replay (40 fresh, 292 applied), backup `.bak_split150`, apply.  Idempotent replay
(332 applied, nothing to do).  Gates: integrity INTACT, naming OK (2034), verify_rebuild faithful
(SPLIT 119 sha256-pinned + ADDED 240 + LOST 0 + CHANGED 0 + REGISTER 169 applied).
"""

def log(s):
    return s.rstrip("\n") + "\n" + LOG_ENTRY

STATUS_OLD = "   - **S1c-5e (finding 149):**"
STATUS_NEW = """   - **S1c-5f (finding 150):** P1 batch 6: 40 more pure-split merges; functions 3,790 -> 3,830; backup `.bak_split150`.
     - **S1c-5e (finding 149):**"""

NOW_OLD = "   - **Now (after finding 149, measured 2026-11-11):** 3,790 functions"
NOW_NEW = "   - **Now (after finding 150, measured 2026-11-11):** 3,830 functions"

def status(s):
    assert s.count(STATUS_OLD) == 1
    s = s.replace(STATUS_OLD, STATUS_NEW)
    assert s.count(NOW_OLD) == 1
    return s.replace(NOW_OLD, NOW_NEW)

RB_OLD = "and 200 pure-split merged functions split in five batches (findings 145-149)"
RB_NEW = "and 240 pure-split merged functions split in six batches (findings 145-150)"

def rb(s):
    assert s.count(RB_OLD) == 1
    return s.replace(RB_OLD, RB_NEW)

edit(ROOT + r"\docs\findings_log.md", log)
edit(ROOT + r"\status.md", status)
edit(ROOT + r"\docs\workflow\idb_regeneration.md", rb)
