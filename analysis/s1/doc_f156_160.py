"""doc_f156_160.py: document findings 156-160 (P1 batches 12-16, completing pure splits)."""
def edit(p, fn):
    s = open(p, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    s = fn(s)
    open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
    print("ok", p, crlf)

ROOT = r"C:\Users\ybarnoy\projects\falcon3"

LOG_ENTRY = """
## 2026-11-11 156 - P1 batch 12: split 4 pure-split merged functions (S1c-5l)

**What was done.**  4 splits: first level of the 4 remaining deep chains (mode_record_field_lookup,
farobj_pos_move_angle_step, farobj_move_accumulate_step, ems_entity_slot_script).  Skipped entries
carried over: 0x683C5 (ui_loadout_menu_enter/P5 cluster), 0x6E32A, 0x6E3D0 (R14, add_func fails),
0x12C683 (ADD conflict).  One more bug fixed: multi-level chained splits cannot all be in SPLIT at
once — the manifest-building loop runs before add_all creates intermediate functions; must do one level
per finding.  Results: functions 3,964 -> 3,968; backup `.bak_split156`.  Gates: INTACT, faithful.

## 2026-11-11 157 - P1 batch 13: split 4 pure-split merged functions (S1c-5m)

**What was done.**  Second level of the 4 deep chains: (0x4AB06, 0x4AC1E), (0x4B251, 0x4B2BD),
(0x4D230, 0x4D35A), (0x4ECAC, 0x4EE65).  Results: functions 3,968 -> 3,972; backup `.bak_split157`.
Gates: INTACT, faithful.

## 2026-11-11 158 - P1 batch 14: split 4 pure-split merged functions (S1c-5n)

**What was done.**  Third level: (0x4AC1E, 0x4AC5E), (0x4B2BD, 0x4B2EE), (0x4D35A, 0x4D38C),
(0x4EE65, 0x4EEB3).  farobj_move_accumulate_step and ems_entity_slot_script chains complete.
Results: functions 3,972 -> 3,976; backup `.bak_split158`.  Gates: INTACT, faithful.

## 2026-11-11 159 - P1 batch 15: split 2 pure-split merged functions (S1c-5o)

**What was done.**  Fourth level of two remaining chains: (0x4AC5E, 0x4AC80), (0x4B2EE, 0x4B327).
farobj_pos_move_angle_step chain complete.  Results: functions 3,976 -> 3,978; backup `.bak_split159`.
Gates: INTACT, faithful.

## 2026-11-11 160 - P1 batch 16: split 1 pure-split merged function (S1c-5p) — P1 COMPLETE

**What was done.**  Final split: (0x4AC80, 0x4ACC9) — last level of mode_record_field_lookup chain.
This completes ALL addressable pure-split merged functions.  Findings 145-160 collectively split 389
of the 394 pure-split targets; 5 were deferred (0x683C5/P5, 0x6E32A, 0x6E3D0/R14-fails,
0x12C683/ADD-conflict).  Results: functions 3,978 -> 3,979; backup `.bak_split160`.  Gates: INTACT,
faithful.

**P1 final numbers (after finding 160, survey_mid):**
- Functions: 3,979 (from 3,590 = +389 pure-split tails).
- Mid-body call targets: 140 / 327 sites (from 529 / 1,299):
  - merged_fn: 18 / 59 (from 407 / 1,031); 18 = 12 shared tails + 1 multi-chunk + 5 deferred.
  - not_head: 64 / 125 (unchanged).
  - fallthrough_entry_proloque: 26 / 48 (unchanged).
  - fallthrough_secondary_entry: 23 / 68 (unchanged).
  - other: 9 / 27 (unchanged).
- Orphan code: 96 runs / 221 B (92 are 1-2 B padding), unchanged.

**Next:** P2 (misdecodes), P3 (fall-in entries), P4 (other), P5 (handler cluster), etc.
"""

def log(s):
    return s.rstrip("\n") + "\n" + LOG_ENTRY

STATUS_OLD = "   - **S1c-5k (finding 155):**"
STATUS_NEW = """   - **S1c-5p (finding 160):** P1 COMPLETE: batch 16 (1 split, last mode_record_field_lookup level); functions 3,978 -> 3,979; backup `.bak_split160`.
     - **S1c-5o (finding 159):** P1 batch 15: 2 splits; functions 3,976 -> 3,978; backup `.bak_split159`.
     - **S1c-5n (finding 158):** P1 batch 14: 4 splits; functions 3,972 -> 3,976; backup `.bak_split158`.
     - **S1c-5m (finding 157):** P1 batch 13: 4 splits; functions 3,968 -> 3,972; backup `.bak_split157`.
     - **S1c-5l (finding 156):** P1 batch 12: 4 splits; fixed multi-level chain plan ordering; functions 3,964 -> 3,968; backup `.bak_split156`.
     - **S1c-5k (finding 155):**"""

NOW_OLD = "   - **Now (after finding 155, measured 2026-11-11):** 3,964 functions"
NOW_NEW = ("   - **Now (after finding 160, measured 2026-11-11):** 3,979 functions, ledger 2,034; "
           "140 mid-body targets / 327 sites\n     (18 merged = 12 shared tails + 1 multi-chunk + 5 deferred, "
           "64 misdecodes, 26+23 fall-in, 9 other); 96 orphan code runs / 221 B.\n     "
           "**P1 (pure splits) COMPLETE.**  5 targets deferred to P5 / later investigation.")

P1_OLD = "     - P1 split merged functions (in progress, batch 1 of ~10 done in finding 145; 354 pure-split targets remain);"
P1_NEW = "     - **P1 COMPLETE** (findings 145-160, 16 batches, 389 of 394 pure-split targets split; 5 deferred to P2/P5);"


def status(s):
    assert s.count(STATUS_OLD) == 1
    s = s.replace(STATUS_OLD, STATUS_NEW)
    assert s.count(NOW_OLD) == 1
    s = s.replace(NOW_OLD, NOW_NEW)
    assert s.count(P1_OLD) == 1
    s = s.replace(P1_OLD, P1_NEW)
    return s

RB_OLD = "and 374 pure-split merged functions split in eleven batches (findings 145-155)"
RB_NEW = "and 389 pure-split merged functions split in sixteen batches (findings 145-160; P1 complete)"

def rb(s):
    assert s.count(RB_OLD) == 1
    return s.replace(RB_OLD, RB_NEW)

edit(ROOT + r"\docs\findings_log.md", log)
edit(ROOT + r"\status.md", status)
edit(ROOT + r"\docs\workflow\idb_regeneration.md", rb)
