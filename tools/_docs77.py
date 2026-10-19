"""Record finding 77 (Global Level-6 COMPLETE: 2 batches = 60 named,
L6 queue 60 -> 0, named 1223 -> 1283) in docs/findings_log.md (LF),
time_log.yaml (CRLF), status.md and docs/open_items.md (CRLF).
Idempotent + line-ending preserving."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-19 77 — Global Level-6 COMPLETE: 2 batches named all 60
Level-6 functions (`named` 1,223 -> **1,283**), L6 queue 60 -> 0

Finding 76 closed Level 5. This finding delivers all of Level 6 in two
batches (36 + 24); 13 + 5 truncated bodies were full-dumped
(`dump_full.py`).

| batch | named after | L6 queue after | highlights |
|---|---|---|---|
| l6a (this, part 1) | 1,259 | 24 | `r17_event_main_loop` (R17 main: 4-key table -> menu/router loops), `sbi_channel_event_dispatch` (1286B SBI classxchannel interpreter), slot3 mask transaction (`slot3_mask_rebuild` + `op_slot_mask_release`), slot2 map window (`slot2_map_window_load`/`_read` + `slot2_map_window` family), object draw-step family (`object_view_matrix_build`, `object_record_stream_step`, `object_type3_table_step`, `object_type_field_step`, `object_frame_advance_step`), `entity_record_table_build` + `entity_slot_create`, HUD panel set (`hud_data_panel_draw`, `hud_rowlist_panel_draw`, `hud_dualvalue_panel_draw`, `hud_timer_countdown_draw`, `hud_field0c_value_draw`, `hud_field14_value_draw`), record-script trio (`record_script_coord_dispatch`, `record_script_tilepos_dispatch`, `record_script_slots_run`), `hw_config_flags_build` (55E4E feature bitfield), `state_bits_pack`/`state_bits_unpack`, `terrain_point_project_store`, `farobj_sweep_all`, `pos_move_angle_gate`, `mode_slot_index_build`, `far_op_execute_farptr`, `channel_widen_forward_apply`, `op_cstring_bank_load`, `kb_record_slots_release`, `group_children_release_all`/`_dynamic`, `flag_quad_state_clear` |
| l6b (this, part 2) | **1,283** | **0** | **`r06_mode_step_dispatch`** (bx-indexed call table + mode-init/change-detect entries), keyboard record pipeline (**`kb_record_slots_open`**/**`kb_record_slots_write`** + `kb_record_far_write` / `kb_record_delta_write` / `kb_stream_far_write` / `kb_preset_record_scatter`, closing with `kb_record_slots_release`), **`slot2_window_row_read`**/**`slot2_window_col_read`** (5x5 window fill halves), **`op_onetime_full_write`** (write-side sibling of handle_query_onetime), **`pos_state_block_write`**/**`pos_state_block_read`** (65E4 serialize/deserialize, tail into pos_step_chain_engine), R30 record/config ops (`r30_config_block_create`/`_link`, `r30_record_link`/`r30_record_write`), **`r6e_heap_layout_build`**/**`r6e_heap_layout_finish`** (6DE8 pointer-table carve from 7894:79E5C), **`r69_pending_session_step`** (pending task + far_cb + clip apply chain with int21 ah=41h delete), `sprite_trail_strip_draw` (77-iter motion streak), `hud_crosshair_ratio_draw`, `object_process_list_walk` (nested 42C0 list walker, mutual with the object family), `config_defaults_table_load` (int21 4B03 module hook + 2A788 callback), `accum_div_ratio` |

### MILESTONE

**Levels 0, 1, 2, 3, 4, 5 AND 6 are all complete.** `named` = **1,283**;
global `naming_queue` = **348** across Levels 7..21 (L7=21 next, then
L19=206 giant SCC); L6 residue = **28 unnamed (0 queue: thunks/orphans),
0 to_name**.

### Gates (all green)

`naming.py check` **1,285** . `verify_rebuild` **faithful (2,237 ==
2,237)** . `verify_idb` **INTACT** . `name_readback` **1,283/1,283
function + 2/2 global**.

---

"""

ROW = ("| 2026-10-19 (session 33) | ~4 h | **Finding 77: Global Level-6 "
       "COMPLETE -- 2 batches (36+24) named all 60 L6 fns, `named` 1,223 -> "
       "**1,283**, L6 queue 60 -> 0.** 13 + 5 truncated bodies full-dumped. "
       "Highlights: r17_event_main_loop, sbi_channel_event_dispatch (1286B "
       "interpreter), slot3 mask rebuild/release, slot2 map window + row/col "
       "readers, object draw-step family + process_list_walk, entity table/"
       "slot builders, 6 HUD panel renderers, record-script trio, "
       "kb record pipeline (slots open/write/far/delta/stream/preset + "
       "release), pos_state_block write/read, r30 config/record ops, "
       "r6e heap layout build/finish, r69 pending session step, "
       "r06_mode_step_dispatch, op_onetime_full_write, hw_config_flags_build, "
       "state_bits pack/unpack, sprite_trail_strip_draw. **MILESTONE: "
       "Levels 0-6 all complete**; queue 408 -> 348 (L7=21, L19=206). "
       "**Gates green:** check 1,285, verify_rebuild faithful, verify_idb "
       "INTACT, read-back 1283/1283+2/2. |")

STATUS_PARA = (
    "**Global Level-6 COMPLETE (finding 77):** 2 batches named all 60 "
    "Level-6 functions (`named` 1,223 → **1,283**), **L6 `naming_queue` 60 → "
    "0**. Headlines: **`r17_event_main_loop`** (the R17 module's main loop "
    "dispatching through the 4-key cs:14A table into the menu/router loops), "
    "**`sbi_channel_event_dispatch`** (1286-byte SBI class×channel event "
    "interpreter), the slot3 mask transaction (`slot3_mask_rebuild` + "
    "`op_slot_mask_release`), the slot2 map-window loaders and the "
    "`slot2_window_row_read`/`slot2_window_col_read` halves, the object "
    "draw-step family and its mutual `object_process_list_walk`, six HUD "
    "panel renderers, the keyboard-record pipeline "
    "(`kb_record_slots_open`/`_write` + far/delta/stream/preset writers), "
    "`pos_state_block_write`/`read`, the R6E heap-layout carve "
    "(`r6e_heap_layout_build`/`_finish`), `r69_pending_session_step`, and "
    "`op_onetime_full_write`. **Levels 0–6 are now all complete**; global "
    "naming_queue = **348** across Levels 7–21 (L7 = 21 next, L19 = 206 "
    "giant SCC). **Gates all green** (check 1,285, verify_rebuild faithful, "
    "verify_idb INTACT, read-back **1,283/1,283 + 2/2**)."
)

OPEN_NEW = [
    "- **GLOBAL LEVEL 6 COMPLETE (finding 77):** 2 batches (36+24) named all",
    "  60 L6 fns, `named` **1223 -> 1283**, **L6 queue 60 -> 0**. Highlights:",
    "  r17_event_main_loop, sbi_channel_event_dispatch, slot3 mask rebuild/",
    "  release, slot2 map window + row/col readers, object draw-step family,",
    "  entity table/slot builders, 6 HUD panels, record-script trio, kb",
    "  record pipeline, pos_state_block write/read, r6e heap layout, r69",
    "  pending session step, r06_mode_step_dispatch, op_onetime_full_write.",
    "  All 4 gates green (check 1285, verify_rebuild faithful, verify_idb",
    "  INTACT, read-back 1283/1283+2/2).",
    "- **Next: Global Level-7** (21 targets) -- global queue 348 across",
    "  L7..L21 (L7=21, L8=13, ..., L19=206 giant SCC, L20=25, L21=2).",
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
if "## 2026-10-19 77" in raw:
    print("findings_log: 77 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 77 before footer (LF preserved)")

# ---- docs/time_log.yaml (CRLF) ----
p = "docs/time_log.yaml"
raw = load(p)
if "session 33" in raw:
    print("time_log: 33 already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 32" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 33 after line %d" % (idx + 1))

# ---- status.md (CRLF) ----
p = "status.md"
raw = load(p)
if "Global Level-6 COMPLETE (finding 77)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f77 para")

# ---- docs/open_items.md (CRLF) ----
p = "docs/open_items.md"
raw = load(p)
if "GLOBAL LEVEL 6 COMPLETE (finding 77)" in raw:
    print("open_items: already updated")
else:
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the f77 status (%d bytes)" % len(block))
