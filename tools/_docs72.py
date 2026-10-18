"""Record finding 72 (Global Level-1 COMPLETE: batches l1a-l1e = 149 named,
L1 queue 149 -> 0) in docs/findings_log.md (LF), time_log.yaml (CRLF),
status.md and docs/open_items.md (CRLF).  Idempotent + line-ending preserving."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-18 72 — Global Level-1 COMPLETE: 5 batches named all 149
Level-1 functions (`named` 815 -> 964), Level-1 `naming_queue` 149 -> 0

Finding 71 finished Level 0, which made Level 1 nameable **with full callee
context**: at Level 1, 142/149 queue entries already had **100% named
callees** (the rest call Level-1 SCC peers, named within the same batch).
`dump_level1.py` prints each target's callees' semantic names alongside the
disassembly -- the bottom-up method paying off.

### Cadence (5 batches: 36+36+36+36+5 = 149)

| batch | named after | L1 queue after | highlights |
|---|---|---|---|
| l1a | 851 | 113 | `record_op_dispatch_220b0` (cd=70,789), `view_rotation_build`, `angle_matrix_build_neg`, `adlib_detect_init` prep, SBI event writers (`sbi_midi_event_write`, `sbi_slot_scan_periodic`, `sbi_level_sync_*`) |
| l1b | 887 | 77 | `adlib_detect_init` (**in=18, hottest L1 fan-in**), `view_proj_rotation_build` (in=9), `dgroup_cycle_step_438`, `point_in_rect_6e8`, `r06_vec3_main_proc` (2,899B, largest L1), DOS file ops (`r01_file_create_3ch`, `module_open_3d00`) |
| l1c | 923 | 41 | `coord_delta_dispatch_13bba` (jump-table to 5 named coord-delta variants), `ems_state_bootstrap_2e100` (seeds the `flag_gate_zero_abc` flag!), `kbd_led_update_60h`, `vector_shutdown_restore` (INT 0/8/9 unhook), `sbi_config_triple_*` |
| l1d | 959 | 5 | `line_table_scan_dispatch` + 3 `line_flag_patch_*` + `uibounds_top_bottom_dispatch` (completing the line-table/UI-bound driver families), `anim_frame_step_clip`, `vector_shutdown` twins, `state_block_77720_*` commit trio |
| l1e | **964** | **0** | finale: `entity_event_0e_dispatch`, `r06_gate_4ac9`, `r17_dispatch_seq_2211c`, **`r53_record_walk_entry`** (the SCC partner of `r53_record_walk_main` -- `xor si,si; tail-jmp` loop-entry alias), `slope_far_call_driver` |

### MILESTONE: Level-1 naming_queue = 0

| metric | f71 | f72 |
|---|---|---|
| named (fb join) | 815 | **964 (+149)** |
| naming_queue (global) | 854 | **667** |
| **Level-1 queue** | **149** | **0** |

Level-1 residue = **42 orphans + 12 thunk slots, 0 other**. Global queue 667
remains (Levels 2..22).

### Notable findings from the callee context

* The **line-table / UI-bound driver family** resolved into a coherent set:
  `line_table_scan_dispatch` → `line_table_scan_20`/`_40` →
  `line_flag_patch_28f37/29075/291b1` → `line_table_entry_clone(_slope)` →
  `uibounds_left_right_dispatch` + `uibounds_top_bottom_dispatch` (all four
  edge presets now named).
* `ems_state_bootstrap_2e100` **seeds `cs:2E100` from `state_word_10219_get`**
  — closing the loop on `flag_gate_zero_abc`/`state_byte_2e100_zero` (f66/f71).
* The `r53` record-walk SCC: `r53_record_walk_main` <-> `r53_record_walk_entry`
  (a 2-instruction `xor si,si; tail-jmp` loop head) -- both named, cycle
  intact, invariant re-verified by the callgraph re-run.

### Gates (all green)

`naming.py check` **966** . `verify_rebuild` **faithful (2,237 == 2,237,
LOST 0, CHANGED 0)** . `verify_idb` **INTACT (0 span / 0 name / 0 data-hole
problems)** . `name_readback` **964/964 function + 2/2 global**.

---

"""

ROW = ("| 2026-10-18 (session 28) | ~4 h | **Finding 72: Global Level-1 "
       "COMPLETE -- 5 batches named 149 fns, `named` 815 -> 964, L1 queue "
       "**149 -> 0**.** Callee-context naming: 142/149 L1 entries had 100% "
       "NAMED callees at start (f71 payoff); dump_level1.py prints callee "
       "semantic names inline. Batches: l1a record_op_dispatch_220b0 "
       "(cd=70,789) + view_rotation_build + SBI event writers; l1b "
       "**adlib_detect_init (in=18 hottest L1)** + view_proj_rotation_build + "
       "r06_vec3_main_proc (2,899B) + DOS file ops; l1c "
       "coord_delta_dispatch_13bba (jumptable -> 5 named variants) + "
       "ems_state_bootstrap_2e100 (seeds cs:2E100, closes the flag_gate_zero_"
       "abc loop) + vector_shutdown_restore; l1d line-table/UI-bound driver "
       "family completed (scan_dispatch + 3 line_flag_patch + top_bottom "
       "presets) + state_block_77720 commit trio; l1e finale incl "
       "**r53_record_walk_entry** (SCC partner: xor si,si; tail-jmp loop "
       "alias). L1 residue = 42 orphans + 12 thunks, 0 other. Global queue "
       "667 (L2..22). **Gates green:** check 966, verify_rebuild faithful, "
       "verify_idb INTACT, read-back **964/964+2/2**. |")

STATUS_PARA = (
    "**Global Level-1 COMPLETE (finding 72):** 5 batches named **all 149 "
    "Level-1 functions** (`named` 815 → **964**) — **L1 `naming_queue` 149 → "
    "0**. The bottom-up method paid off: at batch start **142/149 L1 entries "
    "had 100% named callees**, and `dump_level1.py` printed each callee's "
    "semantic name inline. Highlights: `record_op_dispatch_220b0` "
    "(caller_dyn 70,789), `adlib_detect_init` (in=18, hottest L1 fan-in), the "
    "completed **line-table/UI-bound driver family** (`line_table_scan_dispatch` "
    "→ `line_flag_patch_*` → both UI-edge dispatch pairs), "
    "`ems_state_bootstrap_2e100` (seeds `cs:2E100` — closes the "
    "`flag_gate_zero_abc` loop), `coord_delta_dispatch_13bba` (jump-table to 5 "
    "named variants), `vector_shutdown_restore` (INT 0/8/9 unhook), and the "
    "**`r53_record_walk_main`↔`r53_record_walk_entry` SCC** (2-instruction "
    "`xor si,si; tail-jmp` loop head — cycle intact). L1 residue = 42 orphans "
    "+ 12 thunks, 0 other. **Gates all green** (check 966, verify_rebuild "
    "faithful, verify_idb INTACT, read-back **964/964+2/2**). Global "
    "naming_queue = 667 (Levels 2–22)."
)

OPEN_NEW = [
    "- **GLOBAL LEVEL 1 COMPLETE (finding 72):** 5 batches named all 149 L1",
    "  fns, `named` **815 -> 964**, **L1 queue 149 -> 0** (residue: 42",
    "  orphans + 12 thunks, 0 other). Callee-context naming validated (142/149",
    "  had 100% named callees at start). All 4 gates green (check 966,",
    "  verify_rebuild faithful, verify_idb INTACT, read-back 964/964+2/2).",
    "- **Next: Global Level-2 naming** (queue 667 across Levels 2..22). Same",
    "  cadence: dump_level1.py with FALCON_L1_TARGETS/TAG pointing at",
    "  level2_batchN_targets.json (extend sort to level==2), derive, append,",
    "  apply, push-ida, gates.  Level-2 callees are now 100% named (L0+L1).",
    "- **Follow-ups carried:** class-c / undecodable overlay spans (r14/r17/",
    "  r30 entry partials conf:low); 92 low-conf DATA fns; 24 trap-only",
    "  thunks; 397 global orphans stay excluded from bottom-up naming.",
]


def load(p):
    return io.open(p, encoding="utf-8", newline="").read()


def save(p, t):
    io.open(p, "w", encoding="utf-8", newline="").write(t)


# ---- docs/findings_log.md (LF) ----
p = "docs/findings_log.md"
raw = load(p)
if "## 2026-10-18 72" in raw:
    print("findings_log: 72 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 72 before footer (LF preserved)")

# ---- docs/time_log.yaml (CRLF) ----
p = "docs/time_log.yaml"
raw = load(p)
if "session 28" in raw:
    print("time_log: 28 already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 27" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 28 after line %d" % (idx + 1))

# ---- status.md (CRLF) ----
p = "status.md"
raw = load(p)
if "Global Level-1 COMPLETE (finding 72)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f72 para")

# ---- docs/open_items.md (CRLF) ----
p = "docs/open_items.md"
raw = load(p)
if "GLOBAL LEVEL 1 COMPLETE (finding 72)" in raw:
    print("open_items: already updated")
else:
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the f72 status (%d bytes)" % len(block))