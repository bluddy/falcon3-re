"""doc_f151.py: document finding 151 (P1 batch 7)."""
def edit(p, fn):
    s = open(p, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    s = fn(s)
    open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
    print("ok", p, crlf)

ROOT = r"C:\Users\ybarnoy\projects\falcon3"

LOG_ENTRY = """
## 2026-11-11 151 - P1 batch 7: split 40 more pure-split merged functions (S1c-5g)

**What was done.**  40 more `(owner, at)` pairs: multi-split chain continuations plus new owners
(ems_opstream_table_flush, ems_entity_slot_script (8 splits), ems_state_flags_709f, entity_record_table_ops
(5 splits), vga_dac_palette_upload, farobj_cfg_gate_85059, view_pos_cache_update, sprite_blend_0ad2d,
terrain_vm_blend_apply, palette_delta_blend, hw_cfg_copy_a76f, hw_flag_85052_set_ff).

**Results.** Functions 3,830 -> 3,870. Ledger 2,034 (unchanged).

**Applied.**  Plan, dry replay (40 fresh, 332 applied), backup `.bak_split151`, apply.  Idempotent replay
(372 applied, nothing to do).  Gates: integrity INTACT, naming OK (2034), verify_rebuild faithful
(SPLIT 131 sha256-pinned + ADDED 280 + LOST 0 + CHANGED 0 + REGISTER 170 applied).
"""

def log(s):
    return s.rstrip("\n") + "\n" + LOG_ENTRY

STATUS_OLD = "   - **S1c-5f (finding 150):**"
STATUS_NEW = """   - **S1c-5g (finding 151):** P1 batch 7: 40 more pure-split merges; functions 3,830 -> 3,870; backup `.bak_split151`.
     - **S1c-5f (finding 150):**"""

NOW_OLD = "   - **Now (after finding 150, measured 2026-11-11):** 3,830 functions"
NOW_NEW = "   - **Now (after finding 151, measured 2026-11-11):** 3,870 functions"

def status(s):
    assert s.count(STATUS_OLD) == 1
    s = s.replace(STATUS_OLD, STATUS_NEW)
    assert s.count(NOW_OLD) == 1
    return s.replace(NOW_OLD, NOW_NEW)

RB_OLD = "and 240 pure-split merged functions split in six batches (findings 145-150)"
RB_NEW = "and 280 pure-split merged functions split in seven batches (findings 145-151)"

def rb(s):
    assert s.count(RB_OLD) == 1
    return s.replace(RB_OLD, RB_NEW)

edit(ROOT + r"\docs\findings_log.md", log)
edit(ROOT + r"\status.md", status)
edit(ROOT + r"\docs\workflow\idb_regeneration.md", rb)
