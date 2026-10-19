"""Record finding 75 (Global Level-4 COMPLETE: 2 batches = 52 named,
L4 queue 54 -> 0, named 1111 -> 1163; PLUS Level-5 Batch 1: 36 named,
named -> 1199, L5 queue 60 -> 24) in docs/findings_log.md (LF),
time_log.yaml (CRLF), status.md and docs/open_items.md (CRLF).
Idempotent + line-ending preserving."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-19 75 — Global Level-4 COMPLETE (52 named) + Level-5
Batch 1 (36 named): `named` 1,111 -> **1,199**, L4 queue 54 -> 0,
L5 queue 60 -> 24

### Level-4 COMPLETE (36 + 16 = 52)

Same cadence as before (`dump_level1.py` disasm + `dump_full.py`
completions; 14 + 8 truncated bodies full-dumped).

| batch | named after | L4 queue after | highlights |
|---|---|---|---|
| l4a | 1,145 | 18 | **`angle_quad_norm_far`** (dyn=49,210 far stub into the L3 angle primitive), `clip_pending_apply_gate`/`_latch` (the 2549D-latch pair), **`overlay_segment_load`** (605B: chunked read + 0xA92 relocation fixups + chain), `kb_record_save_apply` (11-callee key-record save), `event_tone_key_play` (rate-limited), `sbi_channel_release_close`, `channel_release_close` pairs, `tile_strip_sample_draw` (in=23, 64-tile strip), `line_record_flag_dispatch` (record walker parent of line_record_draw_loop), `object_proj_draw_dispatch`, `farobj_slot_create`, `farobj_pos_wrap_update`, `error_display_terminate`, `r17_ui_event_loop` + `r69_ui_event_loop`, `r06_proximity_select`, `farobj_slot_step_spawn`, `farobj_entity_accum_sweep` |
| l4b | **1,163** | **0** | **`sbi_stream_next_advance`** (min-scan scheduler + cursor advance), `terrain_attr_quadrant_dispatch` + `_b` (8-/4-entry quadrant tables at cs:11C9A/11CA2), `record_queue_gather_drain`, `overlay_patch_verify`, `game_setup_ramp_accum` (7-phase ramp cap), `farobj_slot_create_gate`/`_ems`/`_status` (three gated creators), `scroll_decay_limit` (pair of game_setup_scroll_half_accum), `r17_screen_draw` + `_b`, `r12_cb_args_render`, `view_extent_shadow_save_far`/`_restore_far` thunks, `control_axis_step_quantize`, `op_2a780_release` |

L4 residue = 5 orphans + 18 thunks, **0 other**.

### Level-5 Batch 1 (36 of 60)

| named after | L5 queue after | highlights |
|---|---|---|
| **1,199** | **24** | **`op_dispatch_far_entry`** (in=30 -- the 5-arg far marshaller imported by r30/r32/r33/r35/r48), **`tail_bridge_overlay_load`** (in=302, cd=50,839 -- THE lazy-overlay landing pad every RTLink tail bridge crosses: queue slot + patch verify + overlay_segment_load), **`group_children_release`** (pair of group_register_main), **slot2/slot3 handle subsystem** (slot2_handle_alloc/release/read, slot3_handle_alloc_pair/release_pair, slot3_copy_ems_move with ems_page_move_67), `record_script_exec_main`/`_quad`/`_lite` (49-step 11C8C interpreters), `terrain_attr_scan_draw_a`/`_b` (scan+draw drivers for the quadrant dispatchers), the 4 `object_*_draw` render variants (`scale_gather`/`rot_proj`/`quad_proj`/`init_flag` -- same 6-caller render set), the twin movement engines **`pos_step_chain_engine`** (852B) + **`pos_move_angle_step`** (1,349B, mutually recursive, tile_quad_classify internal entries), `clip_pending_atomic_apply`, `channel_program_fetch_write`, `op_26400_record` (records the slot op_26400_release finalizes) |

### Gates (each milestone verified)

`naming.py check` **1,201** . `verify_rebuild` **faithful (2,237 ==
2,237)** . `verify_idb` **INTACT** . `name_readback` **1,199/1,199
function + 2/2 global**.

---

"""

ROW = ("| 2026-10-19 (session 31) | ~6 h | **Finding 75: Global Level-4 "
       "COMPLETE (2 batches, 52 fns: named 1,111 -> 1,163, L4 queue 54 -> 0, "
       "residue 5 orphans + 18 thunks) + Level-5 Batch 1 (36 fns: named -> "
       "**1,199**, L5 queue 60 -> 24).** L4a: angle_quad_norm_far (dyn=49,210 "
       "far stub), clip_pending_apply_gate/_latch pair, overlay_segment_load "
       "(605B chunked read + relocation fixups), kb_record_save_apply "
       "(11-callee), event_tone_key_play, sbi_channel_release_close, "
       "tile_strip_sample_draw (in=23), line_record_flag_dispatch, "
       "object_proj_draw_dispatch, r17/r69_ui_event_loop, farobj_slot_create, "
       "error_display_terminate, farobj_slot_step_spawn. L4b: "
       "sbi_stream_next_advance (min-scan scheduler), "
       "terrain_attr_quadrant_dispatch(+_b) quadrant tables, "
       "record_queue_gather_drain, overlay_patch_verify, "
       "farobj_slot_create_gate/_ems/_status trio, scroll_decay_limit, "
       "game_setup_ramp_accum, r17_screen_draw(+_b). L5b1: "
       "**op_dispatch_far_entry** (in=30 RTLink marshaller), "
       "**tail_bridge_overlay_load** (in=302, cd=50,839 lazy-overlay "
       "landing pad), group_children_release, slot2/slot3 handle subsystem "
       "(alloc/release/read + EMS chunk copy), record_script_exec "
       "main/quad/lite interpreters, terrain_attr_scan_draw_a/b, 4 "
       "object_*_draw variants, pos_step_chain_engine (852B) + "
       "pos_move_angle_step (1,349B mutual recursion), "
       "clip_pending_atomic_apply, op_26400_record. **Gates green:** check "
       "1,201, verify_rebuild faithful, verify_idb INTACT, read-back "
       "1199/1199+2/2. Global queue 522 -> 432 (L5=24, L6=60, L19=206). |")

STATUS_PARA = (
    "**Global Level-4 COMPLETE + Level-5 Batch 1 (finding 75):** two L4 "
    "batches named **all 52 Level-4 functions** (`named` 1,111 → **1,163**, "
    "**L4 `naming_queue` 54 → 0**, residue 5 orphans + 18 thunks, 0 other), "
    "then 36 more pushed Level-5's queue 60 → **24** and `named` to "
    "**1,199**. Structural wins: `angle_quad_norm_far` (dyn=49,210), "
    "`overlay_segment_load` (the full chunked loader with the 0xA92 "
    "relocation fixup pass), `sbi_stream_next_advance`, the "
    "`terrain_attr_quadrant_dispatch(+_b)` quadrant tables and their "
    "`terrain_attr_scan_draw_a/b` drivers, the `farobj_slot_create "
    "gate/ems/status` trio, and at L5: **`op_dispatch_far_entry`** (in=30 "
    "RTLink far marshaller) and **`tail_bridge_overlay_load`** (in=302, "
    "cd=50,839 -- the lazy-overlay landing pad every RTLink tail bridge "
    "crosses), the slot2/slot3 handle subsystem, the record-script "
    "executors, the four `object_*_draw` variants and the twin movement "
    "engines `pos_step_chain_engine`/`pos_move_angle_step`. **Gates all "
    "green** (check 1,201, verify_rebuild faithful, verify_idb INTACT, "
    "read-back **1,199/1,199 + 2/2**). Global naming_queue = 432 "
    "(L5=24, L6=60, …, L19=206)."
)

OPEN_NEW = [
    "- **GLOBAL LEVEL 4 COMPLETE + LEVEL-5 BATCH 1 (finding 75):** L4 = 52",
    "  fns named (queue 54 -> 0, 5 orphans + 18 thunks, 0 other); L5 = 36",
    "  of 60 named (queue 60 -> 24). `named` **1111 -> 1199**. Highlights:",
    "  angle_quad_norm_far (dyn=49,210), overlay_segment_load (reloc",
    "  fixups), sbi_stream_next_advance, quadrant dispatchers + scan draws,",
    "  op_dispatch_far_entry (in=30), tail_bridge_overlay_load (in=302,",
    "  cd=50,839), slot2/slot3 handle subsystem, record_script_exec trio,",
    "  pos_step_chain_engine + pos_move_angle_step. All 4 gates green (check",
    "  1201, verify_rebuild faithful, verify_idb INTACT, read-back",
    "  1199/1199+2/2).",
    "- **Next: finish Global Level-5** (24 targets, batch 2), then Level 6",
    "  (60) -- global queue 432 across L5..L21 (L19=206 giant SCC).",
    "- **Follow-ups carried:** class-c undecodable overlay spans (conf:low),",
    "  92 low-conf DATA fns, 24 trap-only thunks, 397 global orphans",
    "  excluded from bottom-up naming.",
]


def load(p):
    return io.open(p, encoding="utf-8", newline="").read()


def save(p, t):
    io.open(p, "w", encoding="utf-8", newline="").write(t)


# ---- docs/findings_log.md (LF) ----
p = "docs/findings_log.md"
raw = load(p)
if "## 2026-10-19 75" in raw:
    print("findings_log: 75 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 75 before footer (LF preserved)")

# ---- docs/time_log.yaml (CRLF) ----
p = "docs/time_log.yaml"
raw = load(p)
if "session 31" in raw:
    print("time_log: 31 already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 30" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 31 after line %d" % (idx + 1))

# ---- status.md (CRLF) ----
p = "status.md"
raw = load(p)
if "Global Level-4 COMPLETE + Level-5 Batch 1 (finding 75)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f75 para")

# ---- docs/open_items.md (CRLF) ----
p = "docs/open_items.md"
raw = load(p)
if "GLOBAL LEVEL 4 COMPLETE + LEVEL-5 BATCH 1 (finding 75)" in raw:
    print("open_items: already updated")
else:
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the f75 status (%d bytes)" % len(block))